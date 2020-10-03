# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Gateway Execution Module

.. versionadded:: 1.0.0

.. versionchanged: 3.0.0, 4.0.0

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
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def connection_create_or_update(
    hub, ctx, name, resource_group, virtual_network_gateway, connection_type, **kwargs
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Creates or updates a virtual network gateway connection.

    :param name: The name of the virtual network gateway connection to create or update.

    :param resource_group: The name of the resource group.

    :param virtual_network_gateway: The name of the virtual network gateway that will be the first endpoint of the
        connection. This is immutable once set.

    :param connection_type: Gateway connection type. Possible values include: 'IPsec', 'Vnet2Vnet', and 'ExpressRoute'.
        This is immutable once set.

    A second endpoint must be passed as a keyword argument. The second endpoint will be immutable once set. The
    following are possible second endpoints for the connection:

      - If the connection type is "Vnet2Vnet", then the name of a second virtual network gateway must be passed as the
        ``virtual_network_gateway2`` kwarg. If that second gateway has a different resource group than the resource
        group specified within the ``resource_group`` parameter, then it must be specified within ``vgw2_group`` kwarg.
        Otherwise, the resource_group within the ``resource_group`` parameter will be used.
      - If the connection type is "IPSec", then the name of a local network gateway must be passed within the
        ``local_network_gateway2`` kwarg. If that gateway has a different resource group than the resource group
        specified within the ``resource_group`` parameter, then it must be specified within ``lgw2_group`` kwarg.
        Otherwise, the resource_group within the ``resource_group`` parameter will be used.
      - If the connection type is "ExpressRoute", then a valid Resource ID representing an ExpressRouteCircuit Object
        must be passed as the ``peer`` kwarg.

    The second endpoint is immutable once set.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_create_or_update test_name test_group test_vgw test_type

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

    # Use virtual_network_gateway to link to the ID of the existing vgw
    vgw1 = await hub.exec.azurerm.network.virtual_network_gateway.get(
        ctx=ctx, name=virtual_network_gateway, resource_group=resource_group,
    )
    if "error" not in vgw1:
        virtual_network_gateway = {"id": str(vgw1["id"])}
    else:
        log.error(
            "The virtual network gateway specified within the virtual_network_gateway parameter does not exist."
        )
        result = {
            "error": "The virtual network gateway specified within the virtual_network_gateway parameter does not exist."
        }
        return result

    # Use kwargs(virtual_network_gateway2) to link to the ID of the existing vgw
    if kwargs.get("virtual_network_gateway2"):
        vgw2_name = kwargs["virtual_network_gateway2"]
        vgw2_group = kwargs.get("vgw2_group") or resource_group
        vgw2 = await hub.exec.azurerm.network.virtual_network_gateway.get(
            ctx=ctx, name=vgw2_name, resource_group=vgw2_group,
        )
        if "error" not in vgw2:
            kwargs["virtual_network_gateway2"] = {"id": str(vgw2["id"])}
            if kwargs.get("vgw2_group"):
                kwargs.pop("vgw2_group")
        else:
            log.error(
                f"The virtual network gateway {vgw2_name} does not exist within the resource group {vgw2_group}"
            )
            result = {
                "error": f"The virtual network gateway {vgw2_name} does not exist within the resource group {vgw2_group}"
            }
            return result

    # Use kwargs(local_network_gateway2) to link to the ID of the existing lgw
    if kwargs.get("local_network_gateway2"):
        lgw2_name = kwargs["local_network_gateway2"]
        lgw2_group = kwargs.get("lgw2_group") or resource_group
        lgw2 = await hub.exec.azurerm.network.local_network_gateway.get(
            ctx=ctx, name=lgw2_name, resource_group=lgw2_group,
        )
        if "error" not in lgw2:
            kwargs["local_network_gateway2"] = {"id": str(lgw2["id"])}
            if kwargs.get("lgw2_group"):
                kwargs.pop("lgw2_group")
        else:
            log.error(
                f"The local network gateway {lgw2_name} does not exist within the resource group {lgw2_group}"
            )
            result = {
                "error": f"The local network gateway {lgw2_name} does not exist within the resource group {lgw2_group}"
            }
            return result

    try:
        connectionmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VirtualNetworkGatewayConnection",
            virtual_network_gateway1=virtual_network_gateway,
            connection_type=connection_type,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        connection = netconn.virtual_network_gateway_connections.create_or_update(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
            parameters=connectionmodel,
        )

        connection.wait()
        result = connection.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def connection_get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the details of a specified virtual network gateway connection.

    :param name: The name of the virtual network gateway connection to query.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_get test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        connection = netconn.virtual_network_gateway_connections.get(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
        )

        result = connection.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def connection_delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes the specified virtual network gateway connection.

    :param name: The name of the virtual network gateway connection that will be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        connection = netconn.virtual_network_gateway_connections.delete(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
        )
        connection.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def connection_update_tags(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Updates virtual network gateway connection tags with specified values.

    :param name: The name of the virtual network gateway connection.

    :param resource_group: The name of the resource group to which the virtual network gateway belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_update_tags test_name test_group tags='{"owner": "me"}'

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        connection = netconn.virtual_network_gateway_connections.update_tags(
            virtual_network_gateway_connection_name=name,
            resource_group_name=resource_group,
            tags=tags,
        )

        connection.wait()
        result = connection.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def connection_set_shared_key(hub, ctx, name, resource_group, value, **kwargs):
    """
    .. versionadded:: 1.0.0

    Sets the shared key for a virtual network gateway connection object.

    :param name: The virtual network gateway connection name.

    :param resource_group: The name of the resource group.

    :param value: The new virtual network connection shared key value.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_set_shared_key test_name test_group test_value

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        key = netconn.virtual_network_gateway_connections.set_shared_key(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
            value=value,
        )

        key.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def connection_get_shared_key(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets information about the specified virtual network gateway connection shared key through the Network
    resource provider.

    :param name: The virtual network gateway connection shared key name.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_get_shared_key test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        key = netconn.virtual_network_gateway_connections.get_shared_key(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
        )

        result = key.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def connection_reset_shared_key(
    hub, ctx, name, resource_group, key_length=128, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Resets the virtual network gateway connection shared key for passed virtual network gateway connection in the
    specified resource group through Network resource provider.

    :param name: The name of the virtual network gateway connection that will have its shared key reset.

    :param resource_group: The name of the resource group.

    :param key_length: The virtual network connection reset shared key length, should between 1 and 128.
        Defaults to 128.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connection_set_shared_key test_name test_group test_key_length

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        rkey = netconn.virtual_network_gateway_connections.reset_shared_key(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
            key_length=key_length,
        )

        rkey.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def connections_list(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all the virtual network gateway connections within a specified resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.connections_list test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        connections = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.virtual_network_gateway_connections.list(
                resource_group_name=resource_group
            )
        )

        for connection in connections:
            result[connection["name"]] = connection
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all virtual network gateways within a resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.list test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateways = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.virtual_network_gateways.list(resource_group_name=resource_group)
        )

        for gateway in gateways:
            result[gateway["name"]] = gateway
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(
    hub,
    ctx,
    name,
    resource_group,
    virtual_network,
    ip_configurations,
    gateway_type,
    sku,
    polling=True,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 3.0.0, 4.0.0

    Creates or updates a virtual network gateway in the specified resource group.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    :param virtual_network: The name of the virtual network associated with the virtual network gateway.

    :param ip_configurations: A list of dictionaries representing valid VirtualNetworkGatewayIPConfiguration objects.
        It is important to note that if the active_active key word argument is specified and active_active is disabled,
        then only one IP configuration dictionary is permitted. If active_active is enabled, then two IP configuration
        dictionaries are required. Valid parameters for a VirtualNetworkGatewayIPConfiguration object are:

        - ``name``: The name of the VirtualNetworkGatewayIPConfiguration object that is unique within
          the resource group.
        - ``public_ip_address``: The name of an existing public IP address that will be assigned to the object.
        - ``private_ip_allocation_method``: The private IP allocation method. Possible values are:
          "Static" and "Dynamic".
        - ``subnet``: The name of an existing subnet inside of which the IP configuration will reside.

    :param gateway_type: The type of this virtual network gateway. Possible values include: "Vpn" and "ExpressRoute".
        The gateway type is immutable once set.

    :param sku: The name of the Gateway SKU. Possible values include: 'Basic', 'HighPerformance', 'Standard',
        'UltraPerformance', 'VpnGw1', 'VpnGw2', 'VpnGw3', 'VpnGw4', 'VpnGw5', 'VpnGw1AZ', 'VpnGw2AZ', 'VpnGw3AZ',
        'VpnGw4AZ', 'VpnGw5AZ', 'ErGw1AZ', 'ErGw2AZ', and 'ErGw3AZ'.

    :param polling: An optional boolean flag representing whether a Poller will be used during the creation of the
        Virtual Network Gateway. If set to True, a Poller will be used by this operation and the module will not return
        until the Virtual Network Gateway has completed its creation process and has been successfully provisioned. If
        set to False, the module will return once the Virtual Network Gateway has successfully begun its creation
        process. Defaults to True.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.create_or_update test_name test_group test_vnet test_ip_configs

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

    # Handle VirtualNetworkGatewaySku creation
    sku = {"name": sku, "tier": sku}

    # Loop through IP Configurations and build each dictionary to pass to model creation.
    if isinstance(ip_configurations, list):
        subnet = await hub.exec.azurerm.network.virtual_network.subnet_get(
            ctx=ctx,
            name="GatewaySubnet",
            virtual_network=virtual_network,
            resource_group=resource_group,
            **kwargs,
        )
        if "error" not in subnet:
            subnet = {"id": str(subnet["id"])}
            for ipconfig in ip_configurations:
                if "name" in ipconfig:
                    ipconfig["subnet"] = subnet
                    if ipconfig.get("public_ip_address"):
                        pub_ip = await hub.exec.azurerm.network.public_ip_address.get(
                            ctx=ctx,
                            name=ipconfig["public_ip_address"],
                            resource_group=resource_group,
                            **kwargs,
                        )
                        if "error" not in pub_ip:
                            ipconfig["public_ip_address"] = {"id": str(pub_ip["id"])}

    try:
        gatewaymodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VirtualNetworkGateway",
            ip_configurations=ip_configurations,
            gateway_type=gateway_type,
            sku=sku,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        gateway = netconn.virtual_network_gateways.create_or_update(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            parameters=gatewaymodel,
            polling=polling,
        )

        gateway.wait()
        result = gateway.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the details of a specific virtual network gateway within a specified resource group.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateway = netconn.virtual_network_gateways.get(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        result = gateway.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes the specified virtual network gateway.

    :param name: The name of the virtual network gateway that will be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateway = netconn.virtual_network_gateways.delete(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )
        gateway.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def list_connections(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all connections associated with a virtual network gateway.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.list_connections test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        connections = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.virtual_network_gateways.list_connections(
                resource_group_name=resource_group, virtual_network_gateway_name=name
            )
        )
        for connection in connections:
            result[connection["name"]] = connection
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def reset(hub, ctx, name, resource_group, gateway_vip=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Resets the virtual network gateway in the specified resource group.

    :param name: The name of the virtual network gateway to reset.

    :param resource_group: The name of the resource group.

    :param gateway_vip: Virtual network gateway vip address supplied to the begin reset of the active-active feature
        enabled gateway.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.reset test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        reset = netconn.virtual_network_gateways.reset(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            gateway_vip=gateway_vip,
        )
        reset.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def reset_vpn_client_shared_key(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Resets the VPN client shared key of the virtual network gateway in the specified resource group.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.reset_vpn_client_shared_key test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        reset = netconn.virtual_network_gateways.reset_vpn_client_shared_key(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        reset.wait()
        result = reset.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def generatevpnclientpackage(
    hub,
    ctx,
    name,
    resource_group,
    processor_architecture,
    authentication_method,
    radius_server_auth_certificate=None,
    client_root_certificates=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Generates VPN client package for P2S client of the virtual network gateway in the specified resource group.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    :param processor_architecture: VPN client Processor Architecture. Possible values include: 'Amd64', 'X86'

    :param authentication_method: VPN client authentication method. Possible values include: 'EAPTLS', 'EAPMSCHAPv2'

    :param radius_server_auth_certificate: The public certificate data for the radius server authentication
        certificate as a Base-64 encoded string. Required only if external radius authentication has been configured
        with EAPTLS authentication.

    :param client_root_certificates: A list of client root certificates public certificate data encoded as Base-64
        strings. Optional parameter for external radius based authentication with EAPTLS.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.generatevpnclientpackage test_name test_group test_params

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        pkgmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VpnClientParameters",
            processor_architecture=processor_architecture,
            authentication_method=authentication_method,
            radius_server_auth_certificate=radius_server_auth_certificate,
            client_root_certificates=client_root_certificates,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        pkg = netconn.virtual_network_gateways.generatevpnclientpackage(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            parameters=pkgmodel,
            **kwargs,
        )

        result = pkg
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def generate_vpn_profile(
    hub,
    ctx,
    name,
    resource_group,
    processor_architecture,
    authentication_method,
    radius_server_auth_certificate=None,
    client_root_certificates=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Generates VPN profile for P2S client of the virtual network gateway in the specified resource group. Used for IKEV2
    and radius based authentication.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    :param processor_architecture: VPN client Processor Architecture. Possible values include: 'Amd64' and 'X86'.

    :param authentication_method: VPN client authentication method. Possible values include: 'EAPTLS' and 'EAPMSCHAPv2'.

    :param radius_server_auth_certificate: The public certificate data for the radius server authentication
        certificate as a Base-64 encoded string. Required only if external radius authentication has been configured
        with EAPTLS authentication.

    :param client_root_certificates: A list of client root certificates public certificate data encoded as Base-64
        strings. This is an optional parameter for external radius based authentication with EAPTLS.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.generate_vpn_profile test_name test_group test_params

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        profilemodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VpnClientParameters",
            processor_architecture=processor_architecture,
            authentication_method=authentication_method,
            radius_server_auth_certificate=radius_server_auth_certificate,
            client_root_certificates=client_root_certificates,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        profile = netconn.virtual_network_gateways.generate_vpn_profile(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            parameters=profilemodel,
            **kwargs,
        )

        result = profile
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def get_vpn_profile_package_url(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets pre-generated VPN profile for P2S client of the virtual network gateway in the specified resource group.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get_vpn_profile_package_url test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        url = netconn.virtual_network_gateways.get_vpn_profile_package_url(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        url.wait()
        result = url.result()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_bgp_peer_status(hub, ctx, name, resource_group, peer=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the status of all BGP peers.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    :param peer: The IP address of the peer to retrieve the status of.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get_bgp_peer_status test_name test_group test_peer

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        peers = netconn.virtual_network_gateways.get_bgp_peer_status(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            peer=peer,
        )

        peers.wait()
        peers_result = peers.result().as_dict()
        for bgp_peer in peers_result["value"]:
            result["BGP peer"] = bgp_peer
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def supported_vpn_devices(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a xml format representation for supported vpn devices.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.supported_vpn_devices test_name test_group

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        devices = netconn.virtual_network_gateways.supported_vpn_devices(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        result = devices
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_learned_routes(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a list of routes that the virtual network gateway has learned, including routes learned from BGP peers.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get_learned_routes test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        routes = netconn.virtual_network_gateways.get_learned_routes(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        routes_result = routes.result().as_dict()
        for route in routes_result["value"]:
            result["route_list"] = route
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_advertised_routes(hub, ctx, name, resource_group, peer, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a list of routes the virtual network gateway is advertising to a specified peer.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    :param peer: The IP address of the peer.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get_learned_routes test_name test_group test_peer

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        routes = netconn.virtual_network_gateways.get_advertised_routes(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            peer=peer,
        )

        routes.wait()
        routes_result = routes.result().as_dict()
        for route in routes_result["value"]:
            result["route_list"] = route
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def set_vpnclient_ipsec_parameters(
    hub,
    ctx,
    name,
    resource_group,
    sa_life_time_seconds,
    sa_data_size_kilobytes,
    ipsec_encryption,
    ipsec_integrity,
    ike_encryption,
    ike_integrity,
    dh_group,
    pfs_group,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Sets the vpnclient ipsec policy for P2S client of virtual network gateway in the specified resource group through
    the network resource provider.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group.

    The following parameters are for creating a VpnClientIPsecParameters object:

    :param sa_life_time_seconds: The IPSec Security Association (also called Quick Mode or Phase 2 SA)
        lifetime in seconds for P2S client. Must be between 300 - 172799 seconds.

    :param sa_data_size_kilobytes: The IPSec Security Association (also called Quick Mode or Phase 2 SA)
        payload size in KB for P2S client. Must be between 1024 - 2147483647 kilobytes.

    :param ipsec_encryption: The IPSec encryption algorithm (IKE phase 1). Possible values include:
        'None', 'DES', 'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES128', 'GCMAES192', 'GCMAES256'

    :param ipsec_integrity: The IPSec integrity algorithm (IKE phase 1). Possible values include:
        'MD5', 'SHA1', 'SHA256', 'GCMAES128', 'GCMAES192', 'GCMAES256'

    :param ike_encryption: The IKE encryption algorithm (IKE phase 2). Possible values include:
        'DES', 'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES256', 'GCMAES128'

    :param ike_integrity: The IKE integrity algorithm (IKE phase 2). Possible values include:
        'MD5', 'SHA1', 'SHA256', 'SHA384', 'GCMAES256', 'GCMAES128'

    :param dh_group: The DH Group used in IKE Phase 1 for initial SA. Possible values include:
        'None', 'DHGroup1', 'DHGroup2', 'DHGroup14', 'DHGroup2048', 'ECP256', 'ECP384', 'DHGroup24'

    :param pfs_group: The Pfs Group used in IKE Phase 2 for new child SA. Possible values include:
        'None', 'PFS1', 'PFS2', 'PFS2048', 'ECP256', 'ECP384', 'PFS24', 'PFS14', 'PFSMM'

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.set_vpnclient_ipsec_parameters test_name test_group
                                                                               test_vpnclient_ipsec_params

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VpnClientIPsecParameters",
            sa_life_time_seconds=sa_life_time_seconds,
            sa_data_size_kilobytes=sa_data_size_kilobytes,
            ipsec_encryption=ipsec_encryption,
            ipsec_integrity=ipsec_integrity,
            ike_encryption=ike_encryption,
            ike_integrity=ike_integrity,
            dh_group=dh_group,
            pfs_group=pfs_group,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        params = netconn.virtual_network_gateways.set_vpnclient_ipsec_parameters(
            resource_group_name=resource_group,
            virtual_network_gateway_name=name,
            vpnclient_ipsec_params=paramsmodel,
            **kwargs,
        )

        params.wait()
        result = params.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_vpnclient_ipsec_parameters(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets information about the vpnclient ipsec policy for P2S client of virtual network gateway in the specified
    resource group through Network resource provider.

    :param name: The virtual network gateway name.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.get_vpnclient_ipsec_parameters test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        policy = netconn.virtual_network_gateways.get_vpnclient_ipsec_parameters(
            resource_group_name=resource_group, virtual_network_gateway_name=name
        )

        policy.wait()
        result = policy.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def vpn_device_configuration_script(
    hub, ctx, name, resource_group, vendor, device_family, firmware_version, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Gets a xml format representation for vpn device configuration script.

    :param name: The name of the virtual network gateway connection for which the configuration
        script is generated.

    :param resource_group: The name of the resource group.

    :param vendor: The vendor for the vpn device.

    :param device_family: The device family for the vpn device.

    :param firmware_version: The firmware version for the vpn device.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.vpn_device_configuration_script test_name test_group test_vendor
                                                                                test_device_fam test_version

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        scriptmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VpnDeviceScriptParameters",
            vendor=vendor,
            device_family=device_family,
            firmware_version=firmware_version,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        script = netconn.virtual_network_gateways.vpn_device_configuration_script(
            resource_group_name=resource_group,
            virtual_network_gateway_connection_name=name,
            parameters=scriptmodel,
            **kwargs,
        )

        result = script
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def update_tags(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Updates virtual network gateway tags with specified values.

    :param name: The name of the virtual network gateway.

    :param resource_group: The name of the resource group to which the virtual network gateway belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.update_tags test_name test_group tags='{"owner": "me"}'

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        gateway = netconn.virtual_network_gateways.update_tags(
            virtual_network_gateway_name=name,
            resource_group_name=resource_group,
            tags=tags,
        )

        result = gateway.as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
