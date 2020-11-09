import re
import os
import json


def readfile(path):

    assert os.path.exists(path)

    with open(path) as f:
        for i in f.readlines():
            data = json.loads(i)
            yield data


def normalize_entity_id(raw_entity_id):
    normalized_entity_id = None

    if raw_entity_id[0] == 'T':
        normalized_entity_id = "@@DATE@@"
    elif raw_entity_id[0] == 'V':
        normalized_entity_id = "@@QUANTITY@@"
    elif raw_entity_id[0] in ['P', 'Q']:
        normalized_entity_id = raw_entity_id
    return normalized_entity_id


# relation_mapping_table = next(readfile('../rel2name.json'))
# entity_mapping_table = next(readfile('../ent2name.json'))

def add_triple(triples, annotation):
    for rel_idx, rel in enumerate(annotation['relation']):
        normalized_src_entity = normalize_entity_id(annotation['id'])
        normalized_parent_entity = normalize_entity_id(annotation['parent_id'][rel_idx])
        triples.append((normalized_src_entity, rel, normalized_parent_entity))


def get_doc_data(doc, min_entities=15):
    triples = []
    doc_tokens = doc['tokens']
    num_entities = 0
    end_of_sent_index = 0

    while num_entities < min_entities:
        end_of_sent_index = doc_tokens.index('@@END@@', end_of_sent_index + 1)

        for annotation in doc['annotations'][num_entities:]:
            if annotation['span'][1] < end_of_sent_index:
                add_triple(triples, annotation)
                num_entities += 1

    assert num_entities >= min_entities
    sub_tokens = [token.lower() for token in doc_tokens[:end_of_sent_index+1] if re.match(r'@@\w+@@', token) is None]
    return triples, sub_tokens


if __name__ == '__main__':
    file_path = '/home/thlin/kg2text/data/linked_wiki_data/dev/dev.jsonl'
    print(file_path)
    data = readfile(file_path)
    triples, tokens = get_doc_data(next(data))

    print(len(triples))
    print(triples)
    print('=====')
    print(len(tokens))
    print(tokens)