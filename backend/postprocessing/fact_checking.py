from transformers import pipeline
from pathlib import Path

MODEL = 'ze19n/biomedbert-nli'

# WindowsPath --> string
MODEL = str(MODEL)

fact_checker = pipeline(
    task='text-classification',
    model=MODEL,
    tokenizer=MODEL,
    truncation=True,
    max_length=512
)

interpretation_map = {
    "entailment": "support",
    "contradiction": "refute",
    "neutral": "neutral"
}

def claim_verification(post,title,abstract):

    title_abstract = f"Title: {title}. Abstract: {abstract}"
    prediction = fact_checker({'text':title_abstract,'text_pair':post})
    label = interpretation_map[prediction['label']]
    score = prediction['score'] * 100
    return label,score
    
