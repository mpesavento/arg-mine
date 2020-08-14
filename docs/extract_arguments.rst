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
API, running a BERT-like model for argument extraction. The primary literature for
the argument mining model can be found in :ref:`modeling_references`.

Below, we describe how to use this API for argument extraction from a list of URLs
containing web articles on a target topic.

Currently, all data is stored as CSV files. The intended structure of the objects
methods is to make it easy to link to a SQL database containing extracted document
data. To hold the primary content in a format that is easy to translate between
returned query data, CSV, and eventually database rows, we have the
``DocumentMetadata`` object for document metadata, and the ``ClassifiedSentences``
objet for holding the model predictions per extracted sentence.

ArgumenText API
---------------
The lowest level Application Programming Interface is the RESTful server, hosted at
`<https://api.argumentsearch.com/en>`_. This endpoint has subpaths, depending
on whether you want to classify, cluster, or search, eg
``https://api.argumentsearch.com/en/classify``.
The design is to use the POST verb via HTTP, with a JSON payload containing the
target content and required parameters. These parameters are fully documented
`here <https://api.argumentsearch.com/en/doc>`_.

The model published as a service contains proprietary training data, so does not
exactly match the model described in the
`AURC paper <https://aaai.org/Papers/AAAI/2020GB/AAAI-TrautmannD.7498.pdf>`_.

It is important to note the limitations of the service. Based on communication
with the author of the service (Johannes Daxenberger, a collaborator with the
`AURC paper <https://aaai.org/Papers/AAAI/2020GB/AAAI-TrautmannD.7498.pdf>`_), there are a few key limitations to note:

1. There is an internal limit in the server for the number of concurrent connections
   that can occur in parallel, with a given API key. This number is reported to be
   a maximum of ``3`` threads, but this has not been verified. As a rule of thumb,
   it is more efficient to send longer texts in a single request,
   then multiple shorter requests in parallel.
2. The server times out on a given classification task after 200 seconds (3.3 minutes).
   This means that if a document is too large, or you send the server too much content
   to process in a single task, that it may time out on processing the sentence
   classification.

Internally, ArgumenText uses Apache Tika or JusText for article parsing from
the html webpages into articles and sentences. As such, it is not perfect, and may
return portions of the webpage that may not be considered part of the main article body.


Command Line Interface for document URL argument extraction
-----------------------------------------------------------

The top level method for running an extraction is the CLI application entry point::

    python arg_mine/data/extract_gdelt_sentences.py --year=2020 --ndocs=1000

This command will run an extraction on the first 1000 URLs in the year 2020 dataset.

The command currently defaults to the year ``2020``, so you must include that flag
if you want to run extractions from any other year.

The ``ndocs`` flag specifies the number of documents in the given GDELT year to extract.
By default, this starts at the first row (row 0) of the year's dataset.

For more information on the extraction app, see the help content::

    python arg_mine/data/extract_gdelt_sentences.py --help

Output files
^^^^^^^^^^^^^
The output files will be saved to
``data/processed/gdelt-climate-change-docs`` in two separate files, one for the
document metadata (``gdelt_{year}_docs_*.csv``), one for the sentences and their
associated likelihood of containing an arugment or not (``gdelt_{year}_sentences_*.csv``).
For example::

    python arg_mine/data/extract_gdelt_sentences.py --year=2020 --ndocs=1000

loads the dataset for year 2020, and extracts the first 1000 sentences and classifications
into the files ``gdelt_2020_docs_docs0000-0999.csv`` and ``gdelt_2020_sentences_docs0000-0999.csv``
Note that if you do not specify ``start-row``, it will default to 0, and always start at the
first document of the year's dataset.

Note that while a filename may span over a start and end index (say, 0-999), the
content inside the file may not have that many documents listed internally (eg 1000).
This is due to data attrition, and a significant number of the articles in the
GDELT dataset returning 404, and thus no available data. This attrition rate
appears to be close to 25%. For example, out of 1000 articles, you may expect to see 750
within the output file.

The docs file contains the output from the ``DocumentMetadata`` class, and
has the following columns:

* doc_id
* url
* topic
* model_version
* language
* time_argument_prediction
* time_attention_computation
* time_preprocessing
* time_stance_prediction
* time_logging
* time_total
* total_arguments
* total_contra_arguments
* total_pro_arguments
* total_non_arguments
* total_classified_sentences

