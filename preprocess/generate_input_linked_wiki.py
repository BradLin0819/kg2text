import sys
from pathlib import Path
import re
import os
import json
from linked_wiki_utils import *
from planning_tgt import *

folder_source = sys.argv[1]
folder_preprocessed_files = sys.argv[2]

if not os.path.exists(folder_preprocessed_files):
    os.makedirs(folder_preprocessed_files)

datasets = ['train', 'dev', 'test']


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    d = [m.group(0) for m in matches]
    new_d = []
    for token in d:
        token = token.replace('(', '')
        token_split = token.split('_')
        for t in token_split:
            new_d.append(t)
    return new_d


def get_nodes(n):
    n = n.strip()
    n = n.replace('(', '')
    n = n.replace('\"', '')
    n = n.replace(')', '')
    n = n.replace(',', ' ')
    n = n.replace('_', ' ')

    # n = ' '.join(re.split('(\W)', n))
    # n = n.lower()
    n = n.split()

    return n


def get_relation(n):
    n = n.replace('(', '')
    n = n.replace(')', '')
    n = n.strip()
    n = n.split()
    n = "_".join(n)
    return n


def add_nodes(nodes, entity, original_node, all_nodes):
    if entity not in original_node:
        original_node[entity] = {}
        original_node[entity]['idx'] = len(original_node) - 1
        original_node[entity]['words'] = {}
        for n in nodes:
            all_nodes.append(n)
            original_node[entity]['words'][n] = len(all_nodes) - 1
        all_nodes.append('</entity>')


def add_nodes_bpe(nodes, entity, original_node, all_nodes):
    if entity not in original_node:
        original_node[entity] = {}
        original_node[entity]['idx'] = len(original_node) - 1
        all_nodes.append('<entity>')
        original_node[entity]['words'] = {}
        for n in nodes:
            all_nodes.append(n)
            original_node[entity]['words'][n] = len(all_nodes) - 1
        all_nodes.append('</entity>')


def process_triples(doc_triples):

    original_node = {}
    triples = []
    nodes = []
    adj_matrix = []

    for triple in doc_triples:
        n1 = triple[0]
        n2 = triple[2]
        nodes1 = get_nodes(n1)
        nodes2 = get_nodes(n2)
        add_nodes(nodes1, n1, original_node, nodes)
        edge = get_relation(triple[1])

        edge_split = camel_case_split(edge)
        add_nodes(edge_split, edge, original_node, nodes)

        add_nodes(nodes2, n2, original_node, nodes)

        triples.append([edge, original_node[n1]['idx'], original_node[n2]['idx'],
                        original_node[edge]['idx']])


    return nodes, adj_matrix, triples


def get_data(file_):

    datapoints = []
    all_tripes = []
    ordered_tgt = []
    docs = readfile(file_)

    for doc in docs:
        doc_triples, doc_tokens = get_doc_data(doc) # list of triples and tokens in one document
        nodes, adj_matrix, triples = process_triples(doc_triples)

        new_doc = ' '.join(doc_tokens)
        datapoints.append((nodes, adj_matrix, new_doc))
        all_tripes.append(triples)
        ordered_tgt.append(generate_ordered_triples(doc))

    return datapoints, all_tripes, ordered_tgt


