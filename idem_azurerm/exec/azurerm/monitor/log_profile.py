# -*- coding: utf-8 -*-
"""
Azure (ARM) Monitor Log Profile Execution Module

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
    import azure.mgmt.monitor.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List log profiles.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.log_profile.list

    """
    result = {}
    moniconn = await hub.exec.azurerm.utils.get_client(ctx, "monitor", **kwargs)
    try:
        profiles = await hub.exec.azurerm.utils.paged_object_to_list(
            moniconn.log_profiles.list()
        )

        for profile in profiles:
            result[profile["name"]] = profile
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("monitor", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
