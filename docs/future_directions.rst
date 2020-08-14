.. `future_directions`:

Future Directions
=================

There is still a lot of work that can be done to improve this tool. Here, we outline
a few of the suggested improvements on the software engineering side, as well
as future directions that the data extraction, argument mining, and argument clustering
can take.



TODO
---------
There are so many things to do to improve this package.

* move ``classify.fetch_concurrent()`` into sessions
* swap ``grequests`` out for ``requests-futures``, removing the monkey patch warning
* Stratify the extraction code; we are doing the same error handling in too many places

* Add a context manager for the authentication tokens in ``arg_mine.api.auth``


Next Steps
---------------
The next step in this process will be to do a clustering analysis across all sentences
that contain arguments to identify similarities. The
`ArgumenText API <https://api.argumentsearch.com/en/doc#api.cluster_arguments>`_
has a ``cluster_arguments`` HTTP access point suitable for this purpose,
utilizing an `SBERT <https://arxiv.org/abs/1908.10084>`_ model for the sentence
clustering.

Future work will be able to utilize the low-level wrapper and error handling
around the ``requests`` module to query the clustering end point.


