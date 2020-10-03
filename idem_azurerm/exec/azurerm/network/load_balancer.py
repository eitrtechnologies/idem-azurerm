# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Load Balancer Execution Module

.. versionadded:: 1.0.0

.. versionchanged:: 4.0.0

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
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    List all load balancers within a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.load_balancer.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            load_balancers = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.load_balancers.list(resource_group_name=resource_group)
            )
        else:
            load_balancers = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.load_balancers.list_all()
            )

        for load_balancer in load_balancers:
            result[load_balancer["name"]] = load_balancer
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific load balancer.

    :param name: The name of the load balancer to query.

    :param resource_group: The resource group name assigned to the load balancer.

    CLI Example:

    .. code-block:: bash

        azurerm.network.load_balancer.get test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        load_balancer = netconn.load_balancers.get(
            load_balancer_name=name, resource_group_name=resource_group
        )

        result = load_balancer.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a load balancer within a specified resource group.

    :param name: The name of the load balancer to create.

    :param resource_group: The resource group name assigned to the load balancer.

    CLI Example:

    .. code-block:: bash

        azurerm.network.load_balancer.create_or_update test_name test_group

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

    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    if isinstance(kwargs.get("frontend_ip_configurations"), list):
        for idx in six_range(0, len(kwargs["frontend_ip_configurations"])):
            # Use Public IP Address name to link to the ID of an existing Public IP
            if "public_ip_address" in kwargs["frontend_ip_configurations"][idx]:
                pub_ip = await hub.exec.azurerm.network.public_ip_address.get(
                    ctx=ctx,
                    name=kwargs["frontend_ip_configurations"][idx]["public_ip_address"],
                    resource_group=resource_group,
                    **kwargs,
                )
                if "error" not in pub_ip:
                    kwargs["frontend_ip_configurations"][idx]["public_ip_address"] = {
                        "id": str(pub_ip["id"])
                    }
            # Use Subnet name to link to the ID of an existing Subnet
            elif "subnet" in kwargs["frontend_ip_configurations"][idx]:
                vnets = await hub.exec.azurerm.network.virtual_network.list(
                    ctx=ctx, resource_group=resource_group, **kwargs
                )
                if "error" not in vnets:
                    for vnet in vnets:
                        subnets = await hub.exec.azurerm.network.virtual_network.subnets_list(
                            ctx=ctx,
                            virtual_network=vnet,
                            resource_group=resource_group,
                            **kwargs,
                        )
                        if (
                            kwargs["frontend_ip_configurations"][idx]["subnet"]
                            in subnets
                        ):
                            kwargs["frontend_ip_configurations"][idx]["subnet"] = {
                                "id": str(
                                    subnets[
                                        kwargs["frontend_ip_configurations"][idx][
                                            "subnet"
                                        ]
                                    ]["id"]
                                )
                            }
                            break

    id_url = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/loadBalancers/{2}/{3}/{4}"

    if isinstance(kwargs.get("load_balancing_rules"), list):
        for idx in six_range(0, len(kwargs["load_balancing_rules"])):
            # Link to sub-objects which might be created at the same time as the load balancer
            if "frontend_ip_configuration" in kwargs["load_balancing_rules"][idx]:
                kwargs["load_balancing_rules"][idx]["frontend_ip_configuration"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "frontendIPConfigurations",
                        kwargs["load_balancing_rules"][idx][
                            "frontend_ip_configuration"
                        ],
                    )
                }
            if "backend_address_pool" in kwargs["load_balancing_rules"][idx]:
                kwargs["load_balancing_rules"][idx]["backend_address_pool"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "backendAddressPools",
                        kwargs["load_balancing_rules"][idx]["backend_address_pool"],
                    )
                }
            if "probe" in kwargs["load_balancing_rules"][idx]:
                kwargs["load_balancing_rules"][idx]["probe"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "probes",
                        kwargs["load_balancing_rules"][idx]["probe"],
                    )
                }

    if isinstance(kwargs.get("inbound_nat_rules"), list):
        for idx in six_range(0, len(kwargs["inbound_nat_rules"])):
            # Link to sub-objects which might be created at the same time as the load balancer
            if "frontend_ip_configuration" in kwargs["inbound_nat_rules"][idx]:
                kwargs["inbound_nat_rules"][idx]["frontend_ip_configuration"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "frontendIPConfigurations",
                        kwargs["inbound_nat_rules"][idx]["frontend_ip_configuration"],
                    )
                }

    if isinstance(kwargs.get("inbound_nat_pools"), list):
        for idx in six_range(0, len(kwargs["inbound_nat_pools"])):
            # Link to sub-objects which might be created at the same time as the load balancer
            if "frontend_ip_configuration" in kwargs["inbound_nat_pools"][idx]:
                kwargs["inbound_nat_pools"][idx]["frontend_ip_configuration"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "frontendIPConfigurations",
                        kwargs["inbound_nat_pools"][idx]["frontend_ip_configuration"],
                    )
                }

    if isinstance(kwargs.get("outbound_rules"), list):
        for idx in six_range(0, len(kwargs["outbound_rules"])):
            # Link to sub-objects which might be created at the same time as the load balancer
            if "frontend_ip_configuration" in kwargs["outbound_rules"][idx]:
                kwargs["outbound_rules"][idx]["frontend_ip_configuration"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "frontendIPConfigurations",
                        kwargs["outbound_rules"][idx]["frontend_ip_configuration"],
                    )
                }
            if "backend_address_pool" in kwargs["outbound_rules"][idx]:
                kwargs["outbound_rules"][idx]["backend_address_pool"] = {
                    "id": id_url.format(
                        kwargs.get("subscription_id"),
                        resource_group,
                        name,
                        "backendAddressPools",
                        kwargs["outbound_rules"][idx]["backend_address_pool"],
                    )
                }

    try:
        lbmodel = await hub.exec.azurerm.utils.create_object_model(
            "network", "LoadBalancer", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        load_balancer = netconn.load_balancers.create_or_update(
            resource_group_name=resource_group,
            load_balancer_name=name,
            parameters=lbmodel,
        )

        load_balancer.wait()
        result = load_balancer.result().as_dict()
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

    Deletes the specified load balancer.

    :param name: The name of the load balancer to delete.

    :param resource_group: The resource group name assigned to the load balancer.

    CLI Example:

    .. code-block:: bash

        azurerm.network.load_balancer.delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        load_balancer = netconn.load_balancers.delete(
            load_balancer_name=name, resource_group_name=resource_group
        )

        load_balancer.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def update_tags(hub, ctx, name, resource_group, tags=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Updates a load balancer tags.

    :param name: The name of the load balancer.

    :param resource_group: The resource group of the load balancer.

    :param tags: The resource tags to update.

    CLI Example:

    .. code-block:: bash

        azurerm.network.load_balancer.update_tags test_name test_group test_tags

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        load_balancer = netconn.load_balancers.update_tags(
            load_balancer_name=name, resource_group_name=resource_group, tags=tags
        )

        result = load_balancer.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
