import glob
import logging
import os
import pandas as pd

from arg_mine import utils
from arg_mine import DATA_DIR

_logger = utils.get_logger(__name__, logging.DEBUG)

GDELT_COL_NAMES = (
    "datetime",
    "title",
    "headline_image_url",
    "content_url",
    "topic_context",
)


def convert_datetime_int(datetime_int):
    """
    Convert an integer in format `YYYYMMDDHHMMSS` to pd.Timestamp
     eg, `20200107101500` to `2020.01.07T10:15:00`

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
        raise ValueError(
            "Incorrect length for datetime integer, expected 12, found {}".format(
                len(datetime_str)
            )
        )
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
    From CSV path, load a pandas dataframe with the GDELT URL dataset

    Parameters
    ----------
    csv_filepath : str, path
    col_names : List[str]

    Returns
    -------
    pd.DataFrame
    """
    # convert csv to dataframe. should probably do this in a separate step, and just return the path here.
    _logger.info("reading data from: {}".format(csv_filepath))
    df = pd.read_csv(csv_filepath, header=0, names=col_names, index_col=False)
    df["timestamp"] = df.datetime.apply(convert_datetime_int)
    return df


def load_processed_csv(
    filename, project="gdelt-climate-change-docs", drop_nan_cols=None
):
    csv_filepath = os.path.join(DATA_DIR, "processed", project, filename)
    _logger.info("reading data from: {}".format(csv_filepath))
    df = pd.read_csv(csv_filepath)

    if drop_nan_cols:
        if isinstance(drop_nan_cols, str):
            drop_nan_cols = [drop_nan_cols]
        df.dropna(subset=drop_nan_cols, inplace=True)
    return df


def concat_csvs(filename_glob, base_path):
    """
    Given a globbed filename (eg "my_files_doc*.csv"), concatenate the returned
    CSVs into a DataFrame

    Parameters
    ----------
    filename_glob : str
        filename matching the target files, needs to match the requirements from `glob` module
    base_path : str
        where to start looking for the files

    Returns
    -------
    pd.DataFrame
    """
    filepath_list = sorted(glob.glob(os.path.join(base_path, filename_glob)))
    concat_df = pd.concat([pd.read_csv(filename) for filename in filepath_list], axis=0)
    # TODO: make this drop more generic when we have more than one type of processed data
    concat_df.dropna(subset=["sentence_original"], inplace=True)

    return concat_df
