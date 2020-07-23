import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc


def summary_stats(y_label, y_pred, y_score, name="model stats"):
    """
    Aggregate the summary stats for a binary classification problem

    Parameters
    ----------
    y_label : np.array
        array of true labels per sample (eg 0/1)
    y_pred : np.array
        array of predicted labels per sample (eg 0/1)
        Note that this may change depending on the target threshold value from the score
    y_score : np.array
        array of prediction probability, or confidence, per sample
    name : str, optional
        name for these summary stats, saved as index in output

    Returns
    -------
    pd.DataFrame
        single row dataframe
    """
    cf = confusion_matrix(y_label, y_pred)

    stats = dict()
    # Accuracy is sum of diagonal divided by total observations
    stats["accuracy"] = np.trace(cf) / float(np.sum(cf))

    # if it is a binary confusion matrix, show some more stats
    # Metrics for Binary Confusion Matrices
    precision = cf[1, 1] / sum(cf[:, 1])
    recall = cf[1, 1] / sum(cf[1, :])
    f1_score = 2 * precision * recall / (precision + recall)
    stats["precision"] = precision
    stats["recall"] = recall
    stats["f1_score"] = f1_score

    fpr, tpr, thresholds = roc_curve(y_label, y_score)
    stats["roc_auc"] = auc(fpr, tpr)

    return pd.DataFrame(stats, index=[name])
