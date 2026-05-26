# tokenization -> medical entity selection (NER) -> synonym matchup (linking)

import spacy 
from pathlib import Path
from scispacy.linking import EntityLinker

PIPELINE_PATH = Path(__file__).resolve().parent.parent / 'pipelines/scispacy_linker_pipeline'

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
        "linker_name": "umls",
        "resolve_abbreviations" : True,
        "threshold": 0.85,
        "max_entities_per_mention": 1
    }
)

linker = nlp.get_pipe("scispacy_linker")

def query_expansion(query : str) -> str:
    
    doc = nlp(query)
    
    expanded_terms = set()

    print('Entities Recognized: ')

    for i,entity in enumerate(doc.ents):
        print(i+1,'th entity: ',entity.text)

        # (concept_id, score) pairs
        # concept_id used to look up aliases
        for concept in entity._.kb_ents[:1]:
            concept_id = concept[0]
            score = concept[1]
        
            concept = linker.kb.cui_to_entity[concept_id]
        
            # only take top ten aliases
            for alias in concept.aliases[:10]:
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
