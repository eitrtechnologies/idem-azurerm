# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Interface Execution Module

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


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a network interface.

    :param name: The name of the network interface to delete.

    :param resource_group: The resource group name assigned to the network interface.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.delete test-iface0 testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nic = netconn.network_interfaces.delete(
            network_interface_name=name, resource_group_name=resource_group
        )

        nic.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific network interface.

    :param name: The name of the network interface to query.

    :param resource_group: The resource group name assigned to the network interface.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.get test-iface0 testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nic = netconn.network_interfaces.get(
            network_interface_name=name, resource_group_name=resource_group
        )

        result = nic.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(
    hub, ctx, name, ip_configurations, subnet, virtual_network, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Create or update a network interface within a specified resource group.

    :param name: The name of the network interface to create.

    :param ip_configurations: A list of dictionaries representing valid NetworkInterfaceIPConfiguration objects. The
        ``name`` key is required at minimum. At least one IP Configuration must be present.

    :param subnet: The name of the subnet assigned to the network interface.

    :param virtual_network: The name of the virtual network assigned to the subnet.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.create_or_update test-iface0 [{'name': 'testipconfig1'}] testsubnet
                                                           testvnet testgroup

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

    # Use NSG name to link to the ID of an existing NSG.
    if kwargs.get("network_security_group"):
        nsg = await hub.exec.azurerm.network.network_security_group.get(
            ctx=ctx,
            name=kwargs["network_security_group"],
            resource_group=resource_group,
            **kwargs,
        )
        if "error" not in nsg:
            kwargs["network_security_group"] = {"id": str(nsg["id"])}

    # Loop through IP Configurations and build each dictionary to pass to model creation.
    if isinstance(ip_configurations, list):
        subnet = await hub.exec.azurerm.network.virtual_network.subnet_get(
            ctx=ctx,
            name=subnet,
            virtual_network=virtual_network,
            resource_group=resource_group,
            **kwargs,
        )
        if "error" not in subnet:
            subnet = {"id": str(subnet["id"])}
            for ipconfig in ip_configurations:
                if "name" in ipconfig:
                    ipconfig["subnet"] = subnet
                    if isinstance(
                        ipconfig.get("application_gateway_backend_address_pools"), list
                    ):
                        # TODO: Add ID lookup for referenced object names
                        pass
                    if isinstance(
                        ipconfig.get("load_balancer_backend_address_pools"), list
                    ):
                        # TODO: Add ID lookup for referenced object names
                        pass
                    if isinstance(
                        ipconfig.get("load_balancer_inbound_nat_rules"), list
                    ):
                        # TODO: Add ID lookup for referenced object names
                        pass
                    if isinstance(ipconfig.get("application_security_groups"), list):
                        # TODO: Add ID lookup for referenced object names
                        pass
                    if isinstance(ipconfig.get("virtual_network_taps"), list):
                        # TODO: Add ID lookup for referenced object names
                        pass
                    if ipconfig.get("public_ip_address") and not isinstance(
                        ipconfig.get("public_ip_address"), dict
                    ):
                        pub_ip = await hub.exec.azurerm.network.public_ip_address.get(
                            ctx=ctx,
                            name=ipconfig["public_ip_address"],
                            resource_group=resource_group,
                            **kwargs,
                        )
                        if "error" not in pub_ip:
                            ipconfig["public_ip_address"] = {"id": str(pub_ip["id"])}

    try:
        nicmodel = await hub.exec.azurerm.utils.create_object_model(
            "network", "NetworkInterface", ip_configurations=ip_configurations, **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        nic = netconn.network_interfaces.create_or_update(
            resource_group_name=resource_group,
            network_interface_name=name,
            parameters=nicmodel,
        )

        nic.wait()
        result = nic.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    List all network interfaces within a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            nics = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.network_interfaces.list(resource_group_name=resource_group)
            )
        else:
            nics = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.network_interfaces.list_all()
            )

        for nic in nics:
            result[nic["name"]] = nic
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_effective_route_table(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get all route tables for a specific network interface.

    :param name: The name of the network interface to query.

    :param resource_group: The resource group name assigned to the network interface.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.get_effective_route_table test-iface0 testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nic = netconn.network_interfaces.get_effective_route_table(
            network_interface_name=name, resource_group_name=resource_group
        )

        nic.wait()
        tables = nic.result().as_dict()
        result = tables["value"]
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_effective_network_security_groups(
    hub, ctx, name, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Get all network security groups applied to a specific network interface.

    :param name: The name of the network interface to query.

    :param resource_group: The resource group name assigned to the network interface.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.list_effective_network_security_groups test-iface0 testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        groups = netconn.network_interfaces.list_effective_network_security_groups(
            network_interface_name=name, resource_group_name=resource_group
        )

        nic.wait()
        groups = nic.result().as_dict()
        result = groups["value"]
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_virtual_machine_scale_set_vm_network_interfaces(
    hub, ctx, scale_set, vm_index, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Get information about all network interfaces in a specific virtual machine within a scale set.

    :param scale_set: The name of the scale set to query.

    :param vm_index: The virtual machine index.

    :param resource_group: The resource group name assigned to the scale set.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.list_virtual_machine_scale_set_vm_network_interfaces testset testvm testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nics = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.network_interfaces.list_virtual_machine_scale_set_vm_network_interfaces(
                virtual_machine_scale_set_name=scale_set,
                virtualmachine_index=vm_index,
                resource_group_name=resource_group,
            )
        )

        for nic in nics:
            result[nic["name"]] = nic
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def virtual_machine_scale_set_network_interfaces(
    hub, ctx, scale_set, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Get information about all network interfaces within a scale set.

    :param scale_set: The name of the scale set to query.

    :param resource_group: The resource group name assigned to the scale set.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.list_virtual_machine_scale_set_vm_network_interfaces testset testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nics = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.network_interfaces.list_virtual_machine_scale_set_network_interfaces(
                virtual_machine_scale_set_name=scale_set,
                resource_group_name=resource_group,
            )
        )

        for nic in nics:
            result[nic["name"]] = nic
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_virtual_machine_scale_set_network_interface(
    hub, ctx, name, scale_set, vm_index, resource_group, expand=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Get information about a specfic network interface within a scale set.

    :param name: The name of the network interface to query.

    :param scale_set: The name of the scale set containing the interface.

    :param vm_index: The virtual machine index.

    :param resource_group: The resource group name assigned to the scale set.

    :param expand: Expands referenced resources.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.get_virtual_machine_scale_set_network_interface test-iface0 testset
                                                                                          testvm testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        nic = netconn.network_interfaces.list_virtual_machine_scale_set_vm_network_interfaces(
            network_interface_name=name,
            virtual_machine_scale_set_name=scale_set,
            virtualmachine_index=vm_index,
            resource_group_name=resource_group,
            exapnd=expand,
        )

        result = nic.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update_tags(
    hub, ctx, name, resource_group, tags, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Updates a network interface tags.

    :param name: The name of the network interface.

    :param resource_group: The name of the resource group.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.network_interface.update_tags test_name test_group '{"owner": "me"}'

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        nic = netconn.network_interfaces.update_tags(
            network_interface_name=name, resource_group_name=resource_group, tags=tags,
        )

        result = nic.as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
