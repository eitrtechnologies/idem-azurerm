# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Route Execution Module

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

log = logging.getLogger(__name__)


async def filter_rule_delete(hub, ctx, name, route_filter, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a route filter rule.

    :param name: The route filter rule to delete.

    :param route_filter: The route filter containing the rule.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_rule_delete test-rule test-filter testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        rule = netconn.route_filter_rules.delete(
            resource_group_name=resource_group,
            route_filter_name=route_filter,
            rule_name=name,
        )
        rule.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def filter_rule_get(hub, ctx, name, route_filter, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific route filter rule.

    :param name: The route filter rule to query.

    :param route_filter: The route filter containing the rule.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_rule_get test-rule test-filter testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        rule = netconn.route_filter_rules.get(
            resource_group_name=resource_group,
            route_filter_name=route_filter,
            rule_name=name,
        )

        result = rule.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def filter_rule_create_or_update(
    hub, ctx, name, access, communities, route_filter, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Create or update a rule within a specified route filter.

    :param name: The name of the rule to create.

    :param access: The access type of the rule. Valid values are 'Allow' and 'Deny'.

    :param communities: A list of BGP communities to filter on.

    :param route_filter: The name of the route filter containing the rule.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_rule_create_or_update \
                  test-rule allow "['12076:51006']" test-filter testgroup

    """
    if not isinstance(communities, list):
        log.error("The communities parameter must be a list of strings!")
        return {"error": "The communities parameter must be a list of strings!"}

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
        rule_model = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "RouteFilterRule",
            access=access,
            communities=communities,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        rule = netconn.route_filter_rules.create_or_update(
            resource_group_name=resource_group,
            route_filter_name=route_filter,
            rule_name=name,
            route_filter_rule_parameters=rule_model,
        )
        rule.wait()
        rule_result = rule.result()
        result = rule_result.as_dict()
    except CloudError as exc:
        message = str(exc)
        if kwargs.get("subscription_id") == str(message).strip():
            message = "Subscription not authorized for this operation!"
        await hub.exec.azurerm.utils.log_cloud_error("network", message, **kwargs)
        result = {"error": message}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def filter_rules_list(hub, ctx, route_filter, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all routes within a route filter.

    :param route_filter: The route filter to query.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_rules_list test-filter testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        rules = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.route_filter_rules.list_by_route_filter(
                resource_group_name=resource_group, route_filter_name=route_filter
            )
        )

        for rule in rules:
            result[rule["name"]] = rule
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def filter_delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a route filter.

    :param name: The name of the route filter to delete.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_delete test-filter testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        route_filter = netconn.route_filters.delete(
            route_filter_name=name, resource_group_name=resource_group
        )
        route_filter.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def filter_get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific route filter.

    :param name: The name of the route table to query.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_get test-filter testgroup

    """
    expand = kwargs.get("expand")

    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        route_filter = netconn.route_filters.get(
            route_filter_name=name, resource_group_name=resource_group, expand=expand
        )
        result = route_filter.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def filter_create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a route filter within a specified resource group.

    :param name: The name of the route filter to create.

    :param resource_group: The resource group name assigned to the
        route filter.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filter_create_or_update test-filter testgroup

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
        rt_filter_model = await hub.exec.azurerm.utils.create_object_model(
            "network", "RouteFilter", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        rt_filter = netconn.route_filters.create_or_update(
            resource_group_name=resource_group,
            route_filter_name=name,
            route_filter_parameters=rt_filter_model,
        )
        rt_filter.wait()
        rt_result = rt_filter.result()
        result = rt_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def filters_list(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all route filters within a resource group.

    :param resource_group: The resource group name to list route
        filters within.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filters_list testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        filters = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.route_filters.list_by_resource_group(
                resource_group_name=resource_group
            )
        )

        for route_filter in filters:
            result[route_filter["name"]] = route_filter
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def filters_list_all(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all route filters within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.filters_list_all

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        filters = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.route_filters.list()
        )

        for route_filter in filters:
            result[route_filter["name"]] = route_filter
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, route_table, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a route from a route table.

    :param name: The route to delete.

    :param route_table: The route table containing the route.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.delete test-rt test-rt-table testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        route = netconn.routes.delete(
            resource_group_name=resource_group,
            route_table_name=route_table,
            route_name=name,
        )
        route.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, route_table, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific route.

    :param name: The route to query.

    :param route_table: The route table containing the route.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.get test-rt test-rt-table testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        route = netconn.routes.get(
            resource_group_name=resource_group,
            route_table_name=route_table,
            route_name=name,
        )

        result = route.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(
    hub,
    ctx,
    name,
    address_prefix,
    next_hop_type,
    route_table,
    resource_group,
    next_hop_ip_address=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Create or update a route within a specified route table.

    :param name: The name of the route to create.

    :param address_prefix: The destination CIDR to which the route applies.

    :param next_hop_type: The type of Azure hop the packet should be sent to. Possible values are:
        'VirtualNetworkGateway', 'VnetLocal', 'Internet', 'VirtualAppliance', and 'None'.

    :param next_hop_ip_address: Optional IP address to which packets should be forwarded. Next hop
        values are only allowed in routes where the next_hop_type is 'VirtualAppliance'.

    :param route_table: The name of the route table containing the route.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.create_or_update test-rt '10.0.0.0/8' test-rt-table testgroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        rt_model = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "Route",
            address_prefix=address_prefix,
            next_hop_type=next_hop_type,
            next_hop_ip_address=next_hop_ip_address,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        route = netconn.routes.create_or_update(
            resource_group_name=resource_group,
            route_table_name=route_table,
            route_name=name,
            route_parameters=rt_model,
        )
        route.wait()
        rt_result = route.result()
        result = rt_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def routes_list(hub, ctx, route_table, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all routes within a route table.

    :param route_table: The route table to query.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.routes_list test-rt-table testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        routes = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.routes.list(
                resource_group_name=resource_group, route_table_name=route_table
            )
        )

        for route in routes:
            result[route["name"]] = route
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def table_delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a route table.

    :param name: The name of the route table to delete.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.table_delete test-rt-table testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        table = netconn.route_tables.delete(
            route_table_name=name, resource_group_name=resource_group
        )
        table.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def table_get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific route table.

    :param name: The name of the route table to query.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.table_get test-rt-table testgroup

    """
    expand = kwargs.get("expand")

    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        table = netconn.route_tables.get(
            route_table_name=name, resource_group_name=resource_group, expand=expand
        )
        result = table.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def table_create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a route table within a specified resource group.

    :param name: The name of the route table to create.

    :param resource_group: The resource group name assigned to the
        route table.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.table_create_or_update test-rt-table testgroup

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
        rt_tbl_model = await hub.exec.azurerm.utils.create_object_model(
            "network", "RouteTable", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        table = netconn.route_tables.create_or_update(
            resource_group_name=resource_group,
            route_table_name=name,
            parameters=rt_tbl_model,
        )
        table.wait()
        tbl_result = table.result()
        result = tbl_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def tables_list(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all route tables within a resource group.

    :param resource_group: The resource group name to list route
        tables within.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.tables_list testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        tables = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.route_tables.list(resource_group_name=resource_group)
        )

        for table in tables:
            result[table["name"]] = table
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def tables_list_all(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all route tables within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.network.route.tables_list_all

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        tables = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.route_tables.list_all()
        )

        for table in tables:
            result[table["name"]] = table
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
