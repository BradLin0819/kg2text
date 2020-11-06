from linked_wiki_utils import readfile, add_triple, normalize_entity_id
from collections import defaultdict
import re
import json


def generate_ordered_triples(doc, min_entities=15):
    # list of triples of each sentence 
    all_triples = []
    doc_tokens = doc['tokens']
    num_entities = 0
    end_of_sent_index = 0

    while num_entities < min_entities:
        # triples in one sentence
        triples = []
        end_of_sent_index = doc_tokens.index('@@END@@', end_of_sent_index + 1)

        for annotation in doc['annotations'][num_entities:]:
            if annotation['span'][1] < end_of_sent_index:
                add_triple(triples, annotation)
                num_entities += 1
        if len(triples) > 0:
            all_triples.append(list(map(lambda x: list(x), triples)))

    assert num_entities >= min_entities
    
    return all_triples
        
if __name__ == '__main__':
    
    generate_planning_tgt('data/linked_wiki_data/dev/dev.jsonl')
