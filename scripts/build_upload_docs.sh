#!/usr/bin/env bash
#!/bin/bash
#
# THIS IS FOR ROBOTS ONLY, HUMANS KEEP OUT, NO TRESPASSING
# This script enables circle to push to github pages. If you
# execute it, your GLOBAL github config will be overwritten. We
# strongly recommend staying away from this.
#
# For more info, see: https://gist.github.com/francesco-romano/351a6ae457860c14ee7e907f2b0fc1a5

# throw non-zero exit code if anything fails
set -e

DEST=$(mktemp -d)
TARGET_BRANCH="gh-pages"  # for use in the public-facing Github pages
#TARGET_BRANCH="doc-pages"  # for use in private pages
REPOSITORY_NAME="arg-mine"

git clone -b ${TARGET_BRANCH} --depth 1 git@github.com:mpesavento/${REPOSITORY_NAME}.git "$DEST"

# Skip Host verification for git
#mkdir ~/.ssh/
echo -e "Host github.com\n\tStrictHostKeyChecking no\n" > ~/.ssh/config

# Need to create a .nojekyll file to allow filenames starting with an underscore
# to be seen on the gh-pages site. Therefore creating an empty .nojekyll file.
touch .nojekyll

# build the docs
cd ./docs && make html && cd ../

# get the package version number
PACKAGE_VER=`python version.py`

if [[ -d "docs/build/html" ]] && [[ -f "docs/build/html/index.html" ]]; then
    echo 'Uploading documentation to the gh-pages branch...'

    # first, copy all files from the html dir into the temporary repo
    cp -R ./docs/build/html/* "$DEST"
    cd "$DEST"
    touch .nojekyll

    git config user.email "mike@peztek.com"
    git config user.name "DocGen"

    git add -A
#    git commit -F - <<EOM
#    build $CIRCLE_BUILD_NUM
#    $CIRCLE_BUILD_URL
#    EOM
    git commit -m "Deploy code docs for release: $PACKAGE_VER"
    git push origin gh-pages
else
    echo '' >&2
    echo 'Warning: No documentation (html) files have been found!' >&2
    echo 'Warning: Not going to push the documentation to GitHub!' >&2
    exit 1
fi
