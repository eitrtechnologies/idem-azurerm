# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Bastion Host State Module

.. versionadded:: 4.0.0

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
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.public_ip_address.present",
            "states.azurerm.network.virtual_network.present",
            "states.azurerm.network.virtual_network.subnet_present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    ip_configuration,
    dns_name=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Ensure a Bastion Host exists.

    :param name: The name of the Bastion Host.

    :param resource_group: The resource group of the Bastion Host.

    :param ip_configuration: A dictionary representing a valid BastionHostIPConfiguration object. Valid parameters
        include the following:

        - ``name``: (Required) The name of the BastionHostIPConfiguration resource that is unique within the resource
          group.
        - ``public_ip_address``: (Required) The resource ID of the public IP address which will be assigned to the
          Bastion Host object. The public ip address must have a "Standard" sku.
        - ``subnet``: (Required) The resource ID of the "AzureBastionSubnet" subnet which will be used by the Bastion
          Host.
        - ``private_ip_allocation_method``: (Optional) The Private IP allocation method. Possible values are: 'Static'
          and 'Dynamic'.

    :param dns_name: FQDN for the endpoint on which bastion host is accessible.

    :param tags: A dictionary of strings can be passed as tag metadata to the Bastion Host object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure bastion host exists:
            azurerm.network.bastion_host.present:
                - name: test_host
                - resource_group: test_group
                - ip_configuration:
                    name: test_config
                    public_ip_address: pub_ip_id
                    subnet: subnet_id
                - tags:
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

    try:
        ip_configuration["public_ip_address"] = {
            "id": ip_configuration["public_ip_address"]
        }
    except KeyError as exc:
        log.error(
            "The resource ID of a public IP address must be declared within the ``ip_configration`` parameter."
        )
        result = {
            "error": "The resource ID of a public IP address must be declared within the ``ip_configration`` parameter."
        }
        return result

    try:
        ip_configuration["subnet"] = {"id": ip_configuration["subnet"]}
    except KeyError as exc:
        log.error(
            "The resource ID of the AzureBastionSubnet subnet must be declared within the ``ip_configration`` parameter."
        )
        result = {
            "error": "The resource ID of a AzureBastionSubnet subnet must be declared within the ``ip_configration`` parameter."
        }
        return result

    host = await hub.exec.azurerm.network.bastion_host.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in host:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(host.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # dns_name changes
        if dns_name is not None:
            if dns_name.lower() != host.get("dns_name").lower():
                ret["changes"]["dns_name"] = {
                    "old": host.get("dns_name"),
                    "new": dns_name,
                }

        # ip_configuration changes
        for key, value in ip_configuration.items():
            if value != (host.get("ip_configurations", [])[0]).get(key):
                ret["changes"]["ip_configurations"] = {
                    "new": [ip_configuration],
                    "old": host.get("ip_configurations", []),
                }
                break

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Bastion Host {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Bastion Host {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Bastion Host {0} would be created.".format(name)
        ret["result"] = None
        return ret

    host_kwargs = kwargs.copy()
    host_kwargs.update(connection_auth)

    host = await hub.exec.azurerm.network.bastion_host.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        ip_configuration=ip_configuration,
        dns_name=dns_name,
        tags=tags,
        **host_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": host}

    if "error" not in host:
        ret["result"] = True
        ret["comment"] = f"Bastion Host {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Bastion Host {1}! ({2})".format(
        action, name, host.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Ensure the specified Bastion Host does not exist in the resource group.

    :param name: The name of the Bastion Host.

    :param resource_group: The resource group assigned to the Bastion Host.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure bastion host absent:
            azurerm.network.bastion_host.absent:
                - name: test_host
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

    host = await hub.exec.azurerm.network.bastion_host.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in host:
        ret["result"] = True
        ret["comment"] = "Bastion Host {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Bastion Host {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": host,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.bastion_host.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Bastion Host {0} has been deleted.".format(name)
        ret["changes"] = {"old": host, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Bastion Host {0}!".format(name)
    return ret
