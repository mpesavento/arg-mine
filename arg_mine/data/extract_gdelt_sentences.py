import os
import logging

import click
from dotenv import find_dotenv, load_dotenv

from arg_mine import DATA_DIR
from arg_mine.data.loaders import get_gdelt_df
from arg_mine.api import classify
from arg_mine import utils


_logger = utils.get_logger(__name__, logging.DEBUG)


@click.command()
@click.option(
    "--ndocs",
    default=100,
    type=int,
    help="The number of documents we want to extract from the list",
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
    help="How many articles to iterate through before writing to output file",
)
def main(ndocs, chunk_size, batch_size):
    """
    Download and extract GDELT data to "data/raw/2020-climate-change-narrative"
    """
    # load input data
    topic = "climate change"
    in_csv_datapath = os.path.join(DATA_DIR, "raw", "2020-climate-change-narrative")
    # TODO: change this to read a specific year by parameter
    csv_filepath = os.path.join(in_csv_datapath, "WebNewsEnglishSnippets.2020.csv")

    url_df = get_gdelt_df(csv_filepath)
    total_n_docs = url_df.shape[0]

    # set up output directory
    target_dir = "gdelt-climate-change-docs"
    out_data_path = os.path.join(DATA_DIR, "processed", target_dir)
    os.makedirs(out_data_path, exist_ok=True)

    # check if ndocs is bigger than the size of the source data, and limit
    if not ndocs or ndocs > total_n_docs:
        ndocs = total_n_docs

    batch_size = batch_size or total_n_docs

    url_list = url_df.content_url.values[:ndocs]

    # TODO: better is to wrap the write pattern than repeat it
    if ndocs >= batch_size and total_n_docs > batch_size:
        _logger.info(
            "Running {} BATCHED documents from file: {}, batch size={}".format(
                ndocs, csv_filepath, batch_size
            )
        )

        # we write and append in batches
        for batch_ix, doc_ix in enumerate(
            range(0, url_df[:ndocs].shape[0], batch_size)
        ):
            _logger.debug(
                "Running batch {} [{}-{}]".format(
                    batch_ix, doc_ix, doc_ix + batch_size - 1
                )
            )
            responses = classify.fetch_concurrent(
                topic,
                url_list=url_list[doc_ix : doc_ix + batch_size],
                chunk_size=chunk_size,
            )
            docs_df, sentences_df, missing_docs = classify.process_responses(responses)

            # save outputs to CSV
            filename = "gdelt_2020_{data}_docs{start}-{end}.csv"
            docs_df.to_csv(
                os.path.join(
                    out_data_path,
                    filename.format(
                        data="docs", start=doc_ix, end=doc_ix + batch_size - 1
                    ),
                ),
                header=True,
                index=False,
            )
            sentences_df.to_csv(
                os.path.join(
                    out_data_path,
                    filename.format(
                        data="sentences", start=doc_ix, end=doc_ix + batch_size - 1
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
        # probably want to shuffle the docs here
        responses = classify.fetch_concurrent(
            topic, url_list=url_df.content_url.values[:ndocs], chunk_size=chunk_size
        )
        docs_df, sentences_df, missing_docs = classify.process_responses(responses)

        # save outputs to CSV
        filename = "gdelt_2020_{data}_n{ndocs}.csv"
        docs_df.to_csv(
            os.path.join(out_data_path, filename.format(data="docs", ndocs=ndocs)),
            header=True,
            index=False,
        )
        sentences_df.to_csv(
            os.path.join(out_data_path, filename.format(data="sentences", ndocs=ndocs)),
            header=True,
            index=False,
        )


if __name__ == "__main__":

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
