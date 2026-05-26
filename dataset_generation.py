"""
Scientific Claim Linking Dataset Builder
=========================================
Generates a domain-balanced, stratum-stratified corpus of ~20,000 scientific
papers from OpenAlex, tuned for a multi-stage retrieval pipeline using
scispaCy + UMLS, sciBERT, and SPECTER2.

Output fields: id, title, authors, abstract, date, doi, url

Design principles:
  - Domain balance across 8 scientific areas
  - Citation x recency stratification within each domain
  - Hard quality gates (abstract length, DOI, peer-review signal)
  - Minimum citation = 1 (quality signal, not popularity filter)
  - Year range 1990-2025 to cover both foundational and recent evidence
  - Cursor-based pagination (fast, no offset degradation)
  - Deduplication by DOI across all domains
  - JSONL output for streaming into vector stores
"""

import requests
import json
import time
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# trying to fix the ugly log issue

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EMAIL = "zain.anwer192005@gmail.com"          # OpenAlex polite pool — faster rate limits
OUTPUT_FILE = Path("papers_dataset.jsonl")
LOG_FILE    = Path("build_dataset.log")
TOTAL_TARGET = 20_000

# OpenAlex concept IDs for scientific domains relevant to claim linking.
# These map to high-recall parent concepts; OpenAlex returns child-concept
# papers automatically through its hierarchy traversal.
#
# Chosen for UMLS/MeSH coverage alignment:
#   - Biomedical, nutrition, neuroscience → excellent UMLS coverage
#   - Environmental/chemistry → ChEBI + NCI Thesaurus via UMLS
#   - Physics → SPECTER2 fallback (minimal UMLS coverage, handled by dense retrieval)
#   - Epidemiology → core claim-linking domain
#   - Microbiology/immunology → vaccine + pathogen claims

# Weighing domains based on how often they pop up in social media claims

DOMAINS = {

    "biomedical_health": {
        "concept_id": "C71924100",
        "target": 9000,
        "description": (
            "Core medical claims — disease, treatment, drugs, symptoms"
        ),
    },

    "nutrition_food_science": {
        "concept_id": "C203014093",
        "target": 5000,
        "description": (
            "Diet, supplements, fasting, seed oils, processed food, vitamins"
        ),
    },

    "epidemiology_public_health": {
        "concept_id": "C2779747511",
        "target": 4000,
        "description": (
            "Risk factors, population health, outbreaks, prevalence"
        ),
    },

    "neuroscience_psychology": {
        "concept_id": "C15744967",
        "target": 3000,
        "description": (
            "Mental health, cognition, ADHD, depression, behavioural claims"
        ),
    },

    "immunology_vaccines": {
        "concept_id": "C2986040975",
        "target": 3000,
        "description": (
            "Vaccines, immunity, autoimmune claims, pathogens"
        ),
    },

    "environmental_climate": {
        "concept_id": "C2776140422",
        "target": 1000,
        "description": (
            "Pollution, radiation, climate-health, air quality"
        ),
    },

    "biology_genetics": {
        "concept_id": "C86803240",
        "target": 1500,
        "description": (
            "CRISPR, microbiome, GMO, genetics"
        ),
    },

    "chemistry_toxicology": {
        "concept_id": "C185592680",
        "target": 1000,
        "description": (
            "Heavy metals, fluoride, toxins, endocrine disruptors, EMF"
        ),
    },
}

# Citation × recency strata within each domain.
# Rationale:
#   - high_cited_recent  : strong recent evidence, high retrieval precision
#   - high_cited_older   : foundational/landmark papers, consensus anchors
#   - mid_cited_recent   : emerging evidence, good for contested claims
#   - low_cited_recent   : cutting-edge, may not yet be widely cited
#   - min 1 citation everywhere: eliminates retractions, stub entries, ghost papers
#
# Proportions per domain (must sum to 1.0):
STRATA = [
    {
        "name": "high_cited_recent",
        "min_cited_by": 50,
        "year_from": 2018,
        "year_to": 2025,
        "proportion": 0.25,
        "sort": "cited_by_count:desc",
    },
    {
        "name": "high_cited_older",
        "min_cited_by": 100,
        "year_from": 1990,
        "year_to": 2017,
        "proportion": 0.25,
        "sort": "cited_by_count:desc",
    },
    {
        "name": "mid_cited_recent",
        "min_cited_by": 10,
        "year_from": 2018,
        "year_to": 2025,
        "proportion": 0.30,
        "sort": "publication_date:desc",
    },
    {
        "name": "low_cited_recent",
        "min_cited_by": 1,
        "year_from": 2021,
        "year_to": 2025,
        "proportion": 0.20,
        "sort": "publication_date:desc",
    },
]

# Quality gates applied to every paper before inclusion
MIN_ABSTRACT_CHARS   = 150     # Filters stub/truncated abstracts
MIN_TITLE_CHARS      = 10      # Filters noise entries
REQUIRE_DOI          = True    # DOI required for deduplication + URI
REQUIRE_PEER_REVIEW  = True    # Must be journal article (not preprint/dataset)

