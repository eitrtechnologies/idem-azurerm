# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Virtual Machine Extension Image Operations Execution Module

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
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def get(hub, ctx, location, publisher, extension_type, version, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a virtual machine extension image.

    :param location: The name of a supported Azure region.

    :param publisher: The publisher of the extension image.

    :param extension_type: The type of extension by the publisher.

    :param version: The version of the extension type.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension.get test_loc test_publisher test_type test_version

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        image = compconn.virtual_machine_extension_images.get(
            location=location,
            publisher_name=publisher,
            version=version,
            type=extension_type,
            **kwargs,
        )

        result = image.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_types(hub, ctx, location, publisher, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a list of virtual machine extension image types.

    :param location: The name of a supported Azure region.

    :param publisher: The name of the publisher of the extension types.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension_image.list_types test_loc test_publisher

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_extension_images.list_types(
            location=location, publisher_name=publisher,
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_versions(hub, ctx, location, publisher, extension_type, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a list of virtual machine extension image versions.

    :param location: The name of a supported Azure region.

    :param publisher: The name of the publisher of the extension.

    :param extension_type: The type of extension from the publisher to get the version(s) for.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension_image.list_versions test_loc test_publisher test_type

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_extension_images.list_versions(
            location=location, publisher_name=publisher, type=extension_type
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
