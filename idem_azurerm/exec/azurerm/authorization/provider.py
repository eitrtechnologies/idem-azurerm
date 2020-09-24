# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Authorization Provider Execution Module

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
    import azure.mgmt.authorization.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def operations_metadata_get(hub, ctx, resource_provider_namespace, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Gets provider operations metadata for the specified resource provider.

    :param resource_provider_namespace: The namespace of the resource provider.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.provider.operations_metadata_get testnamespace

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)
    try:
        data = authconn.provider_operations_metadata.get(
            resource_provider_namespace=resource_provider_namespace, **kwargs,
        )

        result = data.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def operations_metadata_list(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Gets provider operations metadata for all resource providers.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.provider.operations_metadata_list

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        providers = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.provider_operations_metadata.list(**kwargs)
        )

        for provider in providers:
            result[provider["name"]] = provider
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
