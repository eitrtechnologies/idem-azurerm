# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute SSH Public Key Execution Module

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


async def create(hub, ctx, name, resource_group, public_key=None, tags=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Creates a new SSH public key resource.

    :param name: The name of the SSH public key.

    :param resource_group: The name of the resource group name assigned to the SSH public key.

    :param public_key: SSH public key used to authenticate to a virtual machine through ssh. If this property is not
        initially provided when the resource is created, the ``public_key`` parameter will be populated when the
        generate_key_pair module is called. If the public key is provided upon resource creation, the provided public
        key needs to be at least 2048-bit and in ssh-rsa format.

    :param tags: A dictionary of strings can be passed as tag metadata to the SSH public key resource object.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.create test_name test_group

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

    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        keymodel = await hub.exec.azurerm.utils.create_object_model(
            "compute",
            "SshPublicKeyResource",
            public_key=public_key,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        key = compconn.ssh_public_keys.create(
            resource_group_name=resource_group,
            ssh_public_key_name=name,
            parameters=keymodel,
        )

        result = key.as_dict()
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
    .. versionadded:: 4.0.0

    Delete an SSH public key.

    :param name: The SSH public key to delete.

    :param resource_group: The resource group name assigned to the SSH public key.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.delete test_name test_group

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        key = compconn.ssh_public_keys.delete(
            resource_group_name=resource_group, ssh_public_key_name=name
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Retrieves information about an SSH public key.

    :param name: The SSH public key to get.

    :param resource_group: The resource group name assigned to the SSH public key.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.get test_name test_group

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        key = compconn.ssh_public_keys.get(
            resource_group_name=resource_group, ssh_public_key_name=name
        )

        result = key.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def generate_key_pair(
    hub, ctx, name, resource_group, public_key=None, tags=None, **kwargs
):
    """
    .. versionadded:: 4.0.0

    Generates and returns a public/private key pair and populates the SSH public key resource with the public key.
    The length of the key will be 3072 bits. This operation can only be performed once per SSH public key resource.

    :param name: The name of the SSH public key.

    :param resource_group: The name of the resource group name assigned to the SSH public key.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.generate_key_pair test_name test_group

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

    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        key = compconn.ssh_public_keys.generate_key_pair(
            resource_group_name=resource_group, ssh_public_key_name=name, **kwargs
        )

        result = key.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all of the SSH public keys in the subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            keys = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.ssh_public_keys.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            keys = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.ssh_public_keys.list_by_subscription()
            )

        for key in keys:
            result[key["name"]] = key
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update(hub, ctx, name, resource_group, public_key=None, tags=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Creates a new SSH public key resource.

    :param name: The name of the SSH public key.

    :param resource_group: The name of the resource group name assigned to the SSH public key.

    :param public_key: SSH public key used to authenticate to a virtual machine through ssh. If this property is not
        initially provided when the resource is created, the ``public_key`` parameter will be populated when the
        generate_key_pair module is called. If the public key is provided upon resource creation, the provided public
        key needs to be at least 2048-bit and in ssh-rsa format.

    :param tags: A dictionary of strings can be passed as tag metadata to the SSH public key resource object.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.ssh_public_key.create test_name test_group

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

    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        key = compconn.ssh_public_keys.update(
            resource_group_name=resource_group,
            ssh_public_key_name=name,
            public_key=public_key,
            tags=tags,
            **kwargs,
        )

        result = key.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result
