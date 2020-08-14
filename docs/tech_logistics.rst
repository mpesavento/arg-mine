.. `tech_logistics`:

Technical Logistics
===================
There are a few key logistical notes that must be documented. These notes will
help guide business decisions on how to proceed with using the ``arg-mine`` tool
presented here.

Cost (time and $$)
---------------------
How much does it cost to use the ArgumenText API to extract arguments from
the GDELT dataset?

Time
^^^^
As observed in experiments that were not fully optimized for parallelization,
the current time estimate is that it take roughly ``1.8 (± 1)`` seconds per URL.
This time includes 1) sending the HTTP request, 2) server parsing and classification,
3) return of the response from the server, 4) local parsing of the response.
The duration of processing time will vary depending on the length of the article,
and how many sentences there are to be classified as argument or no argument.

If we assume a linear extrapolation, this implies that:

|    100 documents = 3 minutes
|    1000 documents  = 30 minutes
|    10000 documents = 300 minutes (5 hours)
|    100000 documents = 3000 minutes (50 hours)
|    1000000 (1M) documents = 30000 minutes (500 hours, or 20.8 days)

These durations have been empirically confirmed up to 10k documents.

With one year worth of data representing approximately 1M documents, it would take
3 weeks of compute time to extract one year worth of argument data.

Note that these time estimates were created by running the extraction locally,
rather than on an EC2 machine. However, the 10k URL extraction that was performed
on an EC2 machine roughly corresponds to the 5 hours estimated above, possibly
a little bit faster.

These times were calculated based on the current speed of the
``classify.fetch_concurrent()`` call. However, we know that this call is not
using concurrency correctly, so we could easily see a 2x reduction in duration
with improved concurrent requests to the server.

We discuss the challenges in concurrency below, in :ref:`future_strategy`.

Money
^^^^^
The times created above were run on a ``t2.large``
`EC2 instance <https://aws.amazon.com/ec2/instance-types/t2/>`_, with
2 CPus and 8 GB of RAM. This instance costs $0.0928/hr with on-demand pricing.

| Running a single server for 24 hours will cost $2.227.
| Running a single server for 168 hours (7 days) will cost $15.59
| Running a single server for 504 hours (21 days) will cost $46.72

Running 20 servers for 24 hours (480 total compute hours) will cost $44.54

Storing the data in S3 will also have an ongoing cost. Current
`S3 storage rates <https://aws.amazon.com/s3/pricing/>`_
are ``$0.023 / GB``, for the first 50 TB under standard tier pricing. There are
other tiers available for infrequently accessed data, which can cut the cost roughly
in half to $0.0125 / GB

From the current data stored on S3, 10000 attempted URLs (actual returned 7450 results)
takes approximately 300 MB of space on disk with the CSV files. This costs roughly
$0.006 per month.

If we linearly extrapolate, we obtain the following disk usage estimates.

| 10000 documents = 300 MB
| 100000 documents = 3 GB
| 1000000 documents = 30 GB
| 5000000 documents = 150 GB

If the entire 5M dataset of sentences is extracted, it would take roughly 150 GB
of storage on S3, and have a monthly cost of $3.45 / month.

.. _`future_strategy`:

Future Strategy
^^^^^^^^^^^^^^^
Divide and conquer tends to be the solution for "big data" problems, and this problem
is no exception. The HTTP requests are set up so that they can be processed in parallel
by as many machines as necessary, with no requirements for shared state or memory between
processes.

This is immensely advantageous, in that one machine taking 21 days to process
1 million documents could also be reduced to 21 machines taking 1 day to process
1 million documents. The cost of using that many servers would be roughly the same
as if one server was running for 21 days.

The most significant blocker is that the ArgumenText API only supports up to 3
requests at a time, presumably associated with a given API key. This is not likely
to change in the near future. Possible workarounds include using 3 servers at a
time with the same key, and obtaining additional keys to scale up. This adds complexity,
which may not be beneficial in the long run.

**Current suggestion**

Use ``fetch_concurrent()`` to run a set of extractions from a single server, given
a specific index range. Set up 3 servers to simultaneously run extractions, each with
a specified non-overlapping index range (remember that the ``end-index`` is exclusive!).

Eg:

| Have server A iterate over 300,000 URLs in batch sizes of 10000, from [0-300000)
| Have server B iterate over 300,000 URLs in batch sizes of 10000, from [300000-600000)
| Have server C iterate over 400,000 URLs in batch sizes of 10000, from [600000-1000000)

The 10k batch sizes should be sufficient to fit in 8 GB memory, and take 5 hours to complete
each batch. If an error occurs in a given batch and the data is lost, identify the last valid
index and restart the job from that start row.

The extraction of 1M documents should have a total cost of $45.00 of compute time,
and $0.69 in S3 storage.


``arg_mine`` package improvements
----------------------------------

There is still a lot of work that can be done to improve this tool. Here, we outline
a few of the suggested improvements on the software engineering side, as well
as future directions that the data extraction, argument mining, and argument clustering
can take.

Concurrency
^^^^^^^^^^^^^
A decision was made to use ``grequests`` package for concurrent HTTP requests.
While this may have worked, this package is rapidly becoming derelict, with
``requests-futures`` or ``concurrent-futures`` (see `this <https://stackoverflow.com/a/46144596>`_)
for doing the asynchronous request parsing.

* move ``classify.fetch_concurrent()`` into sessions
* swap ``grequests`` out for ``requests-futures``, removing the monkey patch warning
* Test & confirm that new concurrency gives a 1.5-3x improvement over serial processing
* Refactor the classify/session code; we are doing the same error handling in too many places


Storage
^^^^^^^^^
Currently, we are relying on manual sync or upload of the local data files
to the S3 bucket. This model is incomplete, and has the possibility of
data file collisions (one file overwriting another). Hopefully the naming should
be unique enough to prevent this, but it is still possible.

Another possible mechanism is to load the CSV files into SQL tables (using
`Amazon RDS <https://aws.amazon.com/rds/sqlserver/>`_. This
would provide a longer term storage solution, and give rapid queryable access
to the target data.

A suggested target is to be able to use ElastiSearch over the S3 data files.
While this may be feasible, it has not been looked into concretely.


Code cleanliness
^^^^^^^^^^^^^^^^^^
While the author of the package did their best, there are definitely a string of
``TODOs`` throughout the package. Here are some of the more important tech debt
items that should be addressed.

* Add unit tests for ``arg_mine.data.extract_gdelt_sentences``
* Add unit tests for ``arg_mine.api.classify`` business logic
* Add a context manager for the authentication tokens in ``arg_mine.api.auth``
* Test efficiency of using the ``only_arguments`` parameter in the classify payload
  (expect to see reduced local memory load, and possibly reduced server time)


Adding cluster requests API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The next step in this process will be to do a clustering analysis across all sentences
that contain arguments to identify similarities. The
`ArgumenText API <https://api.argumentsearch.com/en/doc#api.cluster_arguments>`_
has a ``cluster_arguments`` HTTP access point suitable for this purpose,
utilizing an `SBERT <https://arxiv.org/abs/1908.10084>`_ model for the sentence
clustering.

Future work will be able to utilize the low-level wrapper and error handling
around the ``requests`` module to query the clustering end point. Given
the targeted concurrency model refactoring, the ```arg_mine.api.sessions`` module should
be ready to use in the creation of a new ``arg_mine.api.clustering`` module, paralleling
the work done in ``arg_mine.api.classify``.


