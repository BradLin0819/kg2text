#!/bin/bash

pip install torch==1.6.0+cu101 torchvision==0.7.0+cu101 -f https://download.pytorch.org/whl/torch_stable.html
TORCH=$(python -c "import torch; print(torch.__version__)" | cut -d"+" -f1)
CUDA=$(python -c "import torch; print(torch.version.cuda)" | tr -d ".")
pip install torch-scatter==latest+cu${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html
pip install torch-sparse==latest+cu${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html
pip install torch-cluster==latest+cu${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html
pip install torch-spline-conv==latest+cu${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html
pip install torch-geometric
pip install subword-nmt
pip install torchtext
