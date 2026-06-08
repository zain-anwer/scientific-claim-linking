# ------------------ INITIAL CONFIG ----------------------- #

# mesh performs better in evaluation scripts hence mesh it is
# CHOICE = input("Enter linker type (umls or mesh) : ")

# --------------------------------------------------------- # 

# tokenization -> medical entity selection (NER) -> synonym matchup (linking)

import spacy 
from pathlib import Path
from scispacy.linking import EntityLinker
from preprocessing.query_normalization import normalize_query_bm25_search

# PIPELINE_PATH = Path(__file__).resolve().parent.parent / 'pipelines/scispacy_linker_pipeline'

"""
if not PIPELINE_PATH.exists():
    print('Pipeline not found!! Aborting Program...')
    raise SystemExit
"""
    
# loading the pipeline with the NER model and linker
# nlp = spacy.load(PIPELINE_PATH)

nlp = spacy.load("en_core_sci_sm")
nlp.add_pipe(
    "scispacy_linker",
    config = {
        "linker_name": 'mesh',
        "resolve_abbreviations" : True,
        "threshold": 0.85,
        "max_entities_per_mention": 1
    }
)

linker = nlp.get_pipe("scispacy_linker")

def query_expansion(query : str) -> str:
    
    # pre expansion normalization that doesn't change semantic meaning
    # query = remove_elongation(query)
    # query = remove_emojis(query)
    # query = clean_unicode_and_layout(query)
 
    query = " ".join(normalize_query_bm25_search(query))
 
    print('Modified query prior expansion: ',query)

    doc = nlp(query)
    
    expanded_terms = set()

    print('Entities Recognized: ')

    for i,entity in enumerate(doc.ents):

        # conversational denoising through Part Of Speech (POS) tagging to prevent useless entity recognition 

        # check POS tag of the root word of the entity
        # if the core word is an interjection (e.g., "dude") or pronoun, drop it
        if entity.root.pos_ in {"INTJ", "PRON", "VERB"}:
            continue
            
        # drop entities that are purely numbers or generic symbols
        if entity.text.isdigit() or entity.root.pos_ == "SYM":
            continue
            
        # check if it's an abstract noun acting as a filler
        # "attention" in "pay attention to" usually lacks specific modifiers
        if entity.text.lower() in ["attention", "theory", "level", "study"]:
            # If it doesn't have an adjective or noun modifier attached, skip it
            ancestors_pos = [token.pos_ for token in entity.root.ancestors]
            if "VERB" in ancestors_pos and not any(t.pos_ in {"ADJ", "NOUN"} for t in entity):
                continue

        print(i+1,'th entity: ',entity.text)

        # (concept_id, score) pairs
        # concept_id used to look up aliases
        for concept in entity._.kb_ents[:1]:
            concept_id = concept[0]
            score = concept[1]
        
            concept = linker.kb.cui_to_entity[concept_id]
        
            # TRYING TO DECREASE NOISE THROUGH CANONICAL TERMS AND LESSER ALIASES

            # add the highly accurate canonical anchor term
            expanded_terms.add(concept.canonical_name)

            # grabbing only the top 2 highly correlated aliases instead of 10
            for alias in concept.aliases[:2]:
                expanded_terms.add(alias)

    query = query + " " + " ".join(set(expanded_terms))                

    return query

# --------------------- code testing ----------------------- #

def main():
    query = input('Enter Query: ')
    expanded_query = query_expansion(query)
    print(expanded_query)

if __name__ == "__main__":
   main() 

# ---------------------------------------------------------- #
