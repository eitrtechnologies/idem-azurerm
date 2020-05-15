# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Provider Execution Module

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


async def list_(hub, top=None, expand=None, **kwargs):
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
    resconn = await hub.exec.utils.azurerm.get_client("resource", **kwargs)

    if not expand:
        expand = "resourceTypes/aliases"

    try:
        groups = await hub.exec.utils.azurerm.paged_object_to_list(
            resconn.providers.list(top=top, expand=expand)
        )

        for group in groups:
            result[group["namespace"]] = group
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
