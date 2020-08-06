# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Profile State Module

.. versionadded:: 3.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed via acct. Note that the
    authentication parameters are case sensitive.

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud. Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

    Example configuration for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            default:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

    The authentication parameters can also be passed as a dictionary of keyword arguments to the ``connection_auth``
    parameter of each state, but this is not preferred and could be deprecated in the future.

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        Ensure network profile exists:
            azurerm.network.network_profile.present:
                - name: aci-network-profile
                - resource_group: testgroup
                - container_network_interface_configurations:
                    - name: eth0
                      ip_configurations:
                        - name: ipconfigprofile
                          subnet:
                              id: {{ subnet_resource_id }}
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

        Ensure network profile is absent:
            azurerm.network.network_profile.absent:
                - name: aci-network-profile
                - resource_group: testgroup

"""
# Import Python libs
from dict_tools import differ
import logging


log = logging.getLogger(__name__)


async def present(
    hub,
    ctx,
    name,
    resource_group,
    container_network_interfaces=None,
    container_network_interface_configurations=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Ensure a network profile exists.

    :param name: The name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    :param container_network_interfaces: List of child `container network interfaces
        <https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2018_12_01.models.containernetworkinterface?view=azure-python>`_.

    :param container_network_interface_configurations: List of child `container network interface configurations
        <https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2018_12_01.models.containernetworkinterfaceconfiguration?view=azure-python>`_.

    :param tags: A dictionary of strings can be passed as tag metadata to the object.


    Example usage:

    .. code-block:: yaml

        Ensure network profile exists:
            azurerm.network.network_profile.present:
                - name: aci-network-profile
                - resource_group: testgroup
                - container_network_interface_configurations:
                    - name: eth0
                      ip_configurations:
                        - name: ipconfigprofile
                          subnet:
                              id: {{ subnet_resource_id }}
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"
    new = {}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    # populate dictionary of settings for changes output on creation
    for param in [
        "name",
        "resource_group",
        "container_network_interfaces",
        "container_network_interface_configurations",
        "tags",
    ]:
        value = locals()[param]
        if value is not None:
            new[param] = value

    # get existing network profile if present
    prf = await hub.exec.azurerm.network.network_profile.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in prf:
        action = "update"

        # container_network_interfaces changes
        if container_network_interfaces:
            comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
                prf.get("container_network_interfaces"), container_network_interfaces
            )
            if comp.get("changes"):
                ret["changes"]["container_network_interfaces"] = comp["changes"]

        # container_network_interface_configurations changes
        if container_network_interface_configurations:
            comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
                prf.get("container_network_interface_configurations"),
                container_network_interface_configurations,
            )
            if comp.get("changes"):
                ret["changes"]["container_network_interface_configurations"] = comp[
                    "changes"
                ]

        # tag changes
        tag_diff = differ.deep_diff(prf.get("tags", {}), tags or {})
        if tag_diff:
            ret["changes"]["tags"] = tag_diff

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Network profile {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Network profile {0} would be updated.".format(name)
            ret["result"] = None
            return ret

    elif ctx["test"]:
        ret["comment"] = "Network profile {0} would be created.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": {},
            "new": new,
        }
        return ret

    prf_kwargs = kwargs.copy()
    prf_kwargs.update(connection_auth)

    if action == "create" or len(ret["changes"]) > 1 or not tag_diff:
        prf = await hub.exec.azurerm.network.network_profile.create_or_update(
            ctx,
            name,
            resource_group,
            container_network_interfaces=container_network_interfaces,
            container_network_interface_configurations=container_network_interface_configurations,
            tags=tags,
            **prf_kwargs,
        )

    # no idea why create_or_update doesn't work for tags
    if action == "update" and tag_diff:
        prf = await hub.exec.azurerm.network.network_profile.update_tags(
            ctx, name, resource_group, tags=tags, **prf_kwargs,
        )

    if "error" not in prf:
        ret["result"] = True
        ret["comment"] = f"Network profile {name} has been {action}d."
        if not ret["changes"]:
            ret["changes"] = {"old": {}, "new": new}
        return ret

    ret["comment"] = "Failed to {0} network profile {1}! ({2})".format(
        action, name, prf.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Ensure a network profile does not exist in a resource group.

    :param name: Name of the network profile.

    :param resource_group: The name of the resource group to which the network profile belongs.

    .. code-block:: yaml

        Ensure network profile is absent:
            azurerm.network.network_profile.absent:
                - name: aci-network-profile
                - resource_group: testgroup

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    prf = {}

    prf = await hub.exec.azurerm.network.network_profile.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in prf:
        ret["result"] = True
        ret["comment"] = "Network profile {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Network profile {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": prf,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.network_profile.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Network profile {0} has been deleted.".format(name)
        ret["changes"] = {"old": prf, "new": {}}
        return ret

    ret["comment"] = "Failed to delete network profile {0}!".format(name)
    return ret
