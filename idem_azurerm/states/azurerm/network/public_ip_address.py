# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Public IP Address State Module

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
    "present": {"require": ["states.azurerm.resource.group.present",]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    tags=None,
    sku=None,
    public_ip_allocation_method=None,
    public_ip_address_version=None,
    dns_settings=None,
    idle_timeout_in_minutes=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a public IP address exists.

    :param name:
        Name of the public IP address.

    :param resource_group:
        The resource group assigned to the public IP address.

    :param dns_settings:
        An optional dictionary representing a valid PublicIPAddressDnsSettings object. Parameters include
        'domain_name_label' and 'reverse_fqdn', which accept strings. The 'domain_name_label' parameter is concatenated
        with the regionalized DNS zone make up the fully qualified domain name associated with the public IP address.
        If a domain name label is specified, an A DNS record is created for the public IP in the Microsoft Azure DNS
        system. The 'reverse_fqdn' parameter is a user-visible, fully qualified domain name that resolves to this public
        IP address. If the reverse FQDN is specified, then a PTR DNS record is created pointing from the IP address in
        the in-addr.arpa domain to the reverse FQDN.

    :param sku:
        The public IP address SKU, which can be 'Basic' or 'Standard'.

    :param public_ip_allocation_method:
        The public IP allocation method. Possible values are: 'Static' and 'Dynamic'.

    :param public_ip_address_version:
        The public IP address version. Possible values are: 'IPv4' and 'IPv6'.

    :param idle_timeout_in_minutes:
        An integer representing the idle timeout of the public IP address.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the public IP address object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure public IP exists:
            azurerm.network.public_ip_address.present:
                - name: pub_ip1
                - resource_group: group1
                - dns_settings:
                    domain_name_label: decisionlab-ext-test-label
                - sku: basic
                - public_ip_allocation_method: static
                - public_ip_address_version: ipv4
                - idle_timeout_in_minutes: 4
                - tags:
                    contact_name: Elmer Fudd Gantry
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

    if sku:
        sku = {"name": sku.capitalize()}

    pub_ip = await hub.exec.azurerm.network.public_ip_address.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in pub_ip:
        action = "update"
        # tag changes
        tag_changes = differ.deep_diff(pub_ip.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # dns_settings changes
        if dns_settings:
            if not isinstance(dns_settings, dict):
                ret["comment"] = "DNS settings must be provided as a dictionary!"
                return ret

            for key in dns_settings:
                if dns_settings[key] != pub_ip.get("dns_settings", {}).get(key):
                    ret["changes"]["dns_settings"] = {
                        "old": pub_ip.get("dns_settings"),
                        "new": dns_settings,
                    }
                    break

        # sku changes
        if sku:
            sku_changes = differ.deep_diff(pub_ip.get("sku", {}), sku)
            if sku_changes:
                ret["changes"]["sku"] = sku_changes

        # public_ip_allocation_method changes
        if public_ip_allocation_method:
            if public_ip_allocation_method.capitalize() != pub_ip.get(
                "public_ip_allocation_method"
            ):
                ret["changes"]["public_ip_allocation_method"] = {
                    "old": pub_ip.get("public_ip_allocation_method"),
                    "new": public_ip_allocation_method,
                }

        # public_ip_address_version changes
        if public_ip_address_version:
            if (
                public_ip_address_version.lower()
                != pub_ip.get("public_ip_address_version", "").lower()
            ):
                ret["changes"]["public_ip_address_version"] = {
                    "old": pub_ip.get("public_ip_address_version"),
                    "new": public_ip_address_version,
                }

        # idle_timeout_in_minutes changes
        if idle_timeout_in_minutes and (
            int(idle_timeout_in_minutes) != pub_ip.get("idle_timeout_in_minutes")
        ):
            ret["changes"]["idle_timeout_in_minutes"] = {
                "old": pub_ip.get("idle_timeout_in_minutes"),
                "new": idle_timeout_in_minutes,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Public IP address {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Public IP address {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "tags": tags,
                "dns_settings": dns_settings,
                "sku": sku,
                "public_ip_allocation_method": public_ip_allocation_method,
                "public_ip_address_version": public_ip_address_version,
                "idle_timeout_in_minutes": idle_timeout_in_minutes,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Public IP address {0} would be created.".format(name)
        ret["result"] = None
        return ret

    pub_ip_kwargs = kwargs.copy()
    pub_ip_kwargs.update(connection_auth)

    pub_ip = await hub.exec.azurerm.network.public_ip_address.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        sku=sku,
        tags=tags,
        dns_settings=dns_settings,
        public_ip_allocation_method=public_ip_allocation_method,
        public_ip_address_version=public_ip_address_version,
        idle_timeout_in_minutes=idle_timeout_in_minutes,
        **pub_ip_kwargs,
    )

    if "error" not in pub_ip:
        ret["result"] = True
        ret["comment"] = f"Public IP address {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} public IP address {1}! ({2})".format(
        action, name, pub_ip.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a public IP address does not exist in the resource group.

    :param name:
        Name of the public IP address.

    :param resource_group:
        The resource group assigned to the public IP address.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    pub_ip = await hub.exec.azurerm.network.public_ip_address.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in pub_ip:
        ret["result"] = True
        ret["comment"] = "Public IP address {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Public IP address {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": pub_ip,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.public_ip_address.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Public IP address {0} has been deleted.".format(name)
        ret["changes"] = {"old": pub_ip, "new": {}}
        return ret

    ret["comment"] = "Failed to delete public IP address {0}!".format(name)
    return ret
