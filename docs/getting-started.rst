.. _getting-started:

Getting Started
===============

Uses the ArgumentText API to mine arguments from selected data sources.
A part of the Great American Debate project https://www.greatamericandebate.org/

You can read the full documentation here:
http://mpesavento.github.io/arg-mine


Environment Variables
---------------------
We are using the ``dotenv`` package to maintain separation of required keys and submitted code. The file `.env.example`
is part of the base repo. To use this file, make a copy named ``.env`` at the project root, and edit the
file with following required secrets. These will then be available as environment variables:
::

    ARGUMENTEXT_USERID=<your_userid>
    ARGUMENTEXT_KEY=<your_key>
    AWS_ACCESS_KEY=<your_key>
    AWS_SECRET_ACCESS_KEY=<your_key>

Each of these should have the corresponding values in the appropriate place.

* Enter in your unique AWS access keys, obtained from your personal account or from your AWS account administrator.
* Obtain your ArgumentText keys by filling out the registration form `here <https://api.argumentsearch.com/en/api_registration>`_

These env vars can be loaded into the environment inside a script or notebook via::

    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

and accessed via (for example)::

    import os
    user_id = os.getenv("ARGUMENTEXT_USERID")

Project set up
--------------
To set up a virtual environment for development (assuming you have conda installed, run::

    make create-environment
    conda activate arg-mine
    make requirements

This will create an environment in conda, if conda is installed, or a virtualenv if not. This
will also install all dev requirements into the env.

A full server set up from scratch can be found in the documentation at
:doc:`Setup EC2 <../setup_ec2>`.


Setting up AWS credentials
--------------------------
To set up the AWS command line interface (``awscli``) with your credentials, first make sure
the AWS CLI has been installed. Currently, we recommend installing version 2:
https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html
Follow these instructions for installation for your target operating system.

Once installed, you need to add your secrets to the CLI. In a terminal, run::

    aws configure

This will prompt you for your:

* AWS access key
* AWS secret key
* AWS region (currently ``us-east-2``)
* output format (default is json, recommended)

``make`` commands
-----------------
All of the make commands require that you are already using the project development environment,
either via ``conda`` or ``virtualenv``.

To build a docker image with all dependencies, run::

    make build

Running this command requires ``docker`` to be installed. See the
`OS-dependent installation instructions <https://docs.docker.com/get-docker/>`_ here
for more info on how to do this.

This ``build`` command may take a while, as it needs to download all dependencies and
compile the jupyter lab server.

To access the bash terminal in the docker container, run::

    make shell

To run a jupyter lab server from a docker container, run::

    make jupyter

This will launch the jupyter lab server, with the host repository volume-mapped to the docker container, persisting all changes.

To update the documentation and push the update to http://mpesavento.github.io/arg-mine::

    make docs-upload

Note that this will overwrite any previous documentation and publish the new content live.

**TODO**
Make a command to view documentation locally without publishing it


Dependency management
---------------------
To maintain and update dependencies, we use ``pip-compile`` on ``requirements.in``,
resulting in a complete list of all dependencies.
This list keeps the explicit dependencies small, and deals with possible version
conflicts rapidly.

To update dependencies, inside the dev environment (``arg-mine`` in conda or virtualenv) run::

    make compile-reqs

This will compile the ``requirements.in`` and create a fully updated static ``requirements.txt``,
with a complete list of available packages and package versions that are known to work.