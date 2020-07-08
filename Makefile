

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = arg-mine-gdelt-data
PROFILE = default
PROJECT_NAME = arg_mine
PYTHON_INTERPRETER = python3
DOCKER_WORKSPACE = /opt/workspace

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################



## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8
lint:
	flake8 arg_mine



## Upload Data to S3
# ignore any hidden files starting with "."
sync_data_to_s3:
ifeq (default, $(PROFILE))
	aws s3 sync data/ s3://${BUCKET}/data/ \
		--exclude "*/.DS_Store" --exclude "*/.gitignore" --exclude "*/.gitkeep"
else
	aws s3 sync data/ s3://${BUCKET}/data/
endif

## Download Data from S3
sync_data_from_s3:
ifeq (default, $(PROFILE))
	aws s3 sync s3://$(BUCKET)/data/ data/
else
	aws s3 sync s3://$(BUCKET)/data/ data/ --profile $(PROFILE)
endif

## Set up python interpreter environment
create_environment:
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, creating conda environment."
ifeq (3,$(findstring 3,$(PYTHON_INTERPRETER)))
	conda create --name $(PROJECT_NAME) python=3
else
	conda create --name $(PROJECT_NAME) python=2.7
endif
@echo ">>> New conda env created. Activate with:\nsource activate $(PROJECT_NAME)"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv virtualenvwrapper
	@echo ">>> Installing virtualenvwrapper if not already installed.\nMake sure the following lines are in shell startup file\n\
	export WORKON_HOME=$$HOME/.virtualenvs\nexport PROJECT_HOME=$$HOME/\nsource $$HOME/.local/bin/virtualenvwrapper.sh\n"
	@bash -c "source `which virtualenvwrapper.sh`;mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
endif

## Test python environment is setup correctly
test_environment:
	$(PYTHON_INTERPRETER) tests/test_environment.py

## Install Python Dependencies
requirements: test_environment
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements_dev.txt

compile-reqs:
	pip-compile requirements.in && \
	pip-compile requirements_dev.in

sync-reqs:
	pip-sync requirements_dev.txt

docs:
	./scripts/build_upload_docs.sh

.PHONY: clean data lint \
	requirements \
	create_environment \
	compile-reqs \
	sync-reqs \
	docs \
	sync_data_from_s3 \
	sync_data_to_s3

#################################################################################
# DOCKER RULES                                                                 #
#################################################################################

# default is to map the current directory into the workspace
DOCKER_RUN_OPTS = \
	-v ${PWD}:${DOCKER_WORKSPACE} \
	-w ${DOCKER_WORKSPACE}

build:
	docker build -t $(PROJECT_NAME) .

shell:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} /bin/bash

jupyter:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		-p 8888:8888 \
		${PROJECT_NAME} scripts/run_jupyter.sh

## testing inside docker instance
test:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} scripts/run_tests.sh

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Make Dataset
data:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} \
		$(PYTHON_INTERPRETER) arg_mine/data/make_dataset.py data/raw data/processed


get-gdelt:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} \
		$(PYTHON_INTERPRETER) arg_mine/data/download_gdelt_climate_en.py

extract-gdelt:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} \
		$(PYTHON_INTERPRETER) arg_mine/data/extract_gdelt_sentences.py --ndocs=1000

test-extract-gdelt:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} \
		$(PYTHON_INTERPRETER) arg_mine/data/extract_gdelt_sentences.py --ndocs=42

batch-extract-gdelt:
	docker run --rm -it \
		${DOCKER_RUN_OPTS} \
		${PROJECT_NAME} \
		$(PYTHON_INTERPRETER) arg_mine/data/extract_gdelt_sentences.py --ndocs=10000 --batch-size=1000



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