def process_bpe(triples, ordered_tgts, file_, file_new, file_graph_new, file_ordered_tgt):
    f = open(file_, 'r').readlines()

    datapoints = []
    ordered_tgts_indices = []
    print('processing', len(triples), 'triples')
    assert len(f) == len(triples)

    for idx, t in enumerate(triples):
        original_node = {}
        nodes = []
        adj_matrix = []
        edge_indices = []

        l = f[idx]
        l = l.strip().split('</entity>')

        nodes_file = []

        for e in l:
            e = e.strip()
            e_split = e.split()
            e_split = list(filter(None, e_split))
            nodes_file.append((e_split, e))

        
        num_triples_of_all_sents = 0

        for sent in ordered_tgts[idx]:
            num_triples_of_all_sents += len(sent)

        assert len(t) == num_triples_of_all_sents

        for triple in t:
            edge, e1, e2, rel = triple # each triple of one document
            n1 = nodes_file[e1][1]
            n2 = nodes_file[e2][1]
            add_nodes_bpe(nodes_file[e1][0], n1, original_node, nodes)

            edges_idx = []
            nodes.append('<relation>')
            
            for e in nodes_file[rel][0]:
                nodes.append(e)
                edges_idx.append(len(nodes) - 1)
                edge_indices.append(edges_idx[-1])

            nodes.append('</relation>')
            add_nodes_bpe(nodes_file[e2][0], n2, original_node, nodes)
            for k in original_node[n1]['words'].keys():
                for edge_idx in edges_idx:
                    l = '(' + str(original_node[n1]['words'][k])
                    l += ',' + str(edge_idx) + ',0,0)'
                    adj_matrix.append(l)

                    l = '(' + str(edge_idx)
                    l += ',' + str(original_node[n1]['words'][k]) + ',2,2)'
                    adj_matrix.append(l)

            for k in original_node[n2]['words'].keys():
                for edge_idx in edges_idx:
                    l = '(' + str(edge_idx)
                    l += ',' + str(original_node[n2]['words'][k]) + ',1,1)'
                    adj_matrix.append(l)

                    l = '(' + str(original_node[n2]['words'][k])
                    l += ',' + str(edge_idx) + ',3,3)'
                    adj_matrix.append(l)

        assert len(edge_indices) == len(t)
        
        # convert entity_id, edge_id into indices
        sents_triples_indices = [] # list of triples of each sentence
        relation_idx = 0

        for sent_triples in ordered_tgts[idx]:
            # sent_triples: all triples in one sentence
            sent_triples_indices = []
            for triple in sent_triples:
                e1, _, e2 = triple
                sent_triples_indices.append([original_node[e1]['words'][e1], edge_indices[relation_idx], original_node[e2]['words'][e2]])
                relation_idx += 1
            sents_triples_indices.append(sent_triples_indices)
        
        ordered_tgts_indices.append(sents_triples_indices)
        datapoints.append((nodes, adj_matrix))
    
    assert len(ordered_tgts_indices) == len(ordered_tgts)
    
    f_new = open(file_new, 'w')
    f_graph_new = open(file_graph_new, 'w')
    f_ordered_tgt = open(file_ordered_tgt, 'w')
    nodes = []
    graphs = []
    for dp in datapoints:
        nodes.append(' '.join(dp[0]))
        graphs.append(' '.join(dp[1]))

    f_new.write('\n'.join(nodes))
    f_new.close()
    f_graph_new.write('\n'.join(graphs))
    f_graph_new.close()

    with open(file_ordered_tgt, 'w') as f_ordered_tgt:
        for idx, ordered_tgt_indices in enumerate(ordered_tgts_indices):
            tgt_dict = defaultdict()
            tgt_dict["tgt"] = defaultdict()
            tgt_dict["tgt"]["ids"] = ordered_tgts[idx]
            tgt_dict["tgt"]["indices"] = ordered_tgt_indices
            json.dump(tgt_dict, f_ordered_tgt)
            f_ordered_tgt.write('\n')

    print('done')


triples = {}
# train_cat = set()
dataset_points = []
ordered_tgts = {}

for d in datasets:
    triples[d] = []
    datapoints = []
    ordered_tgts[d] = []

    files = Path(folder_source + d).rglob('*.jsonl')
    for idx, filename in enumerate(files):
        filename = str(filename)
        
        datapoint, tripes, orderedtgt = get_data(filename)
        datapoints.extend(datapoint)
        triples[d].extend(tripes)
        ordered_tgts[d].extend(orderedtgt)
 
    print(d, len(datapoints))
    print(d, ' -> triples:', len(triples[d]))
    assert len(datapoints) == len(triples[d])
    dataset_points.append(datapoints)


path = folder_preprocessed_files
for idx, datapoints in enumerate(dataset_points):

    part = datasets[idx]
    nodes = []
    graphs = []
    surfaces = []

    for datapoint in datapoints:
        nodes.append(' '.join(datapoint[0]))
        graphs.append(' '.join(datapoint[1]))
       
        surfaces.append(datapoint[2])

    with open(path + '/' + part + '-src.txt', 'w', encoding='utf8') as f:
        f.write('\n'.join(nodes)+'\n')
    with open(path + '/' + part + '-surfaces.txt', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces))

# num_operations = 2000
# os.system('cat ' + path + '/train-src.txt ' + path + '/train-surfaces.txt > ' +
#           path + '/training_source.txt')
# print('creating bpe codes...')
# os.system('subword-nmt learn-bpe -s ' + str(num_operations) + ' < ' +
#                 path + '/training_source.txt > ' + path + '/codes-bpe.txt')
# print('done')
# print('converting files to bpe...')

# for d in datasets:
#     file_pre = path + '/' + d + '-src.txt'
#     file_ = path + '/' + d + '-src-bpe.txt'
#     os.system('subword-nmt apply-bpe -c ' + path + '/codes-bpe.txt < ' + file_pre + ' > ' + file_)

#     file_pre = path + '/' + d + '-surfaces.txt'
#     file_ = path + '/' + d + '-surfaces-bpe.txt'
#     os.system('subword-nmt apply-bpe -c ' + path + '/codes-bpe.txt < ' + file_pre + ' > ' + file_)
# print('done')

for d in datasets:
    print('dataset:', d)
    file_ = path + '/' + d + '-src.txt'
    file_new = path + '/' + d + '-nodes.txt'
    file_graph_new = path + '/' + d + '-graph.txt'
    file_ordered_tgt = path + '/' + d + '-ordered-tgt.jsonl'
    process_bpe(triples[d], ordered_tgts[d], file_, file_new, file_graph_new, file_ordered_tgt)

