import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve


def make_confusion_matrix(
    cf,
    group_names=None,
    categories="auto",
    count=True,
    percent=True,
    cbar=True,
    xyticks=True,
    xyplotlabels=True,
    sum_stats=True,
    figsize=None,
    cmap="Blues",
    title=None,
):
    """
    This function will make a pretty plot of an sklearn Confusion Matrix cm using a Seaborn heatmap visualization.

    Method borrowed from https://github.com/DTrimarchi10/confusion_matrix/blob/master/cf_matrix.py

    Arguments
    ---------
    cf:            confusion matrix to be passed in

    group_names:   List of strings that represent the labels row by row to be shown in each square.

    categories:    List of strings containing the categories to be displayed on the x,y axis. Default is 'auto'

    count:         If True, show the raw number in the confusion matrix. Default is True.

    percent:     If True, show the proportions for each category. Default is True.

    cbar:          If True, show the color bar. The cbar values are based off the values in the confusion matrix.
                   Default is True.

    xyticks:       If True, show x and y ticks. Default is True.

    xyplotlabels:  If True, show 'True Label' and 'Predicted Label' on the figure. Default is True.

    sum_stats:     If True, display summary statistics below the figure. Default is True.

    figsize:       Tuple representing the figure size. Default will be the matplotlib rcParams value.

    cmap:          Colormap of the values displayed from matplotlib.pyplot.cm. Default is 'Blues'
                   See http://matplotlib.org/examples/color/colormaps_reference.html

    title:         Title for the heatmap. Default is None.

    Returns
    -------
    handle to current figure
    """

    # CODE TO GENERATE TEXT INSIDE EACH SQUARE
    blanks = ["" for i in range(cf.size)]

    if group_names and len(group_names) == cf.size:
        group_labels = ["{}\n".format(value) for value in group_names]
    else:
        group_labels = blanks

    if count:
        group_counts = ["{0:0.0f}\n".format(value) for value in cf.flatten()]
    else:
        group_counts = blanks

    if percent:
        group_percentages = [
            "{0:.2%}".format(value) for value in cf.flatten() / np.sum(cf)
        ]
    else:
        group_percentages = blanks

    box_labels = [
        f"{v1}{v2}{v3}".strip()
        for v1, v2, v3 in zip(group_labels, group_counts, group_percentages)
    ]
    box_labels = np.asarray(box_labels).reshape(cf.shape[0], cf.shape[1])

    # CODE TO GENERATE SUMMARY STATISTICS & TEXT FOR SUMMARY STATS
    if sum_stats:
        # Accuracy is sum of diagonal divided by total observations
        accuracy = np.trace(cf) / float(np.sum(cf))

        # if it is a binary confusion matrix, show some more stats
        if len(cf) == 2:
            # Metrics for Binary Confusion Matrices
            precision = cf[1, 1] / sum(cf[:, 1])
            recall = cf[1, 1] / sum(cf[1, :])
            f1_score = 2 * precision * recall / (precision + recall)
            stats_text = "\n\nAccuracy={:0.3f}\nPrecision={:0.3f}\nRecall={:0.3f}\nF1 Score={:0.3f}".format(
                accuracy, precision, recall, f1_score
            )
        else:
            stats_text = "\n\nAccuracy={:0.3f}".format(accuracy)
    else:
        stats_text = ""

    # SET FIGURE PARAMETERS ACCORDING TO OTHER ARGUMENTS
    # Get default figure size if not set
    figsize = figsize or plt.rcParams.get("figure.figsize")

    if not xyticks:
        # Do not show categories if xyticks is False
        categories = False

    # MAKE THE HEATMAP VISUALIZATION
    plt.figure(figsize=figsize)
    sns.heatmap(
        cf,
        annot=box_labels,
        fmt="",
        cmap=cmap,
        cbar=cbar,
        xticklabels=categories,
        yticklabels=categories,
    )

    if xyplotlabels:
        plt.ylabel("True label")
        plt.xlabel("Predicted label" + stats_text)
    else:
        plt.xlabel(stats_text)

    if title:
        plt.title(title)

    return plt.gcf()


def make_roc_curve(y_label, y_score, selected_thresh=0.5, ax=None):
    """
    Create plot for the Receiver Operating Characteristic (ROC) curve
    Highlights the selected threshold on the curve
    Only works for binary classification

    Parameters
    ----------
    y_label: np.array
        ground truth labels
    y_score: np.array
        1D array with the confidence scores from the model predictions
    selected_thresh: float
        what threshold you want to highlight
    ax: AxesSubplot
        optional, plots on given axis, or creates new figure otherwise

    Returns
    -------
    AxesSubplot
    """
    fpr, tpr, thresholds = roc_curve(y_label, y_score)
    roc_auc = auc(fpr, tpr)
    thresh_ix = np.argmin(np.abs(thresholds - selected_thresh))
    thresh_fpr = fpr[thresh_ix]
    thresh_tpr = tpr[thresh_ix]
    if not ax:
        fig, ax = plt.subplots(figsize=(6, 6))
    lw = 2
    ax.plot([0, 1], [0, 1], color="gray", lw=lw, linestyle="--")
    ax.plot(fpr, tpr, lw=lw, label="ROC curve (AUC = {:0.2f})".format(roc_auc))
    ax.plot(
        thresh_fpr,
        thresh_tpr,
        "ro",
        alpha=0.5,
        label="threshold ({}): FPR={:0.3f}, TPR={:0.3f}".format(
            selected_thresh, thresh_fpr, thresh_tpr
        ),
    )
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC curve")
    plt.legend(loc="lower right")
    ax.set_aspect("equal", "box")
    return ax


def make_precision_recall_curve(y_label, y_score, selected_thresh=0.5, ax=None):
    precision, recall, thresholds = precision_recall_curve(y_label, y_score)
    thresh_ix = np.argmin(np.abs(thresholds - selected_thresh))
    thresh_recall = recall[thresh_ix]
    thresh_precision = precision[thresh_ix]
    if not ax:
        fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(recall, precision, label="precision-recall curve")
    ax.plot(
        thresh_recall,
        thresh_precision,
        "ro",
        label="threshold ({}): precision={:0.3f}, recall={:0.3f}".format(
            selected_thresh, thresh_precision, thresh_recall
        ),
    )
    plt.legend(loc="lower left")
    ax.set_xlim((0, 1.0))
    ax.set_ylim((0, 1.05))
    ax.set_aspect("equal", "box")
    ax.set_xlabel("recall")
    ax.set_ylabel("precision")
    ax.set_title("Precision-recall")

    return ax
