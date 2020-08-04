Downloading existing datasets
=============================

Some data has already been downloaded and made rapidly accessible to the
``arg-mine`` application. This data can be downloaded via synchronizing to the
AWS S3 project bucket.

**Project data bucket URI**
(why is this not bolding, or line breaking??
https://s3.console.aws.amazon.com/s3/buckets/arg-mine-gdelt-data/

The datasets currently exist in two stages: ``raw`` and ``processed``.

Raw data
--------
This is the
`GDELT dataset <https://blog.gdeltproject.org/a-new-contextual-dataset-for-exploring-climate-change-narratives-6-3m-english-news-urls-with-contextual-snippets-2015-2020/>`_,
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

Download GDELT
^^^^^^^^^^^^^^^
You can manually download the .zip files from the `GDELT dataset`_ webpage.
A simpler way to do this would be to run the makefile command::

    make download-gdelt

This will download all years of the dataset into the repositories
``data/raw/2020-climate-change-narrative`` folder, extract the zip files into the CSV files,
and remove the leftover zip files.

To see more information on the raw download process, see :ref:`download_gdelt_climate_en`

:: warning:: This download will consume 7 MB of your harddrive space.

