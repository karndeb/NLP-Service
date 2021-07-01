from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import requests, zipfile, io
import os


def set_seed(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(42)

model_qe = T5ForConditionalGeneration.from_pretrained('ramsrigouthamg/t5_paraphraser')
tokenizer = T5Tokenizer.from_pretrained('ramsrigouthamg/t5_paraphraser')

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device ", device)
model_qe = model_qe.to(device)


model_nqr = SentenceTransformer('roberta-base-nli-stsb-mean-tokens')


def get_scores(input_query, input_corpus, topk=5):
    emb_corpus = np.array(model_nqr.encode(input_corpus))
    emb_query = np.array(model_nqr.encode([input_query]))
    results = cosine_similarity(emb_query, emb_corpus)[0]
    topk = results.argsort()[-topk:][::-1]
    scores = results[topk]
    sentences = [input_corpus[idx] for idx in topk]
    return [str(s) for s in scores], sentences


def generate_paraphrases(input_query, topk = 5):
    # text = "paraphrase: " + input_query + " </s>"
    max_len = 256
    encoding = tokenizer.encode_plus(input_query, pad_to_max_length=True, return_tensors="pt")
    input_ids, attention_masks = encoding["input_ids"].to(device), encoding["attention_mask"].to(device)
    beam_outputs = model_qe.generate(input_ids=input_ids, attention_mask=attention_masks, do_sample=True,
                                     max_length=max_len, top_k=120, top_p=0.98, early_stopping=True,
                                     num_return_sequences=10)
    final_outputs = []
    for beam_output in beam_outputs:
        sent = tokenizer.decode(beam_output, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        if sent.lower() != input_query.lower() and sent not in final_outputs:
            final_outputs.append(sent)
    return final_outputs[:topk]

