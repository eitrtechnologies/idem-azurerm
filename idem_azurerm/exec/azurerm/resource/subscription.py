# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Subscription Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 2.7.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.34.3
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.2
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
from json import loads, dumps
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


async def list_locations(hub, subscription_id=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all locations for a subscription.

    :param subscription_id: The ID of the subscription to query.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.subscription.list_locations XXXXXXXX

    """
    result = {}

    if not subscription_id:
        subscription_id = kwargs.get("subscription_id")
    elif not kwargs.get("subscription_id"):
        kwargs["subscription_id"] = subscription_id

    subconn = await hub.exec.utils.azurerm.get_client("subscription", **kwargs)
    try:
        locations = await hub.exec.utils.azurerm.paged_object_to_list(
            subconn.subscriptions.list_locations(
                subscription_id=kwargs["subscription_id"]
            )
        )

        for loc in locations:
            result[loc["name"]] = loc
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, subscription_id=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a subscription.

    :param subscription_id: The ID of the subscription to query.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.subscription.get XXXXXXXX

    """
    result = {}

    if not subscription_id:
        subscription_id = kwargs.get("subscription_id")
    elif not kwargs.get("subscription_id"):
        kwargs["subscription_id"] = subscription_id

    subconn = await hub.exec.utils.azurerm.get_client("subscription", **kwargs)
    try:
        subscription = subconn.subscriptions.get(
            subscription_id=kwargs.get("subscription_id")
        )

        result = subscription.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all subscriptions for a tenant.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.subscription.list

    """
    result = {}
    subconn = await hub.exec.utils.azurerm.get_client("subscription", **kwargs)
    try:
        subs = await hub.exec.utils.azurerm.paged_object_to_list(
            subconn.subscriptions.list()
        )

        for sub in subs:
            result[sub["subscription_id"]] = sub
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
