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
    help="The number of documents we want to extract from the list",
)
@click.option(
    "--chunk-size",
    default=100,
    help="how many articles to process in each iteration"
)
def main(ndocs, chunk_size):
    """
    Download and extract GDELT data to "data/raw/2020-climate-change-narrative"
    """
    # load input data
    topic = "climate change"
    in_csv_datapath = os.path.join(DATA_DIR, "raw", "2020-climate-change-narrative")
    csv_filepath = os.path.join(in_csv_datapath, "WebNewsEnglishSnippets.2020.csv")

    url_df = get_gdelt_df(csv_filepath)
    url_df.head()

    # set up output directory
    target_dir = "gdelt-climate-change-docs"
    out_data_path = os.path.join(DATA_DIR, "processed", target_dir)
    os.makedirs(out_data_path, exist_ok=True)

    # probably want to shuffle the docs here
    responses = classify.fetch_concurrent(
        topic, url_list=url_df.content_url.values[:ndocs], chunk_size=chunk_size
    )
    docs_df, sentences_df = classify.process_responses(responses)

    # save outputs to CSV
    docs_df.to_csv(
        os.path.join(out_data_path, "gdelt_2020_docs.csv"), header=True, index=False,
    )
    sentences_df.to_csv(
        os.path.join(out_data_path, "gdelt_2020_sentences.csv"),
        header=True,
        index=False,
    )


if __name__ == "__main__":

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
