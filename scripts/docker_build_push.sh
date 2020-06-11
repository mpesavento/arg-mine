#!/bin/bash
# Log in to your dockerhub instance, and push the built container to hub.docker.com
# This requires the existence of a user repository named "ds-work" on dockerhub.

PROJECT_NAME="ds-work"
DOCKERHUB_USER="mpesavento"
TAG=""

DOCKER_AUTH_FILE="$HOME/.docker/config.json"

# --------------------
# parse the args
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -u|--username)
    DOCKERHUB_USER="$2"
    shift # past argument
    shift # past value
    ;;
    -t|--tag)
    TAG="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done

# --------------------
# build, tag, and push the docker image(s)

# check if have auth file, if not make one
if [[ ! -f ${DOCKER_AUTH_FILE} ]]
then
    # this will prompt for the user password by default
    echo "Enter the hub.docker.com password for user '${DOCKERHUB_USER}':"
    docker login --username=${DOCKERHUB_USER} || exit
else
    echo "Already authenticated to docker.io"
fi

# if we pass in an explicit tag
if [[ ! -z "$TAG" ]]
then
    EXTRA_TAG=${PROJECT_NAME}:${TAG}
    CMD_EXTRA_TAG="-t ${EXTRA_TAG}"
    echo "Adding extra tag: ${EXTRA_TAG}"
else
    EXTRA_TAG=""
    CMD_EXTRA_TAG=""
fi


# build the container
echo "*****"  docker build -t ${PROJECT_NAME} ${CMD_EXTRA_TAG} .
docker build -t ${PROJECT_NAME} ${CMD_EXTRA_TAG} . || exit

# push latest to hub.docker.com
docker tag ${PROJECT_NAME} ${DOCKERHUB_USER}/${PROJECT_NAME}:latest
docker push ${DOCKERHUB_USER}/${PROJECT_NAME}

# push target tag to docker hub
if [[ ! -z "$TAG" ]]
then
    echo ${TAG}
    docker tag ${PROJECT_NAME} ${DOCKERHUB_USER}/${EXTRA_TAG}
    docker push ${DOCKERHUB_USER}/${EXTRA_TAG}
fi

