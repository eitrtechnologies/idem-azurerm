# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Usage Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def list_by_location(hub, ctx, location, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets the current usage count and the limit for the resources of the location under the subscription.

    :param location: The location of the Azure Storage resource.

    CLI Example:

    .. code-block:: bash

       azurerm.storage.usage.list_by_location "eastus"

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        usages = await hub.exec.azurerm.utils.paged_object_to_list(
            storconn.usages.list_by_location(location=location)
        )

        for usage in usages:
            result[usage["name"]["value"]] = usage
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
