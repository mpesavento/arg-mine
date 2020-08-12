.. _`setup_ec2`:

Setting up EC2 instance
==========================

Below we list out the necessary steps for setting up an EC2 instance
and be able to run a docker container hosting the `arg-mine <https://github.com/mpesavento/arg-mine>`_
repository.

Start up the instance
---------------------
First you will want to start up the instance via the AWS console and the EC2 panel.
Once it is started, authenticate via ssh, and install additional utilities


#. Set up the instance via the AWS console
    `<https://console.aws.amazon.com/ec2/>`_

    The minimum instance type is ``t2.medium``, with 2 cores and 4 GB ram. The preferred
    and tested instance size is ``t2.large``, with 2 cores and 8 GB ram.

    If you do not have a PEM file for secure access to the instance, create one and save it locally,
    Eg, save as ``~/.ssh/gad_ec2_key.pem``

#. Log in to the instance via ssh
    Eg::

        ssh -i ~/.ssh/my_pem_key.pem

#. Install docker
    Download and install docker. Set the current user to have permission to access the docker daemon::

        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        sudo usermod -aG docker ubuntu

    You will need to log out and log back in to get access to the docker daemon. If you do not,
    when you run a ``docker`` command you
    may see a message like ``ERRO[0000] failed to dial gRPC: cannot connect to the Docker
    daemon. Is 'docker daemon' running on this host?: dial unix /var/run/docker.sock:
    connect: permission denied``. If this is the case, logout and log back in to the server.

#. Install other base server requirements::

    sudo apt-get install -yq make python3-pip
    python3 -m pip install -q virtualenv virtualenvwrapper


Set up the repository and code environment
------------------------------------------

#. Clone repository from github
    If using https::

        git clone https://github.com/mpesavento/arg-mine.git

    If using ssh, create ssh public key in github. This ssh key will only exist
    for the instance you create::

        ssh-keygen -t rsa -b 4096 -C "your_github_email@example.com"
        chmod 400 ~/.ssh/id_rsa
        cat ~/.ssh/id_rsa.pub
        # copy and add ssh key to your github account
        git clone git@github.com:mpesavento/arg-mine.git

#. Add variables to the env. Copy and paste this block, and run::

    cat << 'EOF' >> ~/.bashrc
    export PATH=/home/ubuntu/.local/bin:$PATH
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=/home/ubuntu/.virtualenvs
    export PROJECT_HOME=/home/ubuntu/
    source ~/.local/bin/virtualenvwrapper.sh
    EOF
    source ~/.bashrc

#. Create and activate the virtual environment::

    cd ~/arg-mine
    make create_environment
    workon arg_mine

#. Install the dev requirements in the host environment (eg virtualenv)::

    make requirements
    pip3 install -e .

Set up the docker image and commands
---------------------------------

#. Build the docker image
    Run::

        make build

    This build may take a while on small machines, especially with compiling ``jupyter lab``
#. Run your target commands.
    This can be hosting a notebook server (open up the appropriate port 8888 on the
    security permissions), or running dockerized commands.
    Eg::

        make jupyter


Next
^^^^
That's it! you have a working EC2 instance!
From here, you can make a docker image to speed up development of future application servers.

In our next section, we will go over how to download the raw data.
:ref:`download_data`