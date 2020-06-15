import os
from pathlib import Path
import requests
import zipfile
import logging

from dotenv import find_dotenv, load_dotenv
import pandas as pd

from arg_mine import ROOT_DIR

logger = logging.getLogger(__name__)

# URL taken from https://blog.gdeltproject.org/a-new-contextual-dataset-for-exploring-climate-change-narratives-6-3m-english-news-urls-with-contextual-snippets-2015-2020/
BASE_URL_FMT = "http://data.gdeltproject.org/blog/2020-climate-change-narrative/WebNewsEnglishSnippets.{year}.csv.zip"

GDELT_COL_NAMES = [
    "datetime",
    "title",
    "headline_image_url",
    "content_url",
    "snippit"  # contextual snippits
]


def download_file_from_url(url, target_file_path):
    """
    Download a file from the given url

    Parameters
    ----------
    url : str
        target URL to download file from
    target_file_path : str
        path to download the file to

    Returns
    -------
    None
    """
    logger.info("downloading file from {}".format(url))
    response = requests.get(url, allow_redirects=True)
    response.raise_for_status()
    with open(target_file_path, 'wb') as f:
        f.write(response.content)
    return


def download_gdelt_year(year, base_url_fmt=BASE_URL_FMT):
    """
    Download the CSV files from the gdelt project, for a given year

    Parameters
    ----------
    year : int
        numeric year to insert into base_url_fmt
    base_url_fmt : str
        the target URL to download from, formatted string with field `{year}`

    Returns
    -------
    path to the extracted CSV file
    """
    full_url = base_url_fmt.format(year=year)
    uri_path, zip_filename = os.path.split(full_url.split("://")[1])
    gdelt_project_name = os.path.basename(uri_path)
    gdelt_raw_dir = os.path.join(ROOT_DIR, "data", "raw", gdelt_project_name)
    os.makedirs(gdelt_raw_dir, exist_ok=True)

    zip_filepath = os.path.join(gdelt_raw_dir, zip_filename)
    csv_filename, ext = os.path.splitext(zip_filename)
    if ext != ".zip":
        raise IOError("Expected to find a zip file, found '{}' instead".format(ext))
    csv_filepath = os.path.join(gdelt_raw_dir, csv_filename)

    if not os.path.isfile(csv_filepath):
        download_file_from_url(full_url, zip_filepath)
        with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
            zip_ref.extractall(gdelt_raw_dir)
        # delete the zip file when we are done with it
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
        else:
            logger.info("Unable to find the zip file we just extracted from: {}".format(zip_filepath))
    else:
        logger.info("Using cached data for '{}': {}".format(year, csv_filepath))

    return csv_filepath


def convert_datetime_int(datetime_int):
    """
    Convert an integer like `20200107101500` to a pd.Timestamp `2020.01.07T10:15:00`

    Parameters
    ----------
    datetime_int : int
        long integer with date and time, 14 char long

    Returns
    -------
    pd.Timestamp

    Raises
    ------
    ValueError : when int is not 14 char long
    """
    # NOTE we still need to confirm that these times are all GMT
    datetime_str = str(datetime_int)
    if len(datetime_str) != 14:
        raise ValueError("Incorrect length for datetime integer, expected 12, found {}". format(len(datetime_str)))
    ts = pd.Timestamp(
        year=int(datetime_str[:4]),
        month=int(datetime_str[4:6]),
        day=int(datetime_str[6:8]),
        hour=int(datetime_str[8:10]),
        minute=int(datetime_str[10:12]),
        second=int(datetime_str[12:14]),
    )
    return ts


def get_gdelt_df(csv_filepath, col_names=GDELT_COL_NAMES):
    """
    From CSV path, load a pandas dataframe with the target data

    Parameters
    ----------
    csv_filepath : str, path
    col_names : List[str]

    Returns
    -------
    pd.DataFrame
    """
    # convert csv to dataframe. should probably do this in a separate step, and just return the path here.
    logger.info("reading data from: {}".format(csv_filepath))
    df = pd.read_csv(csv_filepath, header=0, names=col_names, index_col=False)
    df['timestamp'] = df.datetime.apply(convert_datetime_int)
    return df


def main():
    """
    Download and extract GDELT data to "data/raw/2020-climate-change-narrative"
    """
    logger.info('making final data set from raw data')

    years = list(range(2015, 2021))
    # download article URL datasets from all given years
    data_paths = {}
    for year in years:
        csv_path = download_gdelt_year(year)
        data_paths[str(year)] = csv_path


if __name__ == '__main__':
    log_fmt = '%(levelname)s:%(asctime)s:%(name)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
