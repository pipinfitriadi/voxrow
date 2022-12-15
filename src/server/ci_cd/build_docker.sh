#!/bin/bash

# Copyright 2020 Pipin Fitriadi <pipinfitriadi@gmail.com>

# Licensed under the Microsoft Reference Source License (MS-RSL)

# This license governs use of the accompanying software. If you use the
# software, you accept this license. If you do not accept the license, do not
# use the software.

# 1. Definitions

# The terms "reproduce," "reproduction" and "distribution" have the same
# meaning here as under U.S. copyright law.

# "You" means the licensee of the software.

# "Your company" means the company you worked for when you downloaded the
# software.

# "Reference use" means use of the software within your company as a reference,
# in read only form, for the sole purposes of debugging your products,
# maintaining your products, or enhancing the interoperability of your
# products with the software, and specifically excludes the right to
# distribute the software outside of your company.

# "Licensed patents" means any Licensor patent claims which read directly on
# the software as distributed by the Licensor under this license.

# 2. Grant of Rights

# (A) Copyright Grant- Subject to the terms of this license, the Licensor
# grants you a non-transferable, non-exclusive, worldwide, royalty-free
# copyright license to reproduce the software for reference use.

# (B) Patent Grant- Subject to the terms of this license, the Licensor grants
# you a non-transferable, non-exclusive, worldwide, royalty-free patent
# license under licensed patents for reference use.

# 3. Limitations

# (A) No Trademark License- This license does not grant you any rights to use
# the Licensor's name, logo, or trademarks.

# (B) If you begin patent litigation against the Licensor over patents that
# you think may apply to the software (including a cross-claim or counterclaim
# in a lawsuit), your license to the software ends automatically.

# (C) The software is licensed "as-is." You bear the risk of using it. The
# Licensor gives no express warranties, guarantees or conditions. You may have
# additional consumer rights under your local laws which this license cannot
# change. To the extent permitted under your local laws, the Licensor excludes
# the implied warranties of merchantability, fitness for a particular purpose
# and non-infringement.

# Better way for multiline ssh command
# https://forum.gitlab.com/t/better-way-for-multiline-ssh-command/23420
set -e
filename='src/server/docker-compose/Dockerfile'

# How do I find the most recent git commit that modified a file?
# https://stackoverflow.com/questions/4784575/how-do-i-find-the-most-recent-git-commit-that-modified-a-file
last_commit_hash=$(git log -n 1 --pretty=format:%H)
file_last_commit_hash=$(git log -n 1 --pretty=format:%H -- $filename)

if [ $last_commit_hash == $file_last_commit_hash ]; then
    # Docker Registry login and docker CI template
    # https://gitlab.com/gitlab-org/gitlab-runner/issues/2861
    echo "======== Login docker ========"
    echo $CI_REGISTRY_PASSWORD \
        | docker login \
            -u $CI_REGISTRY_USER \
            $CI_REGISTRY \
            --password-stdin

    echo "======== Get latest docker image ========"
    COMPOSE_FILE='src/server/docker-compose/build_and_test.yml'
    docker-compose \
        -f $COMPOSE_FILE \
        pull docker_image \
        || true
    echo "======== Build docker image ========"
    docker-compose \
        -f $COMPOSE_FILE \
        build docker_image
    echo "======== Push docker image ========"
    docker-compose \
        -f $COMPOSE_FILE \
        push docker_image 
fi
