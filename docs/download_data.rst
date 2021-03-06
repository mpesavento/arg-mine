.. _`download-data`:

Downloading existing datasets
=============================

Some data has already been downloaded and made rapidly accessible to the
``arg-mine`` application. This data can be downloaded via synchronizing to the
AWS S3 project bucket.

The datasets currently exist in two stages: ``raw`` and ``processed``. Here, we
describe the process of downloading the raw data. In :ref:`extract_arugments`, we
show how to run the extraction API to download document metadata and the associated
sentences and sentence metadata.

AWS Storage
-----------

Downloaded and already processed data is stored in the AWS bucket associated with the
Great American Debate AWS account. The URL is given below.

**Project data AWS S3 bucket URI**:
    https://s3.console.aws.amazon.com/s3/buckets/arg-mine-gdelt-data/

The contents of this bucket are structured identically to the content in the root
``data/`` folder for the repository, serving to act as a backup cache for any data that is
downloaded or extracted.

* ``make sync_data_to_s3`` will use ``aws s3 sync`` to recursively sync files in your local ``arg-mmine/data/`` up to `arg-mine-gdelt-data/data/`.
* ``make sync_data_from_s3`` will use ``aws s3 sync`` to recursively sync files from ``arg-mine-gdelt-data/data/`` to local ``arg-mine/data/``.

If working in a new instance, either on an EC2 or your local host, you will want to:

1. download existing data via ``make sync_data_to_s3``
2. run your extraction with ``make batch_extract_gdelt`` (see :ref:`extract_arguments` for more information)
3. sync the new data to S3 with ``make sync_data_from_s3``


GDELT dataset
-------------
This project uses the
`GDELT climate change dataset <https://blog.gdeltproject.org/a-new-contextual-dataset-for-exploring-climate-change-narratives-6-3m-english-news-urls-with-contextual-snippets-2015-2020/>`_,
which encompasses online media stories from global sources over the time span of 2015-2020.
The data consists mainly of a list of URLs to the target articles, the title of the article, and
a "label" containing the context from the article with one of the key phrases used to create the dataset.

The dataset was created by doing a search for the inclusive OR of the following keywords:

* climate change
* global warming
* climate crisis
* greenhouse gas
* greenhouse gases
* carbon tax

The included context contains the keyword, and approximately 100 characters preceding
and following the identified keyword.

In this study, we are not using the context; we are only using the list of URLs to extract sentences
from each document using the `ArgumentText API <https://api.argumentsearch.com/en/doc>`_.

To see more information on the raw download process, see :ref:`../arg_mine/data/download_gdelt_climate_en`


Download GDELT URLs
-------------------
You can manually download the .zip files from the `GDELT dataset`_ webpage.
A simpler way to do this would be to run the makefile command::

    make download-gdelt

This will download all years of the dataset into the repositories
``data/raw/2020-climate-change-narrative`` folder,
extract the zip files into the CSV files, and remove the leftover zip files,
leaving only the CSVs containing the URLs

The `make download-gdelt` command is a thin wrapper into a docker instance that runs the
command::

    arg_mine/data/download_gdelt_climate_en.py

This python command does the downloading. The code can be seen
here :file:`../arg_mine/data/download_gdelt_climate_en.py`


This download will consume 7 MB of your harddrive space.

Load the GDELT data
^^^^^^^^^^^^^^^^^^^
Data loaders have been written to easily read the CSV data for your target year.
The GDELT loader automatically creates a ``pd.Timestamp`` from the parsed datetime in the CSV files.


.. code-block:: python

    import os
    import pandas as pd
    from arg_mine import DATA_DIR
    from arg_mine.data import loaders
    csv_datapath = os.path.join(DATA_DIR, "raw", "2020-climate-change-narrative")
    csv_filepath = os.path.join(csv_datapath, "WebNewsEnglishSnippets.2020.csv")
    url_df = loaders.get_gdelt_df(csv_filepath)

This returns a pandas DataFrame containing the contents of the GDELT dataset.
One can readily concatenate all GDELT data as well:

.. code-block:: python

    all_gdelt_data_df = pd.concat([loaders.get_gdelt_df(os.path.join(
        csv_datapath, "WebNewsEnglishSnippets.{}.csv".format(year)))
         for year in range(2015, 2021)], axis=0)

which writes out to ``stdout`` via logging:

.. code-block::

    INFO:2020-08-05 18:42:49,503:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2015.csv
    INFO:2020-08-05 18:43:01,592:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2016.csv
    INFO:2020-08-05 18:43:15,734:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2017.csv
    INFO:2020-08-05 18:43:26,640:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2018.csv
    INFO:2020-08-05 18:43:36,511:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2019.csv
    INFO:2020-08-05 18:43:50,968:arg_mine.data.loaders: reading data from: /Users/mpesavento/src/arg-mine/data/raw/2020-climate-change-narrative/WebNewsEnglishSnippets.2020.csv

Most commands automatically use logging. If desired, an outer service application can be
written to output all logs to a log file, rather than ``stdout``.




Next
^^^^
In the next section, we will learn about argument extraction based on the raw GDELT data.
:ref:`extract_arguments`
