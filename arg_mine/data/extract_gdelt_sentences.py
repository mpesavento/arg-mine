"""
Main entry point for document sentence argument classification from a list of URLs
TODO: add unit testing for the CLI options
"""
import os
import logging

import click
from dotenv import find_dotenv, load_dotenv

from arg_mine import DATA_DIR
from arg_mine.data.loaders import get_gdelt_df
from arg_mine.api import classify
from arg_mine import utils


_logger = utils.get_logger(__name__, logging.DEBUG)

# formatted string template for the output filenames
_WRITE_FILENAME_FMT = "gdelt_{year}_{data}_docs{start:0{ndigit}d}-{end:0{ndigit}d}.csv"


@click.command()
@click.option(
    "--ndocs",
    default=100,
    type=int,
    help="The number of documents we want to extract from the list",
)
@click.option(
    "--start-row",
    default=0,
    type=int,
    help="Starting row from document URL list for given year (zero indexed). Limiting done by setting end-row or ndocs",
)
@click.option(
    "--end-row",
    default=None,
    type=int,
    help="Ending row from document URL list for given year, exclusive.",
)
@click.option(
    "--chunk-size",
    default=100,
    type=int,
    help="how many articles to process in each iteration; used to clear grequests memory leak",
)
@click.option(
    "--batch-size",
    default=None,
    type=int,
    help=(
        "How many articles to iterate through before writing to output file. "
        "If set to None, the extraction will write all outputs to single files, rather than batched"
    ),
)
@click.option(
    "--year", default=2020, type=int, help="Which GDELT year to run the extraction on"
)
def main(ndocs, start_row, end_row, chunk_size, batch_size, year):
    """
    Download and extract GDELT data to "data/raw/2020-climate-change-narrative"
    """
    assert ndocs or end_row, (
        "Need to either have valid `ndocs` or `end_row`, given:\n"
        "ndocs: {}, start_row={}, end_row={}".format(ndocs, start_row, end_row)
    )

    assert year in list(
        range(2015, 2021)
    ), "Given year does not match available years (2015-2020), given: {}".format(year)

    # load input data
    topic = "climate change"
    in_csv_datapath = os.path.join(DATA_DIR, "raw", "2020-climate-change-narrative")
    csv_filepath = os.path.join(
        in_csv_datapath, "WebNewsEnglishSnippets.{}.csv".format(year)
    )

    url_df = get_gdelt_df(csv_filepath)
    total_n_docs = url_df.shape[0]  # total number of documents in the target year

    # set up output directory
    target_dir = "gdelt-climate-change-docs-test"
    out_data_path = os.path.join(DATA_DIR, "processed", target_dir)
    os.makedirs(out_data_path, exist_ok=True)

    # check if ndocs is bigger than the size of the source data, and limit
    if not ndocs or ndocs > total_n_docs:
        ndocs = total_n_docs

    batch_size = batch_size or total_n_docs

    # Select the target URLS, up to ndocs
    # Note that this is always starting from zero. A future iteration can add
    # start/stop commands to the application for more targeted batches
    # TODO: add testing for this logic. and simplify!
    if start_row == 0 and ndocs is not None:
        # ignore end_row, default
        print(1)
        end_row = ndocs
    elif end_row is None and ndocs:
        print(2)
        end_row = start_row + ndocs
    elif start_row and end_row and ndocs != (end_row-start_row):
        print(3)
        # we set the end_row to stop on, but it doesnt match the target ndocs.
        # warn, and set ndocs to end_row
        _logger.warning("Both ndocs and end_row are specified and don't match; using end_row")
        ndocs = end_row
    else:
        msg = (
            "You need to specify ndocs, (start_row, ndocs), or (start_row, end_row)\n"
            "given: ndocs: {}, start_row={}, end_row={}".format(
                ndocs, start_row, end_row
            )
        )
        _logger.error(msg)
        raise ValueError(msg)

    print("ndocs: {}, start_row={}, end_row={}".format(
                ndocs, start_row, end_row
            ))

    # crop the URL list
    url_list = url_df.content_url.values[start_row:end_row]

    ndigit = len(str(total_n_docs))  # zero padding for doc counts

    # TODO: better is to wrap the output pattern rather than repeat it
    if ndocs >= batch_size and total_n_docs > batch_size:
        _logger.info(
            "Running {} BATCHED documents from file: {}, batch size={}".format(
                ndocs, csv_filepath, batch_size
            )
        )

        # we write and append in batches
        # iterate through the url_list, but use start_row to keep track of where we started
        # TODO: simplify the indexing between the CSV file rows and the url_list batches
        for batch_ix, doc_ix in enumerate(range(0, len(url_list), batch_size)):
            start_ix = doc_ix
            end_ix = doc_ix + batch_size - 1  # this is inclusive!!!
            _logger.debug("Running batch {} [{}-{}]".format(batch_ix, start_ix, end_ix))
            responses = classify.fetch_concurrent(
                topic,
                url_list=url_list[start_ix:end_ix + 1],
                chunk_size=chunk_size,
            )
            docs_df, sentences_df, missing_docs = classify.process_responses(responses)

            # save outputs to CSV
            docs_df.to_csv(
                os.path.join(
                    out_data_path,
                    _WRITE_FILENAME_FMT.format(
                        data="docs",
                        start=start_row + start_ix,
                        end=start_row + end_ix,
                        ndigit=ndigit,
                        year=year,
                    ),
                ),
                header=True,
                index=False,
            )
            sentences_df.to_csv(
                os.path.join(
                    out_data_path,
                    _WRITE_FILENAME_FMT.format(
                        data="sentences",
                        start=start_row + start_ix,
                        end=start_row + end_ix,
                        ndigit=ndigit,
                        year=year,
                    ),
                ),
                header=True,
                index=False,
            )

    else:
        _logger.info(
            "Running {} documents from {} docs in file: {}".format(
                ndocs, total_n_docs, csv_filepath
            )
        )
        responses = classify.fetch_concurrent(
            topic, url_list=url_list, chunk_size=chunk_size
        )
        docs_df, sentences_df, missing_docs = classify.process_responses(responses)
        print(docs_df.shape)
        print(len(missing_docs))
        # save outputs to CSV
        docs_df.to_csv(
            os.path.join(
                out_data_path,
                _WRITE_FILENAME_FMT.format(
                    data="docs", start=start_row, end=ndocs, ndigit=ndigit, year=year,
                ),
            ),
            header=True,
            index=False,
        )
        sentences_df.to_csv(
            os.path.join(
                out_data_path,
                _WRITE_FILENAME_FMT.format(
                    data="sentences", start=start_row, end=ndocs, ndigit=ndigit, year=year,
                ),
            ),
            header=True,
            index=False,
        )


if __name__ == "__main__":

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())

    main()
