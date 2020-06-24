# arg_mine

Uses the ArgumentText API to mine arguments from selected data sources. A part of the Great American Debate project https://www.greatamericandebate.org/

You can read the full documentation here:
http://mpesavento.github.io/arg-mine

## env var requirements
We are using the `dotenv` package to maintain separation of required keys and submitted code. The file `.env`
is part of the base repo, but will NOT be committed to the repository. This file must be updated with the
following required secrets, which will be read as environment variables:
```
ARGUMENTEXT_USERID=<your_userid>
ARGUMENTEXT_KEY=<your_key>
AWS_ACCESS_KEY=<your_key>
AWS_SECRET_ACCESS_KEY=<your_key>
```
Each of these should have the corresponding values in the appropriate place

These env vars can be loaded into the environment inside a script or notebook via:
```
load_dotenv(find_dotenv())
```


## Project set up

To set up a virtual environment for development, run:
```
make create-environment
conda activate arg-mine 
make requirements
```
This will create an environment in conda, if conda is installed, or a virtualenv if not. This
will also install all dev requirements into the env.

To build the associated docker image with identical dependencies, run:
```
make build
```

To access the bash terminal in the docker container, run
```
make shell
```

To run a jupyter lab server from a docker container, run
```
make jupyter
```
This will launch the jupyter lab server, with the host repository volume-mapped to the docker container, persisting all changes.

To update the documentation and push the update to http://mpesavento.github.io/arg-mine:
```
make docs
```

### Dependency management
To maintain and update dependencies, we use `pip-compile` on `requirements.in`, resulting in a complete list of all dependencies.
This list keeps the explicit dependencies small, and deals with possible version conflicts rapidly.
To update dependencies, inside the dev environment run:
```
make compile-reqs
```



## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
