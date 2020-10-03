# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Graph RBAC Client Utility

.. versionadded:: 2.4.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    Optional provider parameters:

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

"""
# Python libs
import logging

# Azure libs
HAS_LIBS = False
try:
    from azure.graphrbac import GraphRbacManagementClient

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


async def get(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.4.0

    Load the Graph RBAC Management client and return a GraphRbacManagementClient object.

    """
    (
        credentials,
        subscription_id,
        cloud_env,
    ) = await hub.exec.azurerm.utils.determine_auth(ctx, **kwargs)

    graph_client = GraphRbacManagementClient(
        credentials=credentials, tenant_id=credentials._tenant
    )

    return graph_client
