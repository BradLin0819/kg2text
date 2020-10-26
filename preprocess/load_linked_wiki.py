import re
import os
import json

def readfile(path):
    data = []
    
    assert os.path.exists(path)

    with open(path) as f:
        for i in f.readlines():
            data.append(json.loads(i))
    return data


def get_doc_data(doc, min_entities=15):
    triples = []
    doc_tokens = doc['tokens']
    last_entity_span_end = -1

    for ent_idx, annotation in enumerate(doc['annotations'][:min_entities]):
        for rel_idx, rel in enumerate(annotation['relation']):
            triples.append((annotation['id'], rel, annotation['parent_id'][rel_idx]))
        
        if ent_idx == (min_entities - 1):
            last_entity_span_end = annotation['span'][1]
    
    assert last_entity_span_end != -1

    while doc_tokens[last_entity_span_end-1] != '.':
        last_entity_span_end += 1

    # Add entities before '.'
    for ent_idx, annotation in enumerate(doc['annotations'][min_entities:]):
        if annotation['span'][1] <= last_entity_span_end:
            for rel_idx, rel in enumerate(annotation['relation']):
                triples.append((annotation['id'], rel, annotation['parent_id'][rel_idx]))
        else:
            break
    sub_tokens = [token.lower() for token in doc_tokens[:last_entity_span_end] if re.match(r'@@\w+@@', token) is None]
    return triples, sub_tokens

if __name__ == '__main__':
    file_path = '/home/thlin20/kg2text/data/linked_wiki_data/dev/dev.jsonl'
    print(file_path)
    data = readfile(file_path)
    triples, tokens = get_doc_data(data[20])

    print(len(triples))
    print(triples)
    print('=====')
    print(len(tokens))
    print(tokens)