The sentences file contains the output from the ``ClassifiedSentence`` class, and
has the following columns:

* doc_id
* url
* topic
* sentence_id
* argument_confidence
* argument_label
* sentence_original
* sentence_preprocessed
* sort_confidence
* stance_confidence
* stance_label


Other than the ``doc_id`` and ``sentence_id``, all of these values come from the
`ArgumenText API classify output <https://api.argumentsearch.com/en/doc#api.classify_api>`_
See their documentation for further information on each column.


Start/end document URL indexing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can specify the start and end row for a given year. This is useful if you
want to manually create batched extractions for a given year. For example::

    python arg_mine/data/extract_gdelt_sentences.py --year=2020 --start-row=42 --end-row=156

would start at row 42 in the GDELT 2020 dataset up through row 156. Note that
``end-row`` is exclusive, keeping consistent with python indexing.

You can also specify the number of documents you want to extract from a starting row::

    python arg_mine/data/extract_gdelt_sentences.py --year=2020 --start-row=42 --ndocs=100

which would return 100 documents worth of sentences, starting with document 42.


Batch extraction
^^^^^^^^^^^^^^^^^^^^^^^
The extraction job may iterate over many documents, which can eventually cause
a memory error on the user's host running the extraction application. In addition,
errors may occur late in an extraction that would cause all prior data in memory
to be lost if the application fails for some reason.

To mitigate this, you can run an extraction in batches, where it writes the output
from the argument miner API to the output files at the end of every batch::

    python arg_mine/data/extract_gdelt_sentences.py --year=2020 --ndocs=5000 --batch-size=1000

This line extracts sentences from the first 5k documents in 2020, iterating
with a batch size of 1000 documents over 5 batches. This will give five output files
with the document metadata, and five files containing all of the classified sentences.

Bathc extraction is to be used in memory-limited environments. For example,
when running the extraction job on an EC2 ``t2.large`` instance with 8 GB of memory,
you may limited to a maximum batch size on the order of 100000 documents. Given that the
full GDELT dataset contains 5 million articles, batch processing would make sense here.

It takes approximately 8 hours to run 10000 articles. During that time, the application
or server may crash, so saving the extracted data once an hour may be a reasonable guideline,
more so than the limitations on memory.

Document and Sentence IDs
----------------------------
A few notes on IDs and cross-linking between sentences and documents.
To make it easy to identify unique documents and unique sentences, we use the
`MD5 <https://en.wikipedia.org/wiki/MD5>`_ hash generation algorithm to create unique
IDs.

For each URL in the GDELT dataset, we use the full URL as the input string
to the hash. This guarantees that each document ID will be unique to each URL we extract.
If there are duplicate URLs, we can search on unique IDs to only return unique
documents.

.. code-block:: python

    from arg_mine import utils
    utils.unique_hash("https://www.stourbridgenews.co.uk/news/national/18141364.seven-arrested-gas-rig-protest/")

gives:

.. code-block::

    cc5e8dcf8b787ea4fc0f7455a84559ac

Similarly, for sentence IDs we use the full sentence string to create the hash;
in particular, we use the ``sentencePreprocessed`` output from the ArgumenText API.
The benefit of using the sentence as the input to the MD5 hash is that it becomes really
easy to see if the same sentences are being used across different articles.

.. code-block:: python

    utils.unique_hash("She said the oil and gas industry is “part of the solution” to climate change.")

gives:

.. code-block::

    6086288265e33cf745512f794d26e9ed

These hash values are saved in the CSV files, and will be useful for linking the
target tables in a database. For example, you can find all sentences associated
with a given article rapidly if you know the doc_id or the origin URL.


Using the ``classify`` module
-------------------------------

We provide a low-level wrapper around the
`ArgumentText REST API calls <https://api.argumentsearch.com/en/doc>`_,
allowing configurable access to changing the different parameters used in the query.

There are two primary data classes that are used to create data objects from the
information returned from the REST API.

`DocumentMetadata`
^^^^^^^^^^^^^^^^^^
A data class that catches the returned dictionary from the low level ``requests``
API call and makes it readily accessible and convertible to other formats.
It also adds a ``doc_id``, based on the MD5 hash of the URL.
This id serves as a unique index for each document,
allowing rapid cross-referencing between sentences and document metadata.