# Request settings
PER_PAGE     = 200             # Max OpenAlex allows
REQUEST_DELAY = 0.12           # Seconds between requests (polite pool: ~8 req/s)
MAX_RETRIES  = 3
RETRY_DELAY  = 5.0

FIELDS = ",".join([
    "id",
    "doi",
    "title",
    "abstract_inverted_index",
    "publication_date",
    "publication_year",
    "authorships",
    "primary_location",
    "type",
    "cited_by_count",
    "concepts",
])

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Abstract reconstruction
# ---------------------------------------------------------------------------

def reconstruct_abstract(inverted_index: dict) -> str:
    """
    OpenAlex stores abstracts as an inverted index: {word: [position, ...]}
    Reconstruct to a plain string. Returns "" if index is missing or malformed.
    """
    if not inverted_index:
        return ""
    try:
        max_pos = max(pos for positions in inverted_index.values() for pos in positions)
        words = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(w for w in words if w)
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------

def passes_quality_gate(paper: dict, abstract: str) -> bool:
    """Return True if paper meets all quality criteria."""
    if REQUIRE_DOI and not paper.get("doi"):
        return False

    if len(abstract) < MIN_ABSTRACT_CHARS:
        return False

    title = paper.get("title") or ""
    if len(title) < MIN_TITLE_CHARS:
        return False

    if REQUIRE_PEER_REVIEW:
        paper_type = paper.get("type", "")
        # OpenAlex types: article, review, book-chapter, dataset, preprint, etc.
        if paper_type not in ("article", "review"):
            return False

    year = paper.get("publication_year")
    if not year or not (1990 <= year <= 2025):
        return False

    return True

# ---------------------------------------------------------------------------
# Paper normalization
# ---------------------------------------------------------------------------

def normalize_paper(raw: dict, domain_name: str, stratum_name: str) -> dict:
    """Extract and normalize fields from raw OpenAlex work record."""
    abstract = reconstruct_abstract(raw.get("abstract_inverted_index") or {})

    # Authors: extract display names preserving order
    authors = [
        a["author"]["display_name"]
        for a in raw.get("authorships", [])
        if a.get("author") and a["author"].get("display_name")
    ]

    # DOI handling: OpenAlex returns full URL; strip to bare DOI
    doi_url = raw.get("doi") or ""
    doi_bare = doi_url.replace("https://doi.org/", "").strip()

    # Publication URL: prefer publisher landing page, fall back to DOI URL
    loc = raw.get("primary_location") or {}
    landing_page = loc.get("landing_page_url") or doi_url or ""

    # Venue
    source = loc.get("source") or {}
    venue = source.get("display_name") or ""

    # Top concepts (useful for downstream domain tagging)
    concepts = [
        c["display_name"]
        for c in (raw.get("concepts") or [])
        if c.get("score", 0) >= 0.4       # Only confident concept assignments
    ][:5]

    return {
        "id":           raw.get("id", "").replace("https://openalex.org/", ""),
        "title":        (raw.get("title") or "").strip(),
        "authors":      authors,
        "abstract":     abstract,
        "date":         raw.get("publication_date") or str(raw.get("publication_year", "")),
        "year":         raw.get("publication_year"),
        "doi":          doi_bare,
        "url":          landing_page,
        "venue":        venue,
        "cited_by":     raw.get("cited_by_count", 0),
        "concepts":     concepts,
        "domain":       domain_name,
        "stratum":      stratum_name,
    }

# ---------------------------------------------------------------------------
# OpenAlex fetcher
# ---------------------------------------------------------------------------

def build_filter(concept_id: str, stratum: dict) -> str:
    """Construct OpenAlex filter string for a domain × stratum combination."""
    parts = [
        f"concepts.id:{concept_id}",
        f"cited_by_count:>{stratum['min_cited_by'] - 1}",  # ≥ min_cited_by
        f"publication_year:{stratum['year_from']}-{stratum['year_to']}",
        "has_doi:true",
        "has_abstract:true",
        "type:article|review",                              # peer-reviewed only
    ]
    return ",".join(parts)


