Setting up EC2 instance
==========================

Below we list out the necessary steps for setting up an EC2 instance
and be able to run a docker container hosting the `arg-mine <https://github.com/mpesavento/arg-mine>`_
repository.


#. Set up the instance via the AWS console
   `<https://console.aws.amazon.com/ec2/>`_
   If you do not have a PEM file for secure access to the instance, create one and save it locally

#. Install docker::

    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh

#. Install other useful utilities::

    sudo apt-get install -yq make python3-pip

#. Create local ssh key for github, add it to your github account::

    ssh-keygen -t rsa -b 4096 -C "your_github_email@example.com"
    chmod 400 ~/.ssh/id_rsa.pem

#. Clone repository from github
If using ssh (requires key)::

    git clone git@github.com:mpesavento/arg-mine.git

If using https::

    git clone https://github.com/mpesavento/arg-mine.git

#. Create the virtual environment::

    cd ~/arg-mine
    make create_environment

#. Build the docker image::

    make build

#. Run your target commands. This can be hosting a notebook server
(open up the appropriate port 8888 on the security permissions), or running dockerized
commands