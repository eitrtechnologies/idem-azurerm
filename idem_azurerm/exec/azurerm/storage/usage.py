# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Usage Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def list_(hub, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the current usage count and the limit for the resources under the subscription.

    CLI Example:

    .. code-block:: bash

       azurerm.storage.usage.list

    """
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client("storage", **kwargs)

    try:
        usages = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.usage.list()
        )

        for usage in usages:
            result[usage["name"]["value"]] = usage
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_location(hub, location, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the current usage count and the limit for the resources of the location under the subscription.

    :param location: The location of the Azure Storage resource.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.usage.list_by_location test_location

    """
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client("storage", **kwargs)

    try:
        usages = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.usage.list_by_location(location)
        )

        for usage in usages:
            result[usage["name"]["value"]] = usage
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
