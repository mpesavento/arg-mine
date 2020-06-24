#!/usr/bin/env bash
# set up an EC2 instance by stepping through this script

# install docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
rm get-docker.sh

# install other useful utilities
sudo apt-get install -qy make

# create a new local key to pull form github via ssh
#ssh-keygen -t rsa -b 4096 -C "mike@peztek.com"
#chmod 600 ~/.ssh/id_rsa
# add the public key to github

# append to ~/.bashrc
cat <<EOT >> ~/.bashrc
export PATH=/home/ubuntu/.local/bin:$PATH
export WORKON_HOME=/home/ubuntu/.virtualenvs
export PROJECT_HOME=/home/ubuntu/
EOT

# clone the target repository
git clone https://github.com/mpesavento/arg-mine.git

# create the virtual environment
cd ~/arg-mine


make create_environment

# build the docker image
make build