import json
import os
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers import util as st_utils
import pickle as pkl
import numpy as np


class Retriever:
    def __init__(self, model_name='stsb-roberta-large', cuda='cuda'):
        self.device = torch.device(cuda if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name).to(self.device)

    def init_corpus_embedding(self, text_list, batch_size=1024):
        return self.model.encode(text_list, batch_size=batch_size, convert_to_tensor=True, device=self.device)  # lower batch_size if limited by GPU memory

    def find_most_similar(self, query_str, corpus_embedding, topk=1):
        query_embedding = self.model.encode(query_str, convert_to_tensor=True, device=self.device)
        # calculate cosine similarity against each candidate sentence in the corpus
        cos_scores = st_utils.pytorch_cos_sim(query_embedding, corpus_embedding)[0].detach().cpu().numpy()
        sorted_idx = np.argsort(-np.array(cos_scores))
        top_k_idx = sorted_idx[:topk]
        top_k_scores = cos_scores[top_k_idx]
        return top_k_idx, top_k_scores