.. _`modeling_references`:

ML primary literature & references
==================================

What did we use for this project?

GDELT
-----
GDELT Datasets:

TV:
https://blog.gdeltproject.org/a-new-dataset-for-exploring-climate-change-narratives-on-television-news-2009-2020/

Online News:
https://blog.gdeltproject.org/a-new-contextual-dataset-for-exploring-climate-change-narratives-6-3m-english-news-urls-with-contextual-snippets-2015-2020/


Argument Unit Recognition and Classification
--------------------------------------------
paper: https://aaai.org/Papers/AAAI/2020GB/AAAI-TrautmannD.7498.pdf

dataset: https://github.com/trtm/AURC

bibtex reference::

    @inproceedings{trautmann2020fine,
      title = {Fine-Grained Argument Unit Recognition and Classification},
      author = {Dietrich Trautmann and
                Johannes Daxenberger and
                Christian Stab and
                Hinrich Schutze and
                Iryna Gurevych},
      booktitle = {The Thirty-Fourth {AAAI} Conference on Artificial Intelligence, {AAAI} 2020},
      publisher = {{AAAI} Press},
      month = {2},
      year = {2020},
      url = {https://aaai.org/Papers/AAAI/2020GB/AAAI-TrautmannD.7498.pdf},
    }


BERT
----
Below we list some references to the MLP models and utilities used in the original model

NLP transformers
^^^^^^^^^^^^^^^^
https://github.com/huggingface/transformers  
Tensorflow & PyTorch set of utilities for transforming text
into something useable by the models

BERT primary reference
^^^^^^^^^^^^^^^^^^^^^^
[BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805)

[documentation](https://huggingface.co/transformers/model_doc/bert.html)

Semantic Role Labeling (SRL)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Identifying conspiracy theories vs real theories
https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233879


Sentence-BERT (SBERT)
^^^^^^^^^^^^^^^^^^^^^^
Used in the clustering algorithm
https://arxiv.org/abs/1908.10084

https://www.groundai.com/project/sentence-bert-sentence-embeddings-using-siamese-bert-networks/1
[code available](https://github.com/UKPLab/sentence-transformers)