def fetch_stratum(concept_id: str, domain_name: str, stratum: dict, target: int, seen_dois: set) -> list[dict]:
    """
    Fetch up to `target` papers for one domain × stratum combination.
    Uses cursor-based pagination for performance.
    Returns list of normalized paper dicts.
    """
    papers = []
    cursor = "*"
    filter_str = build_filter(concept_id, stratum)

    log.info(
        f"  [{domain_name}/{stratum['name']}] "
        f"target={target} | years={stratum['year_from']}–{stratum['year_to']} | "
        f"min_cited >= {stratum['min_cited_by']}"
    )

    while len(papers) < target:
        url = (
            f"https://api.openalex.org/works"
            f"?filter={filter_str}"
            f"&select={FIELDS}"
            f"&sort={stratum['sort']}"
            f"&per_page={PER_PAGE}"
            f"&cursor={cursor}"
            f"&mailto={EMAIL}"
        )

        # Retry loop
        response = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    break
                elif response.status_code == 429:
                    wait = RETRY_DELAY * attempt
                    log.warning(f"    Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    log.warning(f"    HTTP {response.status_code} on attempt {attempt}")
                    time.sleep(RETRY_DELAY)
            except requests.RequestException as e:
                log.warning(f"    Request error on attempt {attempt}: {e}")
                time.sleep(RETRY_DELAY)

        if not response or response.status_code != 200:
            log.error(f"    Failed after {MAX_RETRIES} retries. Skipping stratum.")
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        for raw in results:
            if len(papers) >= target:
                break

            abstract = reconstruct_abstract(raw.get("abstract_inverted_index") or {})

            if not passes_quality_gate(raw, abstract):
                continue

            doi_url = raw.get("doi") or ""
            doi_bare = doi_url.replace("https://doi.org/", "").strip()

            # Cross-domain deduplication
            if doi_bare in seen_dois:
                continue

            seen_dois.add(doi_bare)
            papers.append(normalize_paper(raw, domain_name, stratum["name"]))

        # Cursor advance
        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor:
            break

        cursor = next_cursor
        time.sleep(REQUEST_DELAY)

    log.info(f"    -> collected {len(papers)} papers")
    return papers


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build_dataset(output_file: Path = OUTPUT_FILE, total_target: int = TOTAL_TARGET):
    log.info("=" * 60)
    log.info("Scientific Claim Linking Dataset Builder")
    log.info(f"Target: {total_target:,} papers | Output: {output_file}")
    log.info("=" * 60)

    all_papers: list[dict] = []
    seen_dois: set[str] = set()
    domain_stats: dict[str, dict] = defaultdict(lambda: defaultdict(int))

    for domain_name, domain_cfg in DOMAINS.items():
        concept_id   = domain_cfg["concept_id"]
        domain_target = domain_cfg["target"]

        log.info(f"\nDomain: {domain_name.upper()} (target={domain_target})")
        log.info(f"  {domain_cfg['description']}")

        domain_papers: list[dict] = []

        for stratum in STRATA:
            stratum_target = max(1, round(domain_target * stratum["proportion"]))
            fetched = fetch_stratum(
                concept_id,
                domain_name,
                stratum,
                stratum_target,
                seen_dois,
            )
            domain_papers.extend(fetched)
            domain_stats[domain_name][stratum["name"]] = len(fetched)

        all_papers.extend(domain_papers)
        log.info(f"  Domain total: {len(domain_papers)} papers (running total: {len(all_papers)})")

        if len(all_papers) >= total_target:
            log.info("Global target reached. Stopping early.")
            break

    # ---------------------------------------------------------------------------
    # Write output
    # ---------------------------------------------------------------------------
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for paper in all_papers:
            f.write(json.dumps(paper, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------------------
    # Stats report
    # ---------------------------------------------------------------------------
    log.info("\n" + "=" * 60)
    log.info(f"DONE. Total papers written: {len(all_papers):,}")
    log.info(f"Output: {output_file}")
    log.info("=" * 60)

    log.info("\nDomain breakdown:")
    for domain_name, strata_counts in domain_stats.items():
        total = sum(strata_counts.values())
        log.info(f"  {domain_name:<35} {total:>5}")
        for stratum_name, count in strata_counts.items():
            log.info(f"      {stratum_name:<30} {count:>5}")

    # Year distribution
    year_buckets = defaultdict(int)
    for p in all_papers:
        y = p.get("year") or 0
        if y >= 2021:   bucket = "2021-2025"
        elif y >= 2018: bucket = "2018-2020"
        elif y >= 2010: bucket = "2010-2017"
        elif y >= 2000: bucket = "2000-2009"
        else:           bucket = "1990-1999"
        year_buckets[bucket] += 1

    log.info("\nYear distribution:")
    for bucket in ["2021-2025", "2018-2020", "2010-2017", "2000-2009", "1990-1999"]:
        pct = year_buckets[bucket] / max(len(all_papers), 1) * 100
        log.info(f"  {bucket}   {year_buckets[bucket]:>5}  ({pct:.1f}%)")

    # Citation distribution
    cite_buckets = {"≥100": 0, "10-99": 0, "1-9": 0}
    for p in all_papers:
        c = p.get("cited_by", 0)
        if c >= 100:  cite_buckets["≥100"] += 1
        elif c >= 10: cite_buckets["10-99"] += 1
        else:         cite_buckets["1-9"] += 1

    log.info("\nCitation distribution:")
    for label, count in cite_buckets.items():
        pct = count / max(len(all_papers), 1) * 100
        log.info(f"  {label:<10} {count:>5}  ({pct:.1f}%)")

    return all_papers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build scientific claim-linking paper dataset.")
    parser.add_argument("--output",  type=Path, default=OUTPUT_FILE, help="Output JSONL file path")
    parser.add_argument("--target",  type=int,  default=TOTAL_TARGET, help="Total paper target")
    parser.add_argument("--email",   type=str,  default=EMAIL,        help="Email for OpenAlex polite pool")
    args = parser.parse_args()

    EMAIL = args.email
    build_dataset(output_file=args.output, total_target=args.target)