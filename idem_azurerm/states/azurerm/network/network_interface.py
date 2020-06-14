# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Interface State Module

.. versionadded:: 1.0.0

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

    Example acct setup for Azure Resource Manager authentication:

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

        Ensure virtual network exists:
            azurerm.network.virtual_network.present:
                - name: my_vnet
                - resource_group: my_rg
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'
                - dns_servers:
                    - '8.8.8.8'
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure virtual network is absent:
            azurerm.network.virtual_network.absent:
                - name: other_vnet
                - resource_group: my_rg
                - connection_auth: {{ profile }}

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging
import re

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.virtual_network.present",
            "states.azurerm.network.virtual_network.subnet_present",
            "states.azurerm.network.network_security_group.present",
            "states.azurerm.network.load_balancer.present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    ip_configurations,
    subnet,
    virtual_network,
    resource_group,
    tags=None,
    virtual_machine=None,
    network_security_group=None,
    dns_settings=None,
    mac_address=None,
    primary=None,
    enable_accelerated_networking=None,
    enable_ip_forwarding=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a network interface exists.

    :param name:
        Name of the network interface.

    :param ip_configurations:
        A list of dictionaries representing valid NetworkInterfaceIPConfiguration objects. The 'name' key is required at
        minimum. At least one IP Configuration must be present.

    :param subnet:
        Name of the existing subnet assigned to the network interface.

    :param virtual_network:
        Name of the existing virtual network containing the subnet.

    :param resource_group:
        The resource group assigned to the virtual network.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the network interface object.

    :param network_security_group:
        The name of the existing network security group to assign to the network interface.

    :param virtual_machine:
        The name of the existing virtual machine to assign to the network interface.

    :param dns_settings:
        An optional dictionary representing a valid NetworkInterfaceDnsSettings object. Valid parameters are:

        - ``dns_servers``: List of DNS server IP addresses. Use 'AzureProvidedDNS' to switch to Azure provided DNS
          resolution. 'AzureProvidedDNS' value cannot be combined with other IPs, it must be the only value in
          dns_servers collection.
        - ``internal_dns_name_label``: Relative DNS name for this NIC used for internal communications between VMs in
          the same virtual network.
        - ``internal_fqdn``: Fully qualified DNS name supporting internal communications between VMs in the same virtual
          network.
        - ``internal_domain_name_suffix``: Even if internal_dns_name_label is not specified, a DNS entry is created for
          the primary NIC of the VM. This DNS name can be constructed by concatenating the VM name with the value of
          internal_domain_name_suffix.

    :param mac_address:
        Optional string containing the MAC address of the network interface.

    :param primary:
        Optional boolean allowing the interface to be set as the primary network interface on a virtual machine
        with multiple interfaces attached.

    :param enable_accelerated_networking:
        Optional boolean indicating whether accelerated networking should be enabled for the interface.

    :param enable_ip_forwarding:
        Optional boolean indicating whether IP forwarding should be enabled for the interface.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure network interface exists:
            azurerm.network.network_interface.present:
                - name: iface1
                - subnet: vnet1_sn1
                - virtual_network: vnet1
                - resource_group: group1
                - ip_configurations:
                  - name: iface1_ipc1
                    public_ip_address: pub_ip2
                - dns_settings:
                    internal_dns_name_label: decisionlab-int-test-label
                - primary: True
                - enable_accelerated_networking: True
                - enable_ip_forwarding: False
                - network_security_group: nsg1
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    iface = await hub.exec.azurerm.network.network_interface.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in iface:
        action = "update"
        # tag changes
        tag_changes = differ.deep_diff(iface.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # mac_address changes
        if mac_address and (mac_address != iface.get("mac_address")):
            ret["changes"]["mac_address"] = {
                "old": iface.get("mac_address"),
                "new": mac_address,
            }

        # primary changes
        if primary is not None:
            if primary != iface.get("primary", True):
                ret["changes"]["primary"] = {
                    "old": iface.get("primary"),
                    "new": primary,
                }

        # enable_accelerated_networking changes
        if enable_accelerated_networking is not None:
            if enable_accelerated_networking != iface.get(
                "enable_accelerated_networking"
            ):
                ret["changes"]["enable_accelerated_networking"] = {
                    "old": iface.get("enable_accelerated_networking"),
                    "new": enable_accelerated_networking,
                }

        # enable_ip_forwarding changes
        if enable_ip_forwarding is not None:
            if enable_ip_forwarding != iface.get("enable_ip_forwarding"):
                ret["changes"]["enable_ip_forwarding"] = {
                    "old": iface.get("enable_ip_forwarding"),
                    "new": enable_ip_forwarding,
                }

        # network_security_group changes
        nsg_name = None
        if iface.get("network_security_group"):
            nsg_name = iface["network_security_group"]["id"].split("/")[-1]

        if network_security_group and (network_security_group != nsg_name):
            ret["changes"]["network_security_group"] = {
                "old": nsg_name,
                "new": network_security_group,
            }

        # virtual_machine changes
        vm_name = None
        if iface.get("virtual_machine"):
            vm_name = iface["virtual_machine"]["id"].split("/")[-1]

        if virtual_machine and (virtual_machine != vm_name):
            ret["changes"]["virtual_machine"] = {"old": vm_name, "new": virtual_machine}

        # dns_settings changes
        if dns_settings:
            if not isinstance(dns_settings, dict):
                ret["comment"] = "DNS settings must be provided as a dictionary!"
                return ret

            for key in dns_settings:
                if (
                    dns_settings[key].lower()
                    != iface.get("dns_settings", {}).get(key, "").lower()
                ):
                    ret["changes"]["dns_settings"] = {
                        "old": iface.get("dns_settings"),
                        "new": dns_settings,
                    }
                    break

        # ip_configurations changes
        comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
            iface.get("ip_configurations", []),
            ip_configurations,
            ["public_ip_address", "subnet"],
        )

        if comp_ret.get("comment"):
            ret["comment"] = '"ip_configurations" {0}'.format(comp_ret["comment"])
            return ret

        if comp_ret.get("changes"):
            ret["changes"]["ip_configurations"] = comp_ret["changes"]

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Network interface {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Network interface {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "ip_configurations": ip_configurations,
                "dns_settings": dns_settings,
                "network_security_group": network_security_group,
                "virtual_machine": virtual_machine,
                "enable_accelerated_networking": enable_accelerated_networking,
                "enable_ip_forwarding": enable_ip_forwarding,
                "mac_address": mac_address,
                "primary": primary,
                "tags": tags,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Network interface {0} would be created.".format(name)
        ret["result"] = None
        return ret

    iface_kwargs = kwargs.copy()
    iface_kwargs.update(connection_auth)

    iface = await hub.exec.azurerm.network.network_interface.create_or_update(
        ctx=ctx,
        name=name,
        subnet=subnet,
        virtual_network=virtual_network,
        resource_group=resource_group,
        ip_configurations=ip_configurations,
        dns_settings=dns_settings,
        enable_accelerated_networking=enable_accelerated_networking,
        enable_ip_forwarding=enable_ip_forwarding,
        mac_address=mac_address,
        primary=primary,
        network_security_group=network_security_group,
        virtual_machine=virtual_machine,
        tags=tags,
        **iface_kwargs,
    )

    if "error" not in iface:
        ret["result"] = True
        ret["comment"] = f"Network interface {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} network interface {1}! ({2})".format(
        action, name, iface.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a network interface does not exist in the resource group.

    :param name:
        Name of the network interface.

    :param resource_group:
        The resource group assigned to the network interface.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure network interface absent:
            azurerm.network.network_interface.absent:
                - name: iface1
                - resource_group: group1
                - connection_auth: {{ profile }}

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

    iface = await hub.exec.azurerm.network.network_interface.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in iface:
        ret["result"] = True
        ret["comment"] = "Network interface {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Network interface {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": iface,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.network_interface.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Network interface {0} has been deleted.".format(name)
        ret["changes"] = {"old": iface, "new": {}}
        return ret

    ret["comment"] = "Failed to delete network interface {0}!)".format(name)
    return ret
