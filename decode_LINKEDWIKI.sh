#!/bin/bash

if [ "$#" -lt 5 ]; then
  echo "./decode_LINKEDWIKI.sh <gpuid> <model> <nodes-file> <graph-file> <output>"
  exit 2
fi

GPUID=$1
MODEL=$2
NODES_FILE=$3
GRAPH_FILE=$4
OUTPUT=$5

export CUDA_VISIBLE_DEVICES=${GPUID}
export OMP_NUM_THREADS=10

python -u graph2text/translate.py -model ${MODEL} \
-src ${NODES_FILE} \
-graph ${GRAPH_FILE} \
-output ${OUTPUT} \
-tgt graph2text/data/linkedwiki/test-surfaces.txt \
-beam_size 3 \
-share_vocab \
-length_penalty wu \
-alpha 3 \
-verbose \
-batch_size 60 \
-gpu ${GPUID} \
-min_length 150 \
--report_rouge \
--report_bleu \
-log_file test_report.log

cat ${OUTPUT} | sed -r 's/(@@ )|(@@ ?$)//g' > "${OUTPUT}_proc.txt"
mv "${OUTPUT}_proc.txt" ${OUTPUT}
