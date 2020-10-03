# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Provider Execution Module

.. versionadded:: 1.0.0

.. versionchanged:: 4.0.0

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
from __future__ import absolute_import
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets the specified resource provider.

    :param name: The namespace of the resource provider.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.provider.get test_name

    """
    result = {}
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)

    try:
        provider = resconn.providers.get(resource_provider_namespace=name)

        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, top=None, expand=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all resource providers for a subscription.

    :param top: The number of results to return. Default returns all providers.

    :param expand: The properties to include in the results. For example, use 'metadata' in the query string
        to retrieve resource provider metadata. To include property aliases in response, use 'resourceTypes/aliases'.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.provider.list

    """
    result = {}
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)

    if not expand:
        expand = "resourceTypes/aliases"

    try:
        groups = await hub.exec.azurerm.utils.paged_object_to_list(
            resconn.providers.list(top=top, expand=expand)
        )

        for group in groups:
            result[group["namespace"]] = group
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
