import json
import requests
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
from tqdm import tqdm


def readfile(path):
    data = []

    with open(path, 'r') as f:
        for line in f.readlines():
            data.append(json.loads(line.strip()))
    return data


def build_ents_rels_set(path):
    docs = readfile(path)
    rels_counter = Counter()
    ents_set = set()

    for doc in docs:
        for annotation in doc['annotations']:
            for rel in annotation['relation']:
                rels_counter[rel] += 1

            ents_set.add(annotation['id'])
            
            for parent_id in annotation['parent_id']:
                ents_set.add(parent_id)

    return {
        'rels_counter': rels_counter,
        'ents_set': ents_set
    }


def get_rels_mapping(rels_counter, out_file_path='rel2name.json'):
    rel_id2name = defaultdict() # {'P131': ..., }
    rel_id_group2name = defaultdict() # {'P131:P150': ..., }

    for rels_id_group in tqdm(list(rels_counter.keys())):
        rel_ids = rels_id_group.split(':')
        rel_names = []

        for rel_id in rel_ids:
            if rel_id == 'R':
                rel_names += ['Reverse']
            elif rel_id in rel_id2name:
                rel_names += [rel_id2name[rel_id]]
            else:
                web_page = requests.get(f'https://www.wikidata.org/wiki/Property:{rel_id}')
                soup = BeautifulSoup(web_page.text, 'html.parser')
                rel_id_name = soup.title.text.split('-')[0].strip()
                rel_id2name[rel_id] = rel_id_name
                rel_names += [rel_id_name]

        rel_id_group2name[rels_id_group] = ':'.join(rel_names)

    with open(out_file_path, 'w') as f:
        json.dump(rel_id_group2name, f)


def get_ents_mapping(ents_set, out_file_path='ent2name.json'):
    ent_id2name = defaultdict() # {'Q123': ..., }

    assert len(ents_set) != 0

    for ent_id in tqdm(ents_set):
        if ent_id[0] in ['P', 'Q']:
            if ent_id not in ent_id2name:
                web_page = requests.get(f'https://www.wikidata.org/wiki/{ent_id}')
                soup = BeautifulSoup(web_page.text, 'html.parser')
                ent_id_name = soup.title.text.split('-')[0].strip()
                ent_id2name[ent_id] = ent_id_name

    with open(out_file_path, 'w') as f:
        json.dump(ent_id2name, f)     

sets = build_ents_rels_set('./linkedwiki.jsonl')
ents_set = sets['ents_set']
rel_counter = sets['rels_counter']

get_ents_mapping(ents_set)
get_rels_mapping(rel_counter)