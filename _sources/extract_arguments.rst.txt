.. _`extract_arguments`:

Extracting arguments from GDELT documents
=========================================

To more rapidly and effectively examine the Great American Debate on climate change,
we want to identify arguments and claims made in internet content related to climate change.

The sentences that contain arguments can then be further processed for analyzing
the content and position of the argument, including whether they are for or against
the given topic. However, this is a time-consuming process for humans to do. It
would be far more efficient for a machine to automatically pre-label each sentence
with whether or not there may be an argument or claim within that sentence, with some
confidence.

The `ArgumentText API <https://api.argumentsearch.com/en/doc>`_ allows
queries via a `RESTful <https://en.wikipedia.org/wiki/Representational_state_transfer>`_
API, running a BERT-like model for argument extraction.

TODO: more content here, point to the references doc?

Below, we describe how to use this API for argument extraction from a list of URLs
containing web articles on a target topic.

Using the high-level extractor application
------------------------------------------
blarg

Using the ``sessions`` API
--------------------------
We provide a low-level wrapper around the
`ArgumentText REST API calls <https://api.argumentsearch.com/en/doc>`_,
allowing configurable access to changing the different parameters used in the query.
