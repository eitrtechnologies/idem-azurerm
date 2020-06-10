# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) SKU Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    Lists the available SKUs supported by Microsoft.Storage for given subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.sku.list

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        skus = await hub.exec.azurerm.utils.paged_object_to_list(storconn.skus.list())

        for sku in skus:
            result[sku["name"]] = sku
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
