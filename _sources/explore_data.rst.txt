.. _`explore_data`:

Exploring the Mined Argument Data
=================================

So now you have some datasets, consisting of the documents and the sentences
from those documents. What does this data look like? What can we do with it downstream?



Argument Classification results
-------------------------------
What is an argument, or a claim?
The `Great American Debate <https://www.greatamericandebate.org/>`_ has clear
definitions for these terms, which is beyond the scope of this documentation.
The ArgumenText classifier is designed to identify a token (in this case a sentence)
that contains an argument or claim. Manual review of a subset of classified sentences
revealed that the model does a reasonable job at identifying sentences that contain
claims. It must be noted that it does not isolate the claim(s) in a sentence, only
flag that a claim is present.

The trained BERT-like model underlying the
`ArgumentText classifier <https://aaai.org/Papers/AAAI/2020GB/AAAI-TrautmannD.7498.pdf>`_
was trained on 8 different topics, none of which are related to climate change.
However, the primary literature suggests that the model is reasonably good at
transfer learning, and is able to generalize to other topics such as climate change.

As referenced in the ArgumenText API `documentation <https://api.argumentsearch.com/en/doc>`_,
for a URL that is passed in, the model returns all of the parsed sentences, whether or not the
sentence contains an ``argument`` or ``no argument`` (thresholded at 0.5 confidence),
the confidence score of the label, and the predicted stance (``pro`` vs ``con``), which
is currently not being used.

The returned data can be controlled with the ``arg-mine`` API, via
``arg_mine.api.classify.bundle_payload()``. Two main factors that will affect the outputs
are the ``topicRelevance`` model and ``showOnlyArgs`` option.

The ``topicRelevance`` model (default: ``word2vec``)selects the word distance matching algorithm to find
words that are similar to the given topic, eg "climate change". The ``classify.TopicRelevance``
enum class contains all of the possible options. Other options include ``match-string``
and ``n_gram_overlap``. ``word2vec`` was selected as the default for the most breadth
in identifying sentences related to the selected topic. Further studies may examine
the changes in model performance depending on which ``topicRelevance`` is selected.

The ``showOnlyArgs`` decreases the memory load on the client computer (currently unclear if
it decreases computational load on the API server) by only returning sentences that are classified
as arguments. However, this has the side effect of possibly missing some sentences
that contain arguments and have a confidence score lower than 0.50.


Argument Mining accuracy
------------------------
While the transfer learning of the BERT-based argument classifier is reasonably
performative, it is not perfect. In a
`report <https://github.com/mpesavento/arg-mine/blob/master/notebooks/reports/argText%20accuracy%20evaluation%2020200714.ipynb>`_
done to evaluate the accuracy, precision,
and recall of the model, we analyzed the results on 600 manually labeled sentences.
With a dataset based on the presumed natural
distribution of sentences containing arguments vs no arguments (~21% of published articles),
we see

+-----------------+----------+-----------+----------+----------+----------+
|                 | accuracy | precision | recall   | f1_score | roc_auc  |
+-----------------+----------+-----------+----------+----------+----------+
| threshold = 0.5 | 0.821429 | 0.555556  | 0.833333 | 0.666667 | 0.894746 |
+-----------------+----------+-----------+----------+----------+----------+

Overall, the model correctly identifies 82% of the true positives and true negatives.
The recall score of ``0.83`` indicates that the model is pretty good at identifying
arugment sentences as argument sentences.

The mediocre precision score indicates that out of the sentences that the model
thinks are arguments, just over half of them are actually arguments. Part of the
reason behind this is based on the fact that sentences containing arguments are
more rare than sentences without arguments (about 1 in 5). This ratio may be different
depending on the topic selected.

The precision score can be slightly increased (order of 0.1) by increasing the threshold
of confidence values from 0.5 to 0.90. This would also cause a corresponding decrease
in recall, resulting in more false negatives (sentences that are actually
arguments labeled as not argument).

To adjust for the target balance of precision vs recall, the user can threshold
based on the confidence value returned.

.. code-block:: python

    from arg_mine import DATA_DIR
    from arg_mine.data import loaders
    data_processed_project = "gdelt-climate-change-docs"
    base_path = os.path.join(DATA_DIR, "processed", data_processed_project)
    docs_df = loaders.load_processed_csv("gdelt_2020_docs_docs0-999.csv", data_processed_project)
    sentences_df = loaders.load_processed_csv("gdelt_2020_sentences_docs0-999.csv", data_processed_project, drop_nan_cols='sentence_original')
    target_threshold = 0.75

    sentences_df['argument_outcome'] = (sentences_df.argument_confidence > target_threshold).astype(int)

This code creates a new column in the sentences dataframe that contains a binary integer result
for all sentences that have a confidence greater than the given threshold.
From this column, the user can rapidly identify sentences that contain arguments.

