# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Image Execution Module

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


async def create_or_update(
    hub,
    ctx,
    name,
    resource_group,
    source_vm=None,
    source_vm_group=None,
    os_disk=None,
    data_disks=None,
    zone_resilient=False,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Create or update an image.

    :param name: The image to create.

    :param resource_group: The resource group name assigned to the image.

    :param source_vm: The name of the virtual machine from which the image is created. This parameter
        or a valid os_disk is required.

    :param source_vm_group: The name of the resource group containing the source virtual machine.
        This defaults to the same resource group specified for the resultant image.

    :param os_disk: The resource ID of an operating system disk to use for the image.

    :param data_disks: The resource ID or list of resource IDs associated with data disks to add to
        the image.

    :param zone_resilient: Specifies whether an image is zone resilient or not. Zone resilient images
        can be created only in regions that provide Zone Redundant Storage (ZRS).

    CLI Example:

    .. code-block:: bash

        azurerm.compute.image.create_or_update testimage testgroup

    """
    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            ctx, resource_group, **kwargs
        )

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {
                "error": "Unable to determine location from resource group specified."
            }
        kwargs["location"] = rg_props["location"]

    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    if source_vm:
        # Use VM name to link to the IDs of existing VMs.
        vm_instance = await hub.exec.azurerm.compute.virtual_machine.get(
            ctx=ctx,
            name=source_vm,
            resource_group=(source_vm_group or resource_group),
            log_level="info",
            **kwargs,
        )

        if "error" in vm_instance:
            errmsg = "The source virtual machine could not be found."
            log.error(errmsg)
            result = {"error": errmsg}
            return result

        source_vm = {"id": str(vm_instance["id"])}

    spmodel = None
    if os_disk:
        if is_valid_resource_id(os_disk):
            os_disk = {"id": os_disk}
        else:
            errmsg = "The os_disk parameter is not a valid resource ID string."
            log.error(errmsg)
            result = {"error": errmsg}
            return result

        if data_disks:
            if isinstance(data_disks, list):
                data_disks = [{"id": dd} for dd in data_disks]
            elif isinstance(data_disks, six.string_types):
                data_disks = [{"id": data_disks}]
            else:
                errmsg = "The data_disk parameter is a single resource ID string or a list of resource IDs."
                log.error(errmsg)
                result = {"error": errmsg}
                return result

        try:
            spmodel = await hub.exec.azurerm.utils.create_object_model(
                "compute",
                "ImageStorageProfile",
                os_disk=os_disk,
                data_disks=data_disks,
                zone_resilient=zone_resilient,
                **kwargs,
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

    try:
        imagemodel = await hub.exec.azurerm.utils.create_object_model(
            "compute",
            "Image",
            source_virtual_machine=source_vm,
            storage_profile=spmodel,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        image = compconn.images.create_or_update(
            resource_group_name=resource_group, image_name=name, parameters=imagemodel
        )
        image.wait()
        image_result = image.result()
        result = image_result.as_dict()

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete an image.

    :param name: The image to delete.

    :param resource_group: The resource group name assigned to the image.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.image.delete testimage testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        compconn.images.delete(resource_group_name=resource_group, image_name=name)
        result = True

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a dictionary representing an image's properties.

    :param name: The image to get.

    :param resource_group: The resource group name assigned to the image.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.image.get testimage testgroup

    """
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        image = compconn.images.get(resource_group_name=resource_group, image_name=name)
        result = image.as_dict()

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def images_list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all images within a resource group.

    :param resource_group: The resource group name to list images within.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.image.list_by_resource_group testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        images = await hub.exec.azurerm.utils.paged_object_to_list(
            compconn.images.list_by_resource_group(resource_group_name=resource_group)
        )

        for image in images:
            result[image["name"]] = image
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def images_list(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all images in a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.image.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        images = await hub.exec.azurerm.utils.paged_object_to_list(
            compconn.images.list()
        )

        for image in images:
            result[image["name"]] = image
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
