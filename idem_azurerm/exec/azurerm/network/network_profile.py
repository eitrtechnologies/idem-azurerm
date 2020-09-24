# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Profile Execution Module

.. versionadded:: 3.0.0

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
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass


__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


async def create_or_update(
    hub,
    ctx,
    name,
    resource_group,
    container_network_interfaces=None,
    container_network_interface_configurations=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates or updates a network profile.

    :param name: The name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    :param container_network_interfaces: List of child `container network interfaces
        <https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2018_12_01.models.containernetworkinterface?view=azure-python>`__.

    :param container_network_interface_configurations: List of child `container network interface configurations
        <https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2018_12_01.models.containernetworkinterfaceconfiguration?view=azure-python>`__.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_profile.create_or_update myprofile mygroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

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

    try:
        prfmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "NetworkProfile",
            container_network_interfaces=container_network_interfaces,
            container_network_interface_configurations=container_network_interface_configurations,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        prf = netconn.network_profiles.create_or_update(
            network_profile_name=name,
            resource_group_name=resource_group,
            parameters=prfmodel,
        )

        prf.wait()
        result = prf.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update_tags(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Updates network profile tags with specified values.

    :param name: The name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_profile.update_tags myprofile mygroup tags='{"owner": "me"}'

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        prf = netconn.network_profiles.update_tags(
            network_profile_name=name, resource_group_name=resource_group, tags=tags,
        )

        result = prf.as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets the specified network profile in a specified resource group.

    :param name: The name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_profile.get myprofile mygroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        ret = netconn.network_profiles.get(
            network_profile_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets all network profiles in a resource group or subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_profile.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        if resource_group:
            profiles = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.network_profiles.list(resource_group_name=resource_group)
            )
        else:
            profiles = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.network_profiles.list_all()
            )

        for profile in profiles:
            result[profile["name"]] = profile
    except (CloudError, Exception) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Deletes the specified network profile.

    :param name: The name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_profile.delete myprofile mygroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        ret = netconn.network_profiles.delete(
            network_profile_name=name, resource_group_name=resource_group
        )

        ret.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
