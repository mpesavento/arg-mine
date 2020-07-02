import logging
import pandas as pd

log_fmt = "%(levelname)s:%(asctime)s:%(name)s: %(message)s"
# logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

GDELT_COL_NAMES = (
    "datetime",
    "title",
    "headline_image_url",
    "content_url",
    "labeled_argument",
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
    logger.info("reading data from: {}".format(csv_filepath))
    df = pd.read_csv(csv_filepath, header=0, names=col_names, index_col=False)
    df["timestamp"] = df.datetime.apply(convert_datetime_int)
    return df
