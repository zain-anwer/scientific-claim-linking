import spacy
from pathlib import Path
from scispacy.linking import EntityLinker

nlp = spacy.load('en_core_sci_sm')
nlp.add_pipe(
    "scispacy_linker",
    config={
        "linker_name": "umls",
        "resolve_abbreviations": True,
        "threshold": 0.85,
        "max_entities_per_mention": 1
    }
)

BASE_DIR = Path(__file__).resolve().parent
nlp.to_disk(BASE_DIR.parent / "pipelines/scispacy_linker_pipeline")
print('Pipeline Saved')