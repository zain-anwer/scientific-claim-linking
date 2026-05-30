from backend.utils.bm25_search import get_top_bm25_results
from pathlib import Path
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH   = str(BASE_DIR / 'cleaned_metadata.csv')
TRAIN_PATH = str(BASE_DIR / 'train.csv')

df     = pd.read_csv(CSV_PATH)
tp_df  = pd.read_csv(TRAIN_PATH)

query_list = tp_df['social_post'].tolist()
id_list = tp_df['id'].tolist()

id_col       = df.columns.get_loc('id')
title_col    = df.columns.get_loc('title')
abstract_col = df.columns.get_loc('abstract')

mnrl_dict = {
    'queries':          [],
    'positives':        [],
    'hard_negatives_1': [],
    'hard_negatives_2': [],
}

skipped = 0

for i, query in enumerate(query_list):
    idx_list = get_top_bm25_results(query,3)

    row_idx  = df.index[df['id'] == id_list[i]].tolist()[0]
    positive = f"Title: {df.iloc[row_idx, title_col]} Abstract: {df.iloc[row_idx, abstract_col]}"

    hard_negatives = []
    for idx in idx_list:
        if df.iloc[idx, id_col] != id_list[i]:
            text = f"Title: {df.iloc[idx, title_col]} Abstract: {df.iloc[idx, abstract_col]}"
            hard_negatives.append(text)
        if len(hard_negatives) == 2:
            break

    if len(hard_negatives) < 2:
        skipped += 1
        continue   # skip pairs where BM25 couldn't find 2 valid negatives

    mnrl_dict['queries'].append(query)
    mnrl_dict['positives'].append(positive)
    mnrl_dict['hard_negatives_1'].append(hard_negatives[0])
    mnrl_dict['hard_negatives_2'].append(hard_negatives[1])

print(f"Pairs written: {len(mnrl_dict['queries'])} | Skipped: {skipped}")

OUTPUT_FILE_PATH = BASE_DIR / 'data/mnrl_finetuning_pairs.json'

# creates any folders needed and doesn't throw an error if they already exist
OUTPUT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(BASE_DIR / 'data/mnrl_finetuning_pairs.json', 'w') as f:
    json.dump(mnrl_dict, f)