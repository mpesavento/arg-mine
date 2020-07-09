#ARG ROOT_CONTAINER=ubuntu:bionic-20200403@sha256:b58746c8a89938b8c9f5b77de3b8cf1fe78210c696ab03a1442e235eea65d84f
ARG ROOT_CONTAINER=python:3.8-slim-buster

ARG BASE_CONTAINER=$ROOT_CONTAINER
FROM $BASE_CONTAINER

LABEL maintainer="Mike Pesavento <mike@peztek.com>"
ARG NB_USER="mpesavento"
ARG NB_UID="1000"
ARG NB_GID="100"

USER root

# Add permanent apt-get installs and other root commands here
# e.g., RUN apt-get install npm nodejs

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
  && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    less \
    locales \
    fonts-liberation \
    nodejs \
    npm \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2020.06.05 getting npm incompatability issue between nodejs and npm,
# can update these to more specific versions
RUN apt-get install -yq --no-install-recommends \
    nodejs \
    npm \
  && apt-get clean

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

# Configure environment
ENV SHELL=/bin/bash \
    NB_USER=$NB_USER \
    NB_UID=$NB_UID \
    NB_GID=$NB_GID \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    CONDA_DIR=/opt/conda

# Copy a script that we will use to correct permissions after running certain commands
COPY scripts/fix-permissions /usr/local/bin/fix-permissions
RUN chmod a+rx /usr/local/bin/fix-permissions

# Enable prompt color in the skeleton .bashrc before creating the default NB_USER
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc

# Create NB_USER wtih name jovyan user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su && \
    sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers && \
    sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers && \
    useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    mkdir -p $CONDA_DIR && \
    chown $NB_USER:$NB_GID $CONDA_DIR && \
    chmod g+w /etc/passwd && \
    fix-permissions $HOME && \
    fix-permissions $CONDA_DIR


# ffmpeg for matplotlib anim & dvipng for latex labels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg dvipng


# ========================================================

# change user if we aren't using root
#USER $NB_USER

# Add permanent pip/conda installs, data files, other user libs here
# e.g., RUN pip install jupyter_dashboards

COPY requirements.txt requirements_dev.txt ./
RUN pip install -r requirements_dev.txt

# Copy local files as late as possible to avoid cache busting
# copy our version of the notebook config in
COPY .jupyter /etc/jupyter/

# Fix permissions on /etc/jupyter as root
USER root
RUN fix-permissions /etc/jupyter/

# need to build to be able to use jupyter lab easily
RUN \
    # Activate ipywidgets extension in the environment that runs the notebook server
    jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    # Also activate ipywidgets extension for JupyterLab
    # Check this URL for most recent compatibilities
    # https://github.com/jupyter-widgets/ipywidgets/tree/master/packages/jupyterlab-manager
    jupyter labextension install @jupyter-widgets/jupyterlab-manager@^2.0.0 --no-build && \
    jupyter labextension install @bokeh/jupyter_bokeh@^2.0.0 --no-build && \
    jupyter labextension install jupyter-matplotlib@^0.7.2 --no-build && \
    jupyter lab build -y --dev-build=False --minimize=False && \
    jupyter lab clean -y && \
    npm cache clean --force

# Import matplotlib the first time to build the font cache.
ENV XDG_CACHE_HOME /home/$NB_USER/.cache/
RUN MPLBACKEND=Agg python -c "import matplotlib.pyplot" && \
    fix-permissions /home/$NB_USER

# run the post install script for package management and updating
COPY scripts/python_post_install.sh /root/
RUN sh /root/python_post_install.sh

# # create SSL cert
# RUN mkdir certs
# WORKDIR /root/certs
# RUN openssl req \
#     -x509 \
#     -nodes \
#     -days 365 \
#     -newkey rsa:1024 \
#     -subj "/C=US/ST=CA/L=SanFrancisco/O=Peztek/CN=www.peztek.com" \
#     -keyout notebook.pem \
#     -out notebook.pem \
#     && chmod 600 notebook.pem

# add our volume-mapped code to the python path
ENV PYTHONPATH /opt/workspace
