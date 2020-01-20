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

# Install GitLab Runner using the official GitLab repositories
# https://docs.gitlab.com/runner/install/linux-repository.html
# Registering Runners
# https://docs.gitlab.com/runner/register/index.html
# TLS disabled
# https://docs.gitlab.com/ee/ci/docker/using_docker_build.html#tls-disabled
( \
    which gitlab-runner || ( \
        curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | bash \
        && apt-get install gitlab-runner \
    ) \
) \
&& read -p 'Please enter the gitlab-ci coordinator URL (default is https://gitlab.com): ' url \
&& read -p 'Please enter the gitlab-ci description for this runner (default is app_runner): ' description \
&& read -sp 'Please enter the gitlab-ci token for this runner: ' registration_token \
&& gitlab-runner register -n \
    --url ${url:-'https://gitlab.com/'} \
    --registration-token $registration_token \
    --executor docker \
    --description ${description:-app_runner} \
    --docker-image docker:19.03.1 \
    --docker-privileged \
    --docker-volumes "/certs/client" \
    --docker-wait-for-services-timeout 0 \
    --tag-list live
