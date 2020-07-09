"""
Tools for adding ground truth labels to datasets
"""
import logging
import pandas as pd  # noqa: F401, datatype
from nltk import tokenize

from arg_mine import utils

_logger = utils.get_logger(__name__, logging.DEBUG)

# keywords used for context identification in GDELT dataset
GDELT_KEYWORDS = [
    "climate change",
    "global warming",
    "climate crisis",
    "greenhouse gas",
    "greenhouse gases",
    "carbon tax",
]


def match_doc_id(url, docs_df):
    """
    Return the first matching row with the target URL

    Parameters
    ----------
    url : str
    docs_df : pd.DataFrame

    Returns
    -------
    str
    """
    return docs_df[url == docs_df["url"]]["doc_id"].iloc[0]


def get_doc_sentences(doc_id, sentences_df):
    """
    Given a unique document ID, return all sentences from that document

    Parameters
    ----------
    doc_id : str
    sentences_df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    return sentences_df[sentences_df.doc_id == doc_id]


def label_doc_sentences_with_context(url_row, docs_df, sentences_df):
    """
    Ugly way to label which sentences are used in context of the GDELT keywords

    CAVEATS:
    - Context snippit is ~100 characters before and after the keyword, incl whole word.
        This means that the context may have a single word as one of the tokens,
        which may give false positives.
        THIS IS BAD to use for ground truth data.
    - this is modifying the sentences_df in place!!


    Parameters
    ----------
    url_row : pd.Series
    docs_df : pd.DataFrame
    sentences_df : pd.DataFrame

    Returns
    -------

    """
    content_url = url_row["content_url"]
    snippit = url_row["topic_context"]
    doc_id = match_doc_id(content_url, docs_df)
    doc_sentences = get_doc_sentences(doc_id, sentences_df)

    # sanitize, removing odd punctuation
    # TODO: sanitizing is getting more and more complicated!
    snippit = snippit.replace("[", "").replace("]", "")
    snippit = snippit.replace("(", "").replace(")", "")
    snippit = snippit.replace("/", "").replace("\\", "")
    snippit = snippit.replace("+", "")
    snippit = snippit.replace("*", "").strip()

    # tokenize the GT context into sentences
    arg_tokens = tokenize.sent_tokenize(snippit)

    for token in arg_tokens:
        if len(token) < 2:
            continue
        try:
            matches = doc_sentences[
                doc_sentences.sentence_original.str.contains(token)
            ]["sentence_id"]
        except Exception as e:
            _logger.info("**** errant token: '{}'".format(token))
            _logger.info("ALL TOKENS: {}".format(arg_tokens))
            _logger.info("{} : {}".format(utils.unique_hash(content_url), content_url))
            raise e

        if matches.empty:
            # _logger.debug("No matches found for token in doc {}, {}: '{}'".format(doc_id, content_url, token))
            continue
        # only look at the first match
        sentences_df.loc[
            sentences_df["sentence_id"] == matches.values[0], "has_labeled_arg"
        ] = True
    return sentences_df


def label_gdelt_context(url_df, docs_df, sentences_df, label_col_name="has_context"):
    """
    Add column `label_col_name` to sentences_df, with whether or not the sentence
    was part of the context label from GDELT

    Parameters
    ----------
    url_df
    docs_df
    sentences_df
    label_col_name

    Returns
    -------

    """
    # preload label column if doesnt exist
    if label_col_name not in sentences_df.columns:
        sentences_df[label_col_name] = False

    # filter the url_df to just the entries in the docs
    url_df_crop = url_df[url_df["content_url"].isin(docs_df.url.values)]

    for row_ix, url_row in url_df_crop.iterrows():
        if url_row.notna()["topic_context"]:
            # does modification of sentences_df in place
            label_doc_sentences_with_context(url_row, docs_df, sentences_df)

    return sentences_df
