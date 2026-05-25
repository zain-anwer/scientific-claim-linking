# some onnx optimization would help apparently

"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import time

query =  "heart attack is caused by insomnia and painkillers!! Damnn"

MODELS = [
    {
        "name": "prithivida/informal_to_formal_styletransfer",
        # style-transfer model expects this prefix, ignores instruction prompts
        "prompt_fn": lambda q: f"transfer Casual to Formal: {q}",
    },
    {
        "name": "google/flan-t5-small",
        # instruction-tuned, can handle a structured prompt
        "prompt_fn": lambda q: (
            f"Rewrite as a formal biomedical search query:\n{q}"
        ),
    },
    {
        "name": "humarin/chatgpt_paraphraser_on_T5_base",
        # expects this exact prefix
        "prompt_fn": lambda q: f"paraphrase: {q}",
    },
]

rewritten_queries = []

for MODEL in MODELS:
    tokenizer = AutoTokenizer.from_pretrained(MODEL['name'])
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL['name'])
    model.eval()

    # --- saving model and tokenizer --- #
    # tokenizer.save_pretrained(FILE_PATH)
    # model.save_pretrained(FILE_PATH)

    prompt = MODEL['prompt_fn'](query)

    start_time = time.perf_counter()

    # LLMS don't understand words so tokenization --> token ids are fed
    inputs = tokenizer(
        prompt,
        return_tensors = 'pt',
        truncation = True,
        max_length = 128,
    )

    # warm-up pass so first-run JIT overhead doesn't skew timing
    with torch.no_grad():
        model.generate(**inputs, max_new_tokens=32)

    with torch.no_grad():
        output = model.generate(
            **inputs,              # resolves the dictionary,
            num_beams = 4,
            max_new_tokens = 32,
            early_stopping = True
        )

    rewritten = tokenizer.decode(
        output[0],
        skip_special_tokens = True
    )

    end_time = time.perf_counter()

    rewritten_queries.append((end_time - start_time,rewritten))

print('Original Query: ',query)

for duration, rewritten in rewritten_queries:
    print('Rewritten Query: ',rewritten)
    print('Inference time: ',duration)

"""