`ClassifiedSentence`
^^^^^^^^^^^^^^^^^^^^
A data class that catches the returned dictionary from the low level ``requests``
API call. It also creates the URL-associated ``doc_id`` and a ``sentence_id``,
based on the MD5 hash of the sentence. This has the side benefit of rapidly
checking if identical sentences are repeated across different documents.

This class also uses the enum class ``ArgumentLabel`` consistently identify
whether a sentence contains an argument or not, eg ``argument`` or ``no argument``.

It also uses the enum class ``StanceLabel``, with the possible values of ``pro``,
``con``, and NA (empty string).


Argument Mining from web documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The easiest way to classify all sentences in a single document is via the
``classify.classify_url_sentences`` method. Given the target topic, web url, and
the necessary ArugmenText API keys (loaded from the .env file), we can
quickly get the returned output from the API. Using the ``DocumentMetadata``
and ``ClassifiedSentence`` data classes, we can easily create parsable objects
from the dict returned from the API.

.. code-block:: python

    from arg_mine.api import classify, auth, utils
    user_id, api_key = auth.load_auth_tokens()
    topic = "climate change"
    url = "http://westchester.news12.com/story/41551116/firefighter-dies-as-australia-plans-to-adapt-to-wildfires"
    out_dict = classify.classify_url_sentences(topic, url, user_id, api_key)

    doc_metadata = classify.DocumentMetadata.from_dict(out_dict["metadata"]))
    sentence_list = [
        classify.ClassifiedSentence.from_dict(url, topic, sentence)
        for sentence in out_dict["sentences"]
    ]

The sentence_list can easily be turned into a pandas DataFrame:

.. code-block:: python

    sentence_df = pd.DataFrame(utils.dataclasses_to_dicts(sentence_list))

While this pattern works well for a single document, extraction from tens of thousands
needs something a bit easier.

A list of URLs can be run through the API with the following call:

.. code-block:: python

    doc_list, sentence_list, refused_doc_list = classify.collect_sentences_by_topic(topic, url_list)

Still, this method is slow and does not have the ability to run in parallel.

Concurrency
^^^^^^^^^^^

Given a list of urls (eg ``url_list`` below), two simple calls can run the classification
query on the given URLs.

.. code-block:: python

    url_list=[
        'https://www.stourbridgenews.co.uk/news/national/18141364.seven-arrested-gas-rig-protest/',
        'http://global.chinadaily.com.cn/a/202001/07/WS5e13ea37a310cf3e35582e46.html'
        ]
    responses = classify.fetch_concurrent(topic="climate change", url_list=url_list)
    docs_df, sentences_df, missing_docs = classify.process_responses(responses)

The line with ``classify.fetch_concurrent`` uses concurrent requests (via ``grequests``) to send ``POST`` requests to
the ArgumenText API server. It returns the response objects from the `requests` module.

The line with ``classify.process_responses`` parses the server responses, returning a pandas DataFrame for the
document metadata (from `DocumentMetadata`), and a pandas DataFrame for the sentence
classification results (from `ClassifiedSentence`). It also returns a list
of the documents that returned a 404 (see `"Missing" documents`_ below) or the
API was otherwise unable to process the request.


"Missing" documents
^^^^^^^^^^^^^^^^^^^
Some URLs in the dataset may point to articles that no longer exist, or at least
are not visible on the host website. These URLs would produce a
`HTTP 404 <https://en.wikipedia.org/wiki/HTTP_404>`_ error when the content is requested.

While the high level API handles these errors, it currently does so silently in
CLI sentence classifier. This code can be modified to save the missed documents
in a separate output file, if desired.



Using the ``sessions`` module
-------------------------------
A low level API has been built for using sessions in python ``requests``.
The ``session`` module is the basis of a general platform to wrap the
different components of the ArgumenText API. It provides general error handling
and classes for managing the different possible endpoints
("classify", "cluster_arguments", and "search"). The ``classify`` module is written
around the matching API endpoint, with future expansion readily accessible.

Of note, the ``session.get_session()`` method returns a python ``requests``
session with various timeout and retry logic embedded in it. This
has proven to be extremely useful when the ArgumenText API server is unable
to keep up with the load being requested.

This module also contains the low level ``session.fetch()`` method, which performs error
handling and response extraction for the basic classifier mechanisms. This
method contains layers of error handling around the requests.push() call to the
API end point. Generally, the user shouldn't need to look into this method.
Much of the structure in ``session.fetch()`` is duplicated in
``classify.fetch_concurrent()``, which could probably use some refactoring and
simplification.

