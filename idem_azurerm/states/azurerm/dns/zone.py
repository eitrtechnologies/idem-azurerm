# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) DNS Zone State Module

.. versionadded:: 1.0.0

.. versionchanged:: 4.0.0

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
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

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging

log = logging.getLogger(__name__)

TREQ = {
    "present": {"require": ["states.azurerm.resource.group.present",]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    etag=None,
    if_match=None,
    if_none_match=None,
    registration_virtual_networks=None,
    resolution_virtual_networks=None,
    tags=None,
    zone_type="Public",
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a DNS zone exists.

    :param name:
        Name of the DNS zone (without a terminating dot).

    :param resource_group:
        The resource group assigned to the DNS zone.

    :param etag:
        The etag of the zone. `Etags <https://docs.microsoft.com/en-us/azure/dns/dns-zones-records#etags>`__ are used
        to handle concurrent changes to the same resource safely.

    :param if_match:
        The etag of the DNS zone. Omit this value to always overwrite the current zone. Specify the last-seen etag
        value to prevent accidentally overwritting any concurrent changes.

    :param if_none_match:
        Set to '*' to allow a new DNS zone to be created, but to prevent updating an existing zone. Other values will
        be ignored.

    :param registration_virtual_networks:
        A list of references to virtual networks that register hostnames in this DNS zone. This is only when zone_type
        is Private. (requires `azure-mgmt-dns <https://pypi.python.org/pypi/azure-mgmt-dns>`__ >= 2.0.0rc1)

    :param resolution_virtual_networks:
        A list of references to virtual networks that resolve records in this DNS zone. This is only when zone_type is
        Private. (requires `azure-mgmt-dns <https://pypi.python.org/pypi/azure-mgmt-dns>`__ >= 2.0.0rc1)

    :param tags:
        A dictionary of strings can be passed as tag metadata to the DNS zone object.

    :param zone_type:
        The type of this DNS zone (Public or Private). Possible values include: 'Public', 'Private'. Default value: 'Public'
         (requires `azure-mgmt-dns <https://pypi.python.org/pypi/azure-mgmt-dns>`__ >= 2.0.0rc1)

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure DNS zone exists:
            azurerm.dns.zone.present:
                - name: contoso.com
                - resource_group: my_rg
                - zone_type: Private
                - registration_virtual_networks:
                  - /subscriptions/{{ sub }}/resourceGroups/my_rg/providers/Microsoft.Network/virtualNetworks/test_vnet
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

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

    zone = await hub.exec.azurerm.dns.zone.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in zone:
        action = "update"
        tag_changes = differ.deep_diff(zone.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # The zone_type parameter is only accessible in azure-mgmt-dns >=2.0.0rc1
        if zone.get("zone_type"):
            if zone.get("zone_type").lower() != zone_type.lower():
                ret["changes"]["zone_type"] = {
                    "old": zone["zone_type"],
                    "new": zone_type,
                }

            if zone_type.lower() == "private":
                # The registration_virtual_networks parameter is only accessible in azure-mgmt-dns >=2.0.0rc1
                if registration_virtual_networks and not isinstance(
                    registration_virtual_networks, list
                ):
                    ret[
                        "comment"
                    ] = "registration_virtual_networks must be supplied as a list of VNET ID paths!"
                    return ret
                reg_vnets = zone.get("registration_virtual_networks", [])
                remote_reg_vnets = sorted(
                    [vnet["id"].lower() for vnet in reg_vnets if "id" in vnet]
                )
                local_reg_vnets = sorted(
                    [vnet.lower() for vnet in registration_virtual_networks or []]
                )
                if local_reg_vnets != remote_reg_vnets:
                    ret["changes"]["registration_virtual_networks"] = {
                        "old": remote_reg_vnets,
                        "new": local_reg_vnets,
                    }

                # The resolution_virtual_networks parameter is only accessible in azure-mgmt-dns >=2.0.0rc1
                if resolution_virtual_networks and not isinstance(
                    resolution_virtual_networks, list
                ):
                    ret[
                        "comment"
                    ] = "resolution_virtual_networks must be supplied as a list of VNET ID paths!"
                    return ret
                res_vnets = zone.get("resolution_virtual_networks", [])
                remote_res_vnets = sorted(
                    [vnet["id"].lower() for vnet in res_vnets if "id" in vnet]
                )
                local_res_vnets = sorted(
                    [vnet.lower() for vnet in resolution_virtual_networks or []]
                )
                if local_res_vnets != remote_res_vnets:
                    ret["changes"]["resolution_virtual_networks"] = {
                        "old": remote_res_vnets,
                        "new": local_res_vnets,
                    }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "DNS zone {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "DNS zone {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "DNS zone {0} would be created.".format(name)
        ret["result"] = None
        return ret

    zone_kwargs = kwargs.copy()
    zone_kwargs.update(connection_auth)

    zone = await hub.exec.azurerm.dns.zone.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        etag=etag,
        if_match=if_match,
        if_none_match=if_none_match,
        registration_virtual_networks=registration_virtual_networks,
        resolution_virtual_networks=resolution_virtual_networks,
        tags=tags,
        zone_type=zone_type,
        **zone_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": zone}

    if "error" not in zone:
        ret["result"] = True
        ret["comment"] = f"DNS zone {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} DNS zone {1}! ({2})".format(
        action, name, zone.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a DNS zone does not exist in the resource group.

    :param name:
        Name of the DNS zone.

    :param resource_group:
        The resource group assigned to the DNS zone.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure zone absent:
            azurerm.dns.zone.absent:
              - name: test_machine
              - resource_group: test_group

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

    zone = await hub.exec.azurerm.dns.zone.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in zone:
        ret["result"] = True
        ret["comment"] = "DNS zone {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "DNS zone {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": zone,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.dns.zone.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "DNS zone {0} has been deleted.".format(name)
        ret["changes"] = {"old": zone, "new": {}}
        return ret

    ret["comment"] = "Failed to delete DNS zone {0}!".format(name)
    return ret
