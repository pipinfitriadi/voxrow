#!/usr/bin/env python3

# Copyright 2022 Pipin Fitriadi <pipinfitriadi@gmail.com>

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

import os

from airflow.kubernetes.secret import Secret
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator
)
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount
from kubernetes.client.models import V1KeyToPath


class VoxrowOperator:
    '''
    >>> import os
    >>> from voxrow.airflow import VoxrowOperator
    >>> SECRET = 'put-k8s-secret-name-here'  # For KubernetesPodOperator
    >>> task_name = VoxrowOperator(
    ...     env={
    ...         SECRET: [
    ...             'DB_DRIVER',
    ...             'DB_HOST'
    ...         ]
    ...     },
    ...     mounts_volumes=[{
    ...         'secret_name': SECRET,
    ...         'items': [
    ...             {
    ...                 'key': 'creds.json',
    ...                 'path': 'creds.json',
    ...                 'read_only': True
    ...             }
    ...         ]
    ...         'mount_path': '/tmp/',
    ...         # For DockerOperator, use case:
    ...         # https://gitlab.com/pipinfitriadi/airflow-local.git
    ...         'source_path': os.path.join(
    ...             os.getenv('APP_DIR', ''),
    ...             '../..'
    ...         ),
    ...     }],
    ...     # For DockerOperator, use case:
    ...     # https://gitlab.com/pipinfitriadi/airflow-local.git
    ...     use_kubernetes=Variable.get('use_kubernetes', 'true', True),
    ...     image='alpine',
    ...     task_id='tes',
    ...     entrypoint=['ls'],
    ...     command=['-lah', '/tmp/']
    ...     # For KubernetesPodOperator
    ...     namespace='put-k8s-airflow-namespace-here',
    ...     image_pull_secrets='put-k8s-registry-secrets-here-only-if-needed',
    ... )
    >>>
    '''

    DOCKER_TEMPLATE_FIELDS: set = {
        'image',
        'api_version',
        'command',
        'container_name',
        'cpus',
        'docker_url',
        'environment',
        'private_environment',
        'env_file',
        'force_pull',
        'mem_limit',
        'host_tmp_dir',
        'network_mode',
        'tls_ca_cert',
        'tls_client_cert',
        'tls_client_key',
        'tls_hostname',
        'tls_ssl_version',
        'mount_tmp_dir',
        'tmp_dir',
        'user',
        'mounts',
        'entrypoint',
        'working_dir',
        'xcom_all',
        'docker_conn_id',
        'dns',
        'dns_search',
        'auto_remove',
        'shm_size',
        'tty',
        'hostname',
        'privileged',
        'cap_add',
        'extra_hosts',
        'retrieve_output',
        'retrieve_output_path',
        'timeout',
        'device_requests',
        'log_opts_max_size',
        'log_opts_max_file',
        'ipc_mode'
    }

    K8S_TEMPLATE_FIELDS: set = {
        'kubernetes_conn_id',
        'namespace',
        'image',
        'name',
        'random_name_suffix',
        'cmds',
        'arguments',
        'ports',
        'volume_mounts',
        'volumes',
        'env_vars',
        'env_from',
        'secrets',
        'in_cluster',
        'cluster_context',
        'labels',
        'reattach_on_restart',
        'startup_timeout_seconds',
        'get_logs',
        'image_pull_policy',
        'annotations',
        'container_resources',
        'affinity',
        'config_file',
        'node_selector',
        'image_pull_secrets',
        'service_account_name',
        'is_delete_operator_pod',
        'hostnetwork',
        'tolerations',
        'security_context',
        'container_security_context',
        'dnspolicy',
        'schedulername',
        'full_pod_spec',
        'init_containers',
        'log_events_on_failure',
        'do_xcom_push',
        'pod_template_file',
        'priority_class_name',
        'pod_runtime_info_envs',
        'termination_grace_period',
        'configmaps'
    }

    def __new__(
        cls,
        env: dict = {},
        mounts_volumes: list = [],
        use_kubernetes: bool = True,
        **kwargs
    ):
        task_id = kwargs['task_id']

        if use_kubernetes:
            kwargs['cmds'] = kwargs.get(
                'cmds', kwargs.pop('entrypoint', [])
            )
            kwargs['arguments'] = kwargs.get(
                'arguments', kwargs.pop('command', [])
            )

            for key in cls.DOCKER_TEMPLATE_FIELDS & kwargs.keys():
                if key != 'image':
                    kwargs.pop(key)

            kwargs['secrets'] = [
                *(
                    Secret('env', env_var, secret_name, env_var)
                    for secret_name, env_vars in env.items()
                    for env_var in env_vars
                ),
                *[
                    Secret(
                        'volume',
                        volume['mount_path'],
                        volume['secret_name'],
                        None,
                        # V1KeyToPath
                        # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1KeyToPath.md
                        [
                            V1KeyToPath(
                                **{
                                    key: value
                                    for key, value in item.items()
                                    if key in ['key', 'mode', 'path']
                                }
                            )
                            for item in volume['items']
                        ]
                    )
                    for volume in mounts_volumes
                ],
                *kwargs.get('secrets', [])
            ]
            kwargs['name'] = kwargs.get('name', task_id)
            kwargs['labels'] = kwargs.get('labels', {'pod-label': task_id})
            kwargs['image_pull_policy'] = kwargs.get(
                'image_pull_policy', 'Always'
            )
            kwargs['is_delete_operator_pod'] = kwargs.get(
                'is_delete_operator_pod', True
            )
            kwargs['in_cluster'] = kwargs.get('in_cluster', True)
            kwargs['get_logs'] = kwargs.get('get_logs', True)

            operator = KubernetesPodOperator(**kwargs)
        else:
            kwargs['entrypoint'] = kwargs.get(
                'entrypoint', kwargs.pop('cmds', [])
            )
            kwargs['command'] = kwargs.get(
                'command', kwargs.pop('arguments', [])
            )

            for key in cls.K8S_TEMPLATE_FIELDS & kwargs.keys():
                if key != 'image':
                    kwargs.pop(key)

            kwargs['private_environment'] = {
                **{
                    key: Variable.get(
                        key.lower()
                    )
                    for value in env.values()
                    for key in value
                },
                **kwargs.get('private_environment', {})
            }
            kwargs['mounts'] = [
                *[
                    Mount(
                        **{
                            key: os.path.join(
                                volume[value], item['path']
                            )
                            for key, value in {
                                'source': 'source_path',
                                'target': 'mount_path'
                            }.items()
                        },
                        type='bind',
                        read_only=item['read_only']
                    )
                    for volume in mounts_volumes
                    for item in volume['items']
                ],
                *kwargs.get('mounts', [])
            ]
            kwargs['container_name'] = kwargs.get('container_name', task_id)
            kwargs['mount_tmp_dir'] = kwargs.get('mount_tmp_dir', False)
            kwargs['auto_remove'] = kwargs.get('auto_remove', True)
            kwargs['docker_url'] = kwargs.get(
                'docker_url', 'tcp://docker-proxy:2375'
            )

            operator = DockerOperator(**kwargs)

        return operator
