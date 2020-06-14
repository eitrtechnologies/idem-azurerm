# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Security Group Execution Module

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

try:
    from six.moves import range as six_range
except ImportError:
    six_range = range

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def default_security_rule_get(
    hub, ctx, name, security_group, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Get details about a default security rule within a security group.

    :param name: The name of the security rule to query.

    :param security_group: The network security group containing the
        security rule.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.default_security_rule_get DenyAllOutBound testnsg testgroup

    """
    result = {}

    default_rules = await hub.exec.azurerm.network.network_security_group.default_security_rules_list(
        ctx=ctx, security_group=security_group, resource_group=resource_group, **kwargs
    )

    if isinstance(default_rules, dict) and "error" in default_rules:
        return default_rules

    try:
        for default_rule in default_rules:
            if default_rule["name"] == name:
                result = default_rule
        if not result:
            result = {
                "error": "Unable to find {0} in {1}!".format(name, security_group)
            }
    except KeyError as exc:
        log.error("Unable to find {0} in {1}!".format(name, security_group))
        result = {"error": str(exc)}

    return result


async def default_security_rules_list(
    hub, ctx, security_group, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    List default security rules within a security group.

    :param security_group: The network security group to query.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.default_security_rules_list testnsg testgroup

    """
    result = {}

    secgroup = await hub.exec.azurerm.network.network_security_group.get(
        ctx=ctx, security_group=security_group, resource_group=resource_group, **kwargs
    )

    if "error" in secgroup:
        return secgroup

    try:
        result = secgroup["default_security_rules"]
    except KeyError as exc:
        log.error("No default security rules found for {0}!".format(security_group))
        result = {"error": str(exc)}

    return result


async def security_rules_list(hub, ctx, security_group, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List security rules within a network security group.

    :param security_group: The network security group to query.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.security_rules_list testnsg testgroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secrules = netconn.security_rules.list(
            network_security_group_name=security_group,
            resource_group_name=resource_group,
        )
        result = await hub.exec.azurerm.utils.paged_object_to_list(secrules)
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def security_rule_create_or_update(
    hub,
    ctx,
    name,
    access,
    direction,
    priority,
    protocol,
    security_group,
    resource_group,
    source_address_prefix=None,
    destination_address_prefix=None,
    source_port_range=None,
    destination_port_range=None,
    source_address_prefixes=None,
    destination_address_prefixes=None,
    source_port_ranges=None,
    destination_port_ranges=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Create or update a security rule within a specified network security group.

    :param name: The name of the security rule to create.

    :param access:
        'allow' or 'deny'

    :param direction:
        'inbound' or 'outbound'

    :param priority:
        Integer between 100 and 4096 used for ordering rule application.

    :param protocol:
        'tcp', 'udp', or '*'

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

    :param security_group: The network security group containing the
        security rule.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.security_rule_create_or_update testrule1 allow outbound 101 tcp \
                  testnsg testgroup source_address_prefix='*' destination_address_prefix=internet \
                  source_port_range='*' destination_port_range='1-1024'

    """
    exclusive_params = [
        ("source_port_ranges", "source_port_range"),
        ("source_address_prefixes", "source_address_prefix"),
        ("destination_port_ranges", "destination_port_range"),
        ("destination_address_prefixes", "destination_address_prefix"),
    ]

    for params in exclusive_params:
        # pylint: disable=eval-used
        if not eval(params[0]) and not eval(params[1]):
            errmsg = "Either the {0} or {1} parameter must be provided!".format(
                params[0], params[1]
            )
            log.error(errmsg)
            return {"error": errmsg}
        # pylint: disable=eval-used
        if eval(params[0]):
            # pylint: disable=exec-used
            exec("{0} = None".format(params[1]))

    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        rulemodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "SecurityRule",
            name=name,
            access=access,
            direction=direction,
            priority=priority,
            protocol=protocol,
            source_port_ranges=source_port_ranges,
            source_port_range=source_port_range,
            source_address_prefixes=source_address_prefixes,
            source_address_prefix=source_address_prefix,
            destination_port_ranges=destination_port_ranges,
            destination_port_range=destination_port_range,
            destination_address_prefixes=destination_address_prefixes,
            destination_address_prefix=destination_address_prefix,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        secrule = netconn.security_rules.create_or_update(
            resource_group_name=resource_group,
            network_security_group_name=security_group,
            security_rule_name=name,
            security_rule_parameters=rulemodel,
        )
        secrule.wait()
        secrule_result = secrule.result()
        result = secrule_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def security_rule_delete(
    hub, ctx, security_rule, security_group, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Delete a security rule within a specified security group.

    :param name: The name of the security rule to delete.

    :param security_group: The network security group containing the
        security rule.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.security_rule_delete testrule1 testnsg testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secrule = netconn.security_rules.delete(
            network_security_group_name=security_group,
            resource_group_name=resource_group,
            security_rule_name=security_rule,
        )
        secrule.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def security_rule_get(
    hub, ctx, security_rule, security_group, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Get a security rule within a specified network security group.

    :param name: The name of the security rule to query.

    :param security_group: The network security group containing the
        security rule.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.security_rule_get testrule1 testnsg testgroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secrule = netconn.security_rules.get(
            network_security_group_name=security_group,
            resource_group_name=resource_group,
            security_rule_name=security_rule,
        )
        result = secrule.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a network security group.

    :param name: The name of the network security group to create.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.create_or_update testnsg testgroup

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

    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        secgroupmodel = await hub.exec.azurerm.utils.create_object_model(
            "network", "NetworkSecurityGroup", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        secgroup = netconn.network_security_groups.create_or_update(
            resource_group_name=resource_group,
            network_security_group_name=name,
            parameters=secgroupmodel,
        )
        secgroup.wait()
        secgroup_result = secgroup.result()
        result = secgroup_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a network security group within a resource group.

    :param name: The name of the network security group to delete.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.delete testnsg testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secgroup = netconn.network_security_groups.delete(
            resource_group_name=resource_group, network_security_group_name=name
        )
        secgroup.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a network security group within a resource group.

    :param name: The name of the network security group to query.

    :param resource_group: The resource group name assigned to the
        network security group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_group.get testnsg testgroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secgroup = netconn.network_security_groups.get(
            resource_group_name=resource_group, network_security_group_name=name
        )
        result = secgroup.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all network security groups within a resource group.

    :param resource_group: The resource group name to list network security \
        groups within.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_groups.list testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secgroups = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.network_security_groups.list(resource_group_name=resource_group)
        )
        for secgroup in secgroups:
            result[secgroup["name"]] = secgroup
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_all(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all network security groups within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_security_groups.list_all

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        secgroups = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.network_security_groups.list_all()
        )
        for secgroup in secgroups:
            result[secgroup["name"]] = secgroup
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
