import os
import requests
import zipfile
import logging

from dotenv import find_dotenv, load_dotenv

from arg_mine import PROJECT_DIR

logger = logging.getLogger(__name__)

# URL taken from https://blog.gdeltproject.org/a-new-contextual-dataset-for-exploring-climate-change-narratives-6-3m-english-news-urls-with-contextual-snippets-2015-2020/  # noqa: E501
BASE_URL_FMT = "http://data.gdeltproject.org/blog/2020-climate-change-narrative/WebNewsEnglishSnippets.{year}.csv.zip"


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
    gdelt_raw_dir = os.path.join(PROJECT_DIR, "data", "raw", gdelt_project_name)
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
