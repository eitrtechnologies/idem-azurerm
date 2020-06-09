# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Disk Execution Module

.. versionadded:: 1.0.0

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
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import is_valid_resource_id

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a disk.

    :param name: The disk to delete.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.delete testdisk testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        compconn.disks.delete(resource_group_name=resource_group, disk_name=name)
        result = True

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)

    return result
