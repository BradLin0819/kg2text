import os
import json
import re
from preprocess.linked_wiki_utils import *
file_path = 'data/linked_wiki_data/train/train.jsonl'

if __name__ == '__main__':
    data = readfile(file_path)
    doc_tokens_lens = []
    triples_lens = []

    for doc in data:
        triples, tokens = get_doc_data(doc)
        doc_tokens_lens.append(len(tokens))
        triples_lens.append(len(triples))
    
    print('==== STAT INFO ====')
    print(f'avg_num_of_triples: {sum(triples_lens) / len(triples_lens)}')
    print(f'max_num_of_triples: {max(triples_lens)}')
    print(f'avg_num_of_tokens: {sum(doc_tokens_lens) / len(doc_tokens_lens)}')
    print(f'max_num_of_tokens: {max(doc_tokens_lens)}')
