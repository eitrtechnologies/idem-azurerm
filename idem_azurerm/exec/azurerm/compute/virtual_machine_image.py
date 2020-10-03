# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Virtual Machine Image Execution Module

.. versionadded:: 4.0.0

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

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def get(hub, ctx, location, publisher, offer, sku, version, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a virtual machine image.

    :param location: The name of a supported Azure region.

    :param publisher: A valid image publisher.

    :param offer: A valid image publisher offer.

    :param sku: A valid image SKU.

    :param version: A valid image SKU version.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_image.get "eastus" test_publisher test_offer test_sku test_version

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        image = compconn.virtual_machine_images.get(
            location=location,
            publisher_name=publisher,
            offer=offer,
            skus=sku,
            version=version,
        )

        result = image.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, location, publisher, offer, sku, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a list of all virtual machine image versions for the specified location, publisher, offer, and SKU.

    :param location: The name of a supported Azure region.

    :param publisher: A valid image publisher.

    :param offer: A valid image publisher offer.

    :param sku: A valid image SKU.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_image.list "eastus" test_publisher test_offer test_sku

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_images.list(
            location=location,
            skus=sku,
            publisher_name=publisher,
            offer=offer,
            **kwargs,
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except (CloudError, AttributeError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_offers(hub, ctx, location, publisher, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a list of virtual machine image offers for the specified location and publisher.

    :param location: The name of a supported Azure region.

    :param publisher: A valid image publisher.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_image.list_offers "eastus" test_publisher

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_images.list_offers(
            location=location, publisher_name=publisher, **kwargs
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_publishers(hub, ctx, location, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a list of virtual machine image publishers for the specified Azure location.

    :param location: The name of a supported Azure region.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_image.list_publishers "eastus"

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_images.list_publishers(
            location=location, **kwargs
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_skus(hub, ctx, location, publisher, offer, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a list of virtual machine image offers for the specified location and publisher.

    :param location: The name of a supported Azure region.

    :param publisher: A valid image publisher.

    :param offer: A valid image publisher offer.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_image.list_skus "eastus" test_publisher test_offer

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        images = compconn.virtual_machine_images.list_skus(
            location=location, publisher_name=publisher, offer=offer, **kwargs
        )

        for image in images:
            img = image.as_dict()
            result[img["name"]] = img
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
