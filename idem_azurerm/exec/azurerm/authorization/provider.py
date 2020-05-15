# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Authorization Provider Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
to every function in order to work properly.

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


async def operations_metadata_get(
    hub, resource_provider_namespace, api_version="2015-07-01", **kwargs
):
    """
    .. versionadded:: 1.0.0

    Gets provider operations metadata for the specified resource provider.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param api_version: The API version to use for the operation.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.provider.operations_metadata_get testnamespace

    """
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client("authorization", **kwargs)
    try:
        data = authconn.provider_operations_metadata.get(
            resource_provider_namespace=resource_provider_namespace,
            api_version=api_version,
            **kwargs,
        )

        result = data.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def operations_metadata_list(hub, api_version="2015-07-01", **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets provider operations metadata for all resource providers.

    :param api_version: The API version to use for the operation.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.provider.operations_metadata_list

    """
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client("authorization", **kwargs)

    try:
        providers = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.provider_operations_metadata.list(
                api_version=api_version, **kwargs
            )
        )

        for provider in providers:
            result[provider["name"]] = provider
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
