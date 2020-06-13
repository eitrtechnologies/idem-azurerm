# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Availability Set State Module

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

        Ensure availability set exists:
            azurerm.compute.availability_set.present:
                - name: my_avail_set
                - resource_group: my_rg
                - virtual_machines:
                    - my_vm1
                    - my_vm2
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure availability set is absent:
            azurerm.compute.availability_set.absent:
                - name: other_avail_set
                - resource_group: my_rg
                - connection_auth: {{ profile }}

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
    tags=None,
    platform_update_domain_count=None,
    platform_fault_domain_count=None,
    virtual_machines=None,
    sku=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure an availability set exists.

    :param name:
        Name of the availability set.

    :param resource_group:
        The resource group assigned to the availability set.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the availability set object.

    :param platform_update_domain_count:
        An optional parameter which indicates groups of virtual machines and underlying physical hardware that can be
        rebooted at the same time.

    :param platform_fault_domain_count:
        An optional parameter which defines the group of virtual machines that share a common power source and network
        switch.

    :param virtual_machines:
        A list of names of existing virtual machines to be included in the availability set.

    :param sku:
        The availability set SKU, which specifies whether the availability set is managed or not. Possible values are
        'Aligned' or 'Classic'. An 'Aligned' availability set is managed, 'Classic' is not.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure availability set exists:
            azurerm.compute.availability_set.present:
                - name: aset1
                - resource_group: group1
                - platform_update_domain_count: 5
                - platform_fault_domain_count: 3
                - sku: aligned
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

    aset = await hub.exec.azurerm.compute.availability_set.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in aset:
        action = "update"
        tag_changes = differ.deep_diff(aset.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if platform_update_domain_count and (
            int(platform_update_domain_count)
            != aset.get("platform_update_domain_count")
        ):
            ret["changes"]["platform_update_domain_count"] = {
                "old": aset.get("platform_update_domain_count"),
                "new": platform_update_domain_count,
            }

        if platform_fault_domain_count and (
            int(platform_fault_domain_count) != aset.get("platform_fault_domain_count")
        ):
            ret["changes"]["platform_fault_domain_count"] = {
                "old": aset.get("platform_fault_domain_count"),
                "new": platform_fault_domain_count,
            }

        if sku and (sku["name"] != aset.get("sku", {}).get("name")):
            ret["changes"]["sku"] = {"old": aset.get("sku"), "new": sku}

        if virtual_machines:
            if not isinstance(virtual_machines, list):
                ret["comment"] = "Virtual machines must be supplied as a list!"
                return ret
            aset_vms = aset.get("virtual_machines", [])
            remote_vms = sorted(
                [vm["id"].split("/")[-1].lower() for vm in aset_vms if "id" in aset_vms]
            )
            local_vms = sorted([vm.lower() for vm in virtual_machines or []])
            if local_vms != remote_vms:
                ret["changes"]["virtual_machines"] = {
                    "old": aset_vms,
                    "new": virtual_machines,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Availability set {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Availability set {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "virtual_machines": virtual_machines,
                "platform_update_domain_count": platform_update_domain_count,
                "platform_fault_domain_count": platform_fault_domain_count,
                "sku": sku,
                "tags": tags,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Availability set {0} would be created.".format(name)
        ret["result"] = None
        return ret

    aset_kwargs = kwargs.copy()
    aset_kwargs.update(connection_auth)

    aset = await hub.exec.azurerm.compute.availability_set.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        virtual_machines=virtual_machines,
        platform_update_domain_count=platform_update_domain_count,
        platform_fault_domain_count=platform_fault_domain_count,
        sku=sku,
        tags=tags,
        **aset_kwargs,
    )

    if "error" not in aset:
        ret["result"] = True
        ret["comment"] = f"Availability set {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} availability set {1}! ({2})".format(
        action, name, aset.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure an availability set does not exist in a resource group.

    :param name:
        Name of the availability set.

    :param resource_group:
        Name of the resource group containing the availability set.

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

    aset = await hub.exec.azurerm.compute.availability_set.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in aset:
        ret["result"] = True
        ret["comment"] = "Availability set {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Availability set {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": aset,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.compute.availability_set.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Availability set {0} has been deleted.".format(name)
        ret["changes"] = {"old": aset, "new": {}}
        return ret

    ret["comment"] = "Failed to delete availability set {0}!".format(name)
    return ret
