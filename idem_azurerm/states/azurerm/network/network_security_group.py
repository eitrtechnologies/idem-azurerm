# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Security Group State Module

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
    "security_rule_present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.network_security_group.present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    tags=None,
    security_rules=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a network security group exists.

    :param name:
        Name of the network security group.

    :param resource_group:
        The resource group assigned to the network security group.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the network security group object.

    :param security_rules:
        A list of dictionaries representing valid SecurityRule objects. See the documentation for the
        security_rule_present state or security_rule_create_or_update execution module for more information on required
        and optional parameters for security rules. The rules are only managed if this parameter is present. When this
        parameter is absent, implemented rules will not be removed, and will merely become unmanaged.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure network security group exists:
            azurerm.network.network_security_group.present:
                - name: nsg1
                - resource_group: group1
                - security_rules:
                  - name: nsg1_rule1
                    priority: 100
                    protocol: tcp
                    access: allow
                    direction: outbound
                    source_address_prefix: virtualnetwork
                    destination_address_prefix: internet
                    source_port_range: '*'
                    destination_port_range: '*'
                  - name: nsg1_rule2
                    priority: 101
                    protocol: tcp
                    access: allow
                    direction: inbound
                    source_address_prefix: internet
                    destination_address_prefix: virtualnetwork
                    source_port_range: '*'
                    destination_port_ranges:
                      - '80'
                      - '443'
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

    nsg = await hub.exec.azurerm.network.network_security_group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in nsg:
        action = "update"
        tag_changes = differ.deep_diff(nsg.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if security_rules:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                nsg.get("security_rules", []), security_rules
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"security_rules" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["security_rules"] = comp_ret["changes"]

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Network security group {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Network security group {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Network security group {0} would be created.".format(name)
        ret["result"] = None
        return ret

    nsg_kwargs = kwargs.copy()
    nsg_kwargs.update(connection_auth)

    if action == "create" or len(ret["changes"]) > 1 or not tag_changes:
        nsg = await hub.exec.azurerm.network.network_security_group.create_or_update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            tags=tags,
            security_rules=security_rules,
            **nsg_kwargs,
        )

    # no idea why create_or_update doesn't work for tags
    if action == "update" and tag_changes:
        nsg = await hub.exec.azurerm.network.network_security_group.update_tags(
            ctx, name=name, resource_group=resource_group, tags=tags, **nsg_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": nsg}

    if "error" not in nsg:
        ret["result"] = True
        ret["comment"] = f"Network security group {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} network security group {1}! ({2})".format(
        action, name, nsg.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a network security group does not exist in the resource group.

    :param name:
        Name of the network security group.

    :param resource_group:
        The resource group assigned to the network security group.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure nsg is absent:
            azurerm.network.network_security_group.absent:
                - name: nsg1
                - resource_group: group1

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

    nsg = await hub.exec.azurerm.network.network_security_group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in nsg:
        ret["result"] = True
        ret["comment"] = "Network security group {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Network security group {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": nsg,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.network_security_group.delete(
        ctx, name=name, resource_group=resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Network security group {0} has been deleted.".format(name)
        ret["changes"] = {"old": nsg, "new": {}}
        return ret

    ret["comment"] = "Failed to delete network security group {0}!".format(name)
    return ret


async def security_rule_present(
    hub,
    ctx,
    name,
    access,
    direction,
    priority,
    protocol,
    security_group,
    resource_group,
    destination_address_prefix=None,
    destination_port_range=None,
    source_address_prefix=None,
    source_port_range=None,
    description=None,
    destination_address_prefixes=None,
    destination_port_ranges=None,
    source_address_prefixes=None,
    source_port_ranges=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a security rule exists.

    :param name:
        Name of the security rule.

    :param access:
        'allow' or 'deny'

    :param direction:
        'inbound' or 'outbound'

    :param priority:
        Integer between 100 and 4096 used for ordering rule application.

    :param protocol:
        'tcp', 'udp', or '*'

    :param security_group:
        The name of the existing network security group to contain the security rule.

    :param resource_group:
        The resource group assigned to the network security group.

    :param description:
        Optional description of the security rule.

    :param destination_address_prefix:
        The CIDR or destination IP range. Asterix '*' can also be used to match all destination IPs.
        Default tags such as 'VirtualNetwork', 'AzureLoadBalancer' and 'Internet' can also be used.
        If this is an ingress rule, specifies where network traffic originates from.

    :param destination_port_range:
        The destination port or range. Integer or range between 0 and 65535. Asterix '*'
        can also be used to match all ports.

    :param source_address_prefix:
        The CIDR or source IP range. Asterix '*' can also be used to match all source IPs.
        Default tags such as 'VirtualNetwork', 'AzureLoadBalancer' and 'Internet' can also be used.
        If this is an ingress rule, specifies where network traffic originates from.

    :param source_port_range:
        The source port or range. Integer or range between 0 and 65535. Asterix '*'
        can also be used to match all ports.

    :param destination_address_prefixes:
        A list of destination_address_prefix values. This parameter overrides destination_address_prefix
        and will cause any value entered there to be ignored.

    :param destination_port_ranges:
        A list of destination_port_range values. This parameter overrides destination_port_range
        and will cause any value entered there to be ignored.

    :param source_address_prefixes:
        A list of source_address_prefix values. This parameter overrides source_address_prefix
        and will cause any value entered there to be ignored.

    :param source_port_ranges:
        A list of source_port_range values. This parameter overrides source_port_range
        and will cause any value entered there to be ignored.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure security rule exists:
            azurerm.network.network_security_group.security_rule_present:
                - name: nsg1_rule2
                - security_group: nsg1
                - resource_group: group1
                - priority: 101
                - protocol: tcp
                - access: allow
                - direction: inbound
                - source_address_prefix: internet
                - destination_address_prefix: virtualnetwork
                - source_port_range: '*'
                - destination_port_ranges:
                  - '80'
                  - '443'

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

    exclusive_params = [
        ("source_port_ranges", "source_port_range"),
        ("source_address_prefixes", "source_address_prefix"),
        ("destination_port_ranges", "destination_port_range"),
        ("destination_address_prefixes", "destination_address_prefix"),
    ]

    for params in exclusive_params:
        # pylint: disable=eval-used
        if not eval(params[0]) and not eval(params[1]):
            ret["comment"] = "Either the {0} or {1} parameter must be provided!".format(
                params[0], params[1]
            )
            return ret
        # pylint: disable=eval-used
        if eval(params[0]):
            # pylint: disable=eval-used
            if not isinstance(eval(params[0]), list):
                ret["comment"] = "The {0} parameter must be a list!".format(params[0])
                return ret
            # pylint: disable=exec-used
            exec("{0} = None".format(params[1]))

    rule = await hub.exec.azurerm.network.network_security_group.security_rule_get(
        ctx,
        name,
        security_group,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in rule:
        action = "update"

        # access changes
        if access.capitalize() != rule.get("access"):
            ret["changes"]["access"] = {"old": rule.get("access"), "new": access}

        # description changes
        if description != rule.get("description"):
            ret["changes"]["description"] = {
                "old": rule.get("description"),
                "new": description,
            }

        # direction changes
        if direction.capitalize() != rule.get("direction"):
            ret["changes"]["direction"] = {
                "old": rule.get("direction"),
                "new": direction,
            }

        # priority changes
        if int(priority) != rule.get("priority"):
            ret["changes"]["priority"] = {"old": rule.get("priority"), "new": priority}

        # protocol changes
        if protocol.lower() != rule.get("protocol", "").lower():
            ret["changes"]["protocol"] = {"old": rule.get("protocol"), "new": protocol}

        # destination_port_range changes
        if destination_port_range != rule.get("destination_port_range"):
            ret["changes"]["destination_port_range"] = {
                "old": rule.get("destination_port_range"),
                "new": destination_port_range,
            }

        # source_port_range changes
        if source_port_range != rule.get("source_port_range"):
            ret["changes"]["source_port_range"] = {
                "old": rule.get("source_port_range"),
                "new": source_port_range,
            }

        # destination_port_ranges changes
        if sorted(destination_port_ranges or []) != sorted(
            rule.get("destination_port_ranges", [])
        ):
            ret["changes"]["destination_port_ranges"] = {
                "old": rule.get("destination_port_ranges"),
                "new": destination_port_ranges,
            }

        # source_port_ranges changes
        if sorted(source_port_ranges or []) != sorted(
            rule.get("source_port_ranges", [])
        ):
            ret["changes"]["source_port_ranges"] = {
                "old": rule.get("source_port_ranges"),
                "new": source_port_ranges,
            }

        # destination_address_prefix changes
        if (destination_address_prefix or "").lower() != rule.get(
            "destination_address_prefix", ""
        ).lower():
            ret["changes"]["destination_address_prefix"] = {
                "old": rule.get("destination_address_prefix"),
                "new": destination_address_prefix,
            }

        # source_address_prefix changes
        if (source_address_prefix or "").lower() != rule.get(
            "source_address_prefix", ""
        ).lower():
            ret["changes"]["source_address_prefix"] = {
                "old": rule.get("source_address_prefix"),
                "new": source_address_prefix,
            }

        # destination_address_prefixes changes
        if sorted(destination_address_prefixes or []) != sorted(
            rule.get("destination_address_prefixes", [])
        ):
            if len(destination_address_prefixes or []) != len(
                rule.get("destination_address_prefixes", [])
            ):
                ret["changes"]["destination_address_prefixes"] = {
                    "old": rule.get("destination_address_prefixes"),
                    "new": destination_address_prefixes,
                }
            else:
                local_dst_addrs, remote_dst_addrs = (
                    sorted(destination_address_prefixes),
                    sorted(rule.get("destination_address_prefixes")),
                )
                for idx, local_dst_addr in enumerate(local_dst_addrs):
                    if local_dst_addr.lower() != remote_dst_addrs[idx].lower():
                        ret["changes"]["destination_address_prefixes"] = {
                            "old": rule.get("destination_address_prefixes"),
                            "new": destination_address_prefixes,
                        }
                        break

        # source_address_prefixes changes
        if sorted(source_address_prefixes or []) != sorted(
            rule.get("source_address_prefixes", [])
        ):
            if len(source_address_prefixes or []) != len(
                rule.get("source_address_prefixes", [])
            ):
                ret["changes"]["source_address_prefixes"] = {
                    "old": rule.get("source_address_prefixes"),
                    "new": source_address_prefixes,
                }
            else:
                local_src_addrs, remote_src_addrs = (
                    sorted(source_address_prefixes),
                    sorted(rule.get("source_address_prefixes")),
                )
                for idx, local_src_addr in enumerate(local_src_addrs):
                    if local_src_addr.lower() != remote_src_addrs[idx].lower():
                        ret["changes"]["source_address_prefixes"] = {
                            "old": rule.get("source_address_prefixes"),
                            "new": source_address_prefixes,
                        }
                        break

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Security rule {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Security rule {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Security rule {0} would be created.".format(name)
        ret["result"] = None
        return ret

    rule_kwargs = kwargs.copy()
    rule_kwargs.update(connection_auth)

    rule = await hub.exec.azurerm.network.network_security_group.security_rule_create_or_update(
        ctx=ctx,
        name=name,
        access=access,
        description=description,
        direction=direction,
        priority=priority,
        protocol=protocol,
        security_group=security_group,
        resource_group=resource_group,
        destination_address_prefix=destination_address_prefix,
        destination_address_prefixes=destination_address_prefixes,
        destination_port_range=destination_port_range,
        destination_port_ranges=destination_port_ranges,
        source_address_prefix=source_address_prefix,
        source_address_prefixes=source_address_prefixes,
        source_port_range=source_port_range,
        source_port_ranges=source_port_ranges,
        **rule_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": rule}

    if "error" not in rule:
        ret["result"] = True
        ret["comment"] = f"Security rule {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} security rule {1}! ({2})".format(
        action, name, rule.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def security_rule_absent(
    hub, ctx, name, security_group, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Ensure a security rule does not exist in the network security group.

    :param name:
        Name of the security rule.

    :param security_group:
        The network security group containing the security rule.

    :param resource_group:
        The resource group assigned to the network security group.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure security rule absent:
            azurerm.network.network_security_group.security_rule_absent:
                - name: nsg1_rule2
                - security_group: nsg1
                - resource_group: group1

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

    rule = await hub.exec.azurerm.network.network_security_group.security_rule_get(
        ctx,
        name,
        security_group,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in rule:
        ret["result"] = True
        ret["comment"] = "Security rule {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Security rule {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": rule,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.network_security_group.security_rule_delete(
        ctx, name, security_group, resource_group, **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Security rule {0} has been deleted.".format(name)
        ret["changes"] = {"old": rule, "new": {}}
        return ret

    ret["comment"] = "Failed to delete security rule {0}!".format(name)
    return ret
