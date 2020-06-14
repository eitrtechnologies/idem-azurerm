# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Gateway State Module

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
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.virtual_network.present",
        ]
    },
    "connection_present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.virtual_network.present",
            "states.azurerm.network.virtual_network_gateway.present",
        ]
    },
}


async def connection_present(
    hub,
    ctx,
    name,
    resource_group,
    virtual_network_gateway,
    connection_type,
    virtual_network_gateway2=None,
    local_network_gateway2=None,
    peer=None,
    connection_protocol=None,
    shared_key=None,
    enable_bgp=None,
    ipsec_policies=None,
    use_policy_based_traffic_selectors=None,
    routing_weight=None,
    express_route_gateway_bypass=None,
    authorization_key=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network gateway connection exists.

    :param name:
        The name of the virtual network gateway connection.

    :param resource_group:
        The name of the resource group associated with the virtual network gateway connection.

    :param virtual_network_gateway:
        The name of the virtual network gateway that will be the first endpoint of the connection.
        The virtual_network_gateway is immutable once set.

    :param connection_type:
        Gateway connection type. Possible values include: 'IPsec', 'Vnet2Vnet', and 'ExpressRoute'.
        The connection_type is immutable once set.

    :param virtual_network_gateway2:
        The valid Resource ID representing a VirtualNetworkGateway Object that will be used as the second endpoint
        for the connection. Required for a connection_type of 'Vnet2Vnet'. This is immutable once set.

    :param local_network_gateway2:
        The valid Resource ID representing a LocalNetworkGateway Object that will be used as the second endpoint
        for the connection. Required for a connection_type of 'IPSec'. This is immutable once set.

    :param peer:
        The valid Resource ID representing a ExpressRouteCircuit Object that will be used as the second endpoint
        for the connection. Required for a connection_type of 'ExpressRoute'. This is immutable once set.

    :param connection_protocol:
        Connection protocol used for this connection. Possible values include: 'IKEv2', 'IKEv1'.

    :param shared_key:
        The shared key for the connection. Required for a connection_type of 'IPSec' or 'Vnet2Vnet'.
        Defaults to a randomly generated key.

    :param enable_bgp:
        Whether BGP is enabled for this virtual network gateway connection or not. This is a bool value that defaults
        to False. Both endpoints of the connection must have BGP enabled and may not have the same ASN values. Cannot
        be enabled while use_policy_based_traffic_selectors is enabled.

    :param ipsec_policies:
        The IPSec Policies to be considered by this connection. Must be passed as a list containing a single IPSec
        Policy dictionary that contains the following parameters:
          - ``sa_life_time_seconds``: The IPSec Security Association (also called Quick Mode or Phase 2 SA)
                                      lifetime in seconds for P2S client. Must be between 300 - 172799 seconds.
          - ``sa_data_size_kilobytes``: The IPSec Security Association (also called Quick Mode or Phase 2 SA) payload
                                        size in KB for P2S client. Must be between 1024 - 2147483647 kilobytes.
          - ``ipsec_encryption``: The IPSec encryption algorithm (IKE phase 1). Possible values include: 'None',
                                  'DES', 'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES128', 'GCMAES192', 'GCMAES256'
          - ``ipsec_integrity``: The IPSec integrity algorithm (IKE phase 1). Possible values include:
                                 'MD5', 'SHA1', 'SHA256', 'GCMAES128', 'GCMAES192', 'GCMAES256'
          - ``ike_encryption``: The IKE encryption algorithm (IKE phase 2). Possible values include:
                                'DES', 'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES256', 'GCMAES128'
          - ``ike_integrity``: The IKE integrity algorithm (IKE phase 2). Possible values include:
                               'MD5', 'SHA1', 'SHA256', 'SHA384', 'GCMAES256', 'GCMAES128'
          - ``dh_group``: The DH Group used in IKE Phase 1 for initial SA. Possible values include:
                          'None', 'DHGroup1', 'DHGroup2', 'DHGroup14', 'DHGroup2048', 'ECP256', 'ECP384', 'DHGroup24'
          - ``pfs_group``: The Pfs Group used in IKE Phase 2 for new child SA. Possible values include:
                           'None', 'PFS1', 'PFS2', 'PFS2048', 'ECP256', 'ECP384', 'PFS24', 'PFS14', 'PFSMM'

    :param use_policy_based_traffic_selectors:
        Enable policy-based traffic selectors for a connection. Can only be enabled for a connection of type 'IPSec'.
        Cannot be enabled at the same time as BGP. Requires that the IPSec policies are defined. This is a bool value.

    :param routing_weight:
        The routing weight. This is an integer value.

    :param express_route_gateway_bypass:
        Bypass ExpressRoute Gateway for data forwarding. This is a bool value.

    :param authorization_key:
        The authorizationKey. This is a string value.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the virtual network gateway connection object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network gateway Vnet2Vnet connection exists:
            azurerm.network.virtual_network_gateway.connection_present:
                - name: connection1
                - resource_group: group1
                - virtual_network_gateway: Resource ID for gateway1
                - connection_type: 'Vnet2Vnet'
                - virtual_network_gateway2: Resource ID for gateway2
                - enable_bgp: False
                - shared_key: 'key'
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure virtual network gateway IPSec connection exists:
            azurerm.network.virtual_network_gateway.connection_present:
                - name: connection1
                - resource_group: group1
                - virtual_network_gateway: Resource ID for gateway1
                - connection_type: 'IPSec'
                - local_network_gateway2: Resource ID for gateway2
                - enable_bgp: False
                - shared_key: 'key'
                - use_policy_based_traffic_selectors: True
                - ipsec_policies:
                  - sa_life_time_seconds: 300
                    sa_data_size_kilobytes: 1024
                    ipsec_encryption: 'DES'
                    ipsec_integrity: 'SHA256'
                    ike_encryption: 'DES'
                    ike_integrity: 'SHA256'
                    dh_group: 'None'
                    pfs_group: 'None'
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

    connection = await hub.exec.azurerm.network.virtual_network_gateway.connection_get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in connection:
        action = "update"
        tag_changes = differ.deep_diff(connection.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if connection_protocol and connection_protocol != connection.get(
            "connection_protocol"
        ):
            ret["changes"]["connection_protocol"] = {
                "old": connection.get("connection_protocol"),
                "new": connection_protocol,
            }

        if connection_type == "IPSec":
            if ipsec_policies:
                if not isinstance(ipsec_policies, list):
                    ret[
                        "comment"
                    ] = "ipsec_policies must be provided as a list containing a single dictionary!"
                    return ret

                try:
                    policy = ipsec_policies[0]
                except IndexError:
                    ret[
                        "comment"
                    ] = "ipsec_policies must be provided as a list containing a single dictionary!"
                    return ret

                if not isinstance(policy, dict):
                    ret[
                        "comment"
                    ] = "ipsec_policies must be provided as a list containing a single dictionary!"
                    return ret

                if len(connection.get("ipsec_policies", [])) == 1:
                    connection_policy = connection.get("ipsec_policies")[0]

                    for key in policy.keys():
                        if policy[key] != connection_policy.get(key):
                            ret["changes"]["ipsec_policies"] = {
                                "old": connection.get("ipsec_policies", []),
                                "new": ipsec_policies,
                            }
                            break

                else:
                    ret["changes"]["ipsec_policies"] = {
                        "old": connection.get("ipsec_policies", []),
                        "new": ipsec_policies,
                    }

            # Checking boolean parameter
            if use_policy_based_traffic_selectors is not None:
                if use_policy_based_traffic_selectors != connection.get(
                    "use_policy_based_traffic_selectors"
                ):
                    ret["changes"]["use_policy_based_traffic_selectors"] = {
                        "old": connection.get("use_policy_based_traffic_selectors"),
                        "new": use_policy_based_traffic_selectors,
                    }

        if connection_type == "Vnet2Vnet" or connection_type == "IPSec":
            # Checking boolean parameter
            if enable_bgp is not None and enable_bgp != connection.get("enable_bgp"):
                ret["changes"]["enable_bgp"] = {
                    "old": connection.get("enable_bgp"),
                    "new": enable_bgp,
                }

            if shared_key and shared_key != connection.get("shared_key"):
                ret["changes"]["shared_key"] = {
                    "old": connection.get("shared_key"),
                    "new": shared_key,
                }

        if connection_type == "ExpressRoute":
            if peer and peer != connection.get("peer"):
                ret["changes"]["peer"] = {"old": connection.get("peer"), "new": peer}

            if authorization_key and authorization_key != connection.get(
                "authorization_key"
            ):
                ret["changes"]["authorization_key"] = {
                    "old": connection.get("authorization_key"),
                    "new": enable_bgp,
                }

            if routing_weight is not None and routing_weight != connection.get(
                "routing_weight"
            ):
                ret["changes"]["routing_weight"] = {
                    "old": connection.get("routing_weight"),
                    "new": routing_weight,
                }

            # Checking boolean parameter
            if express_route_gateway_bypass is not None:
                if express_route_gateway_bypass != connection.get(
                    "express_route_gateway_bypass"
                ):
                    ret["changes"]["express_route_gateway_bypass"] = {
                        "old": connection.get("express_route_gateway_bypass"),
                        "new": express_route_gateway_bypass,
                    }

        if not ret["changes"]:
            ret["result"] = True
            ret[
                "comment"
            ] = "Virtual network gateway connection {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "Virtual network gateway connection {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "virtual_network_gateway": virtual_network_gateway,
                "connection_type": connection_type,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if enable_bgp is not None:
            ret["changes"]["new"]["enable_bgp"] = enable_bgp
        if connection_protocol:
            ret["changes"]["new"]["connection_protocol"] = connection_protocol
        if shared_key:
            ret["changes"]["new"]["shared_key"] = shared_key
        if local_network_gateway2:
            ret["changes"]["new"]["local_network_gateway2"] = local_network_gateway2
        if ipsec_policies:
            ret["changes"]["new"]["ipsec_policies"] = ipsec_policies
        if virtual_network_gateway2:
            ret["changes"]["new"]["virtual_network_gateway2"] = virtual_network_gateway2
        if express_route_gateway_bypass is not None:
            ret["changes"]["new"][
                "express_route_gateway_bypass"
            ] = express_route_gateway_bypass
        if use_policy_based_traffic_selectors is not None:
            ret["changes"]["new"][
                "use_policy_based_traffic_selectors"
            ] = use_policy_based_traffic_selectors
        if authorization_key:
            ret["changes"]["new"]["authorization_key"] = authorization_key
        if peer:
            ret["changes"]["new"]["peer"] = peer
        if routing_weight is not None:
            ret["changes"]["new"]["routing_weight"] = routing_weight

    if ctx["test"]:
        ret[
            "comment"
        ] = "Virtual network gateway connection {0} would be created.".format(name)
        ret["result"] = None
        return ret

    connection_kwargs = kwargs.copy()
    connection_kwargs.update(connection_auth)

    if connection_type == "IPSec":
        con = await hub.exec.azurerm.network.virtual_network_gateway.connection_create_or_update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            virtual_network_gateway=virtual_network_gateway,
            connection_type=connection_type,
            connection_protocol=connection_protocol,
            enable_bgp=enable_bgp,
            shared_key=shared_key,
            ipsec_policies=ipsec_policies,
            local_network_gateway2=local_network_gateway2,
            use_policy_based_traffic_selectors=use_policy_based_traffic_selectors,
            tags=tags,
            **connection_kwargs,
        )

    if connection_type == "Vnet2Vnet":
        con = await hub.exec.azurerm.network.virtual_network_gateway.connection_create_or_update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            virtual_network_gateway=virtual_network_gateway,
            connection_type=connection_type,
            connection_protocol=connection_protocol,
            enable_bgp=enable_bgp,
            shared_key=shared_key,
            virtual_network_gateway2=virtual_network_gateway2,
            tags=tags,
            **connection_kwargs,
        )

    if "error" not in con:
        ret["result"] = True
        ret[
            "comment"
        ] = f"Virtual network gateway connection {name} has been {action}d."
        return ret

    ret[
        "comment"
    ] = "Failed to {0} virtual network gateway connection {1}! ({2})".format(
        action, name, con.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def connection_absent(
    hub, ctx, name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network gateway connection does not exist in the specified resource group.

    :param name:
        Name of the virtual network gateway connection.

    :param resource_group:
        The resource group associated with the virtual network gateway connection.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network gateway connection absent:
            azurerm.network.virtual_network_gateway.connection_absent:
                - name: connection1
                - resource_group: group1
                - connection_auth: {{ profile }}

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

    connection = await hub.exec.azurerm.network.virtual_network_gateway.connection_get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in connection:
        ret["result"] = True
        ret["comment"] = "Virtual network gateway connection {0} was not found.".format(
            name
        )
        return ret

    if ctx["test"]:
        ret[
            "comment"
        ] = "Virtual network gateway connection {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": connection,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.virtual_network_gateway.connection_delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret[
            "comment"
        ] = "Virtual network gateway connection {0} has been deleted.".format(name)
        ret["changes"] = {"old": connection, "new": {}}
        return ret

    ret["comment"] = "Failed to delete virtal network gateway connection {0}!".format(
        name
    )
    return ret


async def present(
    hub,
    ctx,
    name,
    resource_group,
    virtual_network,
    ip_configurations,
    gateway_type=None,
    vpn_type=None,
    sku=None,
    enable_bgp=None,
    active_active=None,
    bgp_settings=None,
    address_prefixes=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network gateway exists.

    :param name:
        Name of the virtual network gateway.

    :param resource_group:
        The resource group associated with the virtual network gateway.

    :param virtual_network:
        The virtual network associated with the virtual network gateway.

    :param ip_configurations:
        A list of dictionaries representing valid VirtualNetworkGatewayIPConfiguration objects. Valid parameters are:
          - ``name``: The name of the resource that is unique within a resource group.
          - ``public_ip_address``: Name of an existing public IP address that'll be assigned to the IP config object.
          - ``private_ip_allocation_method``: The private IP allocation method. Possible values are:
                                              'Static' and 'Dynamic'.
          - ``subnet``: Name of an existing subnet inside of which the IP config will reside.
        If active_active is disabled, only one IP configuration dictionary is permitted. If active_active is enabled,
        two IP configuration dictionaries are required.

    :param gateway_type:
        The type of this virtual network gateway. Possible values include: 'Vpn' and 'ExpressRoute'.
        The gateway type immutable once set.

    :param vpn_type:
        The type of this virtual network gateway. Possible values include: 'PolicyBased' and 'RouteBased'.
        The vpn type is immutable once set.

    :param sku: A dictionary representing the virtual network gateway SKU. Valid parameters are:
          - ``name``: Gateway SKU name. Possible values include 'Basic', 'HighPerformance', 'Standard',
                      'UltraPerformance', 'VpnGw1', 'VpnGw2', 'VpnGw3', 'VpnGw1AZ', 'VpnGw2AZ', 'VpnGw3AZ',
                      'ErGw1AZ', 'ErGw2AZ', and 'ErGw3AZ'.
          - ``tier``: Gateway SKU tier. Possible values include 'Basic', 'HighPerformance', 'Standard',
                      'UltraPerformance', 'VpnGw1', 'VpnGw2', 'VpnGw3', 'VpnGw1AZ', 'VpnGw2AZ', 'VpnGw3AZ',
                      'ErGw1AZ', 'ErGw2AZ', and 'ErGw3AZ'.
          - ``capacity``: The capacity. This is an integer value.

    :param enable_bgp: Whether BGP is enabled for this virtual network gateway or not. This is a bool value that
        defaults to False. BGP requires a SKU of VpnGw1, VpnGw2, VpnGw3, Standard, or HighPerformance.

    :param active_active: Whether active-active mode is enabled for this virtual network gateway or not. This is a bool
        value that defauls to False. Active-active mode requires a SKU of VpnGw1, VpnGw2, VpnGw3, or HighPerformance.

    :param bgp_settings:
        A dictionary representing a valid BgpSettings object, which stores the virtual network gateway's BGP speaker
        settings. Valid parameters include:
          - ``asn``: The BGP speaker's Autonomous System Number. This is an integer value.
          - ``bgp_peering_address``: The BGP peering address and BGP identifier of this BGP speaker.
                                     This is a string value.
          - ``peer_weight``: The weight added to routes learned from this BGP speaker. This is an integer value.

    :param address_prefixes:
        A list of CIDR blocks which can be used by subnets within the virtual network. Represents the custom routes
        address space specified by the the customer for virtual network gateway and VpnClient.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the virtual network gateway object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network gateway exists:
            azurerm.network.virtual_network_gateway.present:
                - name: gateway1
                - resource_group: group1
                - virtual_network: vnet1
                - ip_configurations:
                  - name: ip_config1
                    private_ip_allocation_method: 'Dynamic'
                    public_ip_address: pub_ip1
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure virtual network gateway exists:
            azurerm.network.virtual_network_gateway.present:
                - name: gateway1
                - resource_group: group1
                - virtual_network: vnet1
                - ip_configurations:
                  - name: ip_config1
                    private_ip_allocation_method: 'Dynamic'
                    public_ip_address: pub_ip1
                  - name: ip_config2
                    private_ip_allocation_method: 'Dynamic'
                    public_ip_address: pub_ip2
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}
                - gateway_type: 'Vpn'
                - vpn_type: 'RouteBased'
                - active_active: True
                - enable_bgp: True
                - bgp_settings:
                    asn: 65514
                    bgp_peering_address: 10.2.2.2
                    peering_weight: 0
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'

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

    gateway = await hub.exec.azurerm.network.virtual_network_gateway.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in gateway:
        action = "update"
        tag_changes = differ.deep_diff(gateway.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if ip_configurations:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                gateway.get("ip_configurations", []),
                ip_configurations,
                ["public_ip_address", "subnet"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"ip_configurations" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["ip_configurations"] = comp_ret["changes"]

        # Checking boolean parameter
        if active_active is not None and active_active != gateway.get("active_active"):
            ret["changes"]["active_active"] = {
                "old": gateway.get("active_active"),
                "new": active_active,
            }

        # Checking boolean parameter
        if enable_bgp is not None and enable_bgp != gateway.get("enable_bgp"):
            ret["changes"]["enable_bgp"] = {
                "old": gateway.get("enable_bgp"),
                "new": enable_bgp,
            }

        if sku:
            sku_changes = differ.deep_diff(gateway.get("sku", {}), sku)
            if sku_changes:
                ret["changes"]["sku"] = sku_changes

        if bgp_settings:
            if not isinstance(bgp_settings, dict):
                ret["comment"] = "BGP settings must be provided as a dictionary!"
                return ret

            for key in bgp_settings:
                if bgp_settings[key] != gateway.get("bgp_settings", {}).get(key):
                    ret["changes"]["bgp_settings"] = {
                        "old": gateway.get("bgp_settings"),
                        "new": bgp_settings,
                    }
                    break

        addr_changes = set(address_prefixes or []).symmetric_difference(
            set(gateway.get("custom_routes", {}).get("address_prefixes", []))
        )
        if addr_changes:
            ret["changes"]["custom_routes"] = {
                "address_prefixes": {
                    "old": gateway.get("custom_routes", {}).get("address_prefixes", []),
                    "new": address_prefixes,
                }
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Virtual network gateway {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Virtual network gateway {0} would be updated.".format(
                name
            )
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "virtual_network": virtual_network,
                "ip_configurations": ip_configurations,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if gateway_type:
            ret["changes"]["new"]["gateway_type"] = gateway_type
        if vpn_type:
            ret["changes"]["new"]["vpn_type"] = vpn_type
        if sku:
            ret["changes"]["new"]["sku"] = sku
        if enable_bgp is not None:
            ret["changes"]["new"]["enable_bgp"] = enable_bgp
        if bgp_settings:
            ret["changes"]["new"]["bgp_settings"] = bgp_settings
        if active_active is not None:
            ret["changes"]["new"]["active_active"] = active_active
        if address_prefixes:
            ret["changes"]["new"]["custom_routes"] = {
                "address_prefixes": address_prefixes
            }

    if ctx["test"]:
        ret["comment"] = "Virtual network gateway {0} would be created.".format(name)
        ret["result"] = None
        return ret

    gateway_kwargs = kwargs.copy()
    gateway_kwargs.update(connection_auth)

    gateway = await hub.exec.azurerm.network.virtual_network_gateway.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        virtual_network=virtual_network,
        ip_configurations=ip_configurations,
        gateway_type=gateway_type,
        vpn_type=vpn_type,
        tags=tags,
        sku=sku,
        enable_bgp=enable_bgp,
        bgp_settings=bgp_settings,
        active_active=active_active,
        custom_routes={"address_prefixes": address_prefixes},
        **gateway_kwargs,
    )

    if "error" not in gateway:
        ret["result"] = True
        ret["comment"] = f"Virtual network gateway {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} virtual network gateway {1}! ({2})".format(
        action, name, gateway.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network gateway object does not exist in the specified resource group.

    :param name:
        Name of the virtual network gateway object.

    :param resource_group:
        The resource group associated with the virtual network gateway.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network gateway absent:
            azurerm.network.virtual_network_gateway.absent:
                - name: gateway1
                - resource_group: group1
                - connection_auth: {{ profile }}

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

    gateway = await hub.exec.azurerm.network.virtual_network_gateway.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in gateway:
        ret["result"] = True
        ret["comment"] = "Virtual network gateway object {0} was not found.".format(
            name
        )
        return ret

    if ctx["test"]:
        ret["comment"] = "Virtual network gateway object {0} would be deleted.".format(
            name
        )
        ret["result"] = None
        ret["changes"] = {
            "old": gateway,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.virtual_network_gateway.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Virtual network gateway object {0} has been deleted.".format(
            name
        )
        ret["changes"] = {"old": gateway, "new": {}}
        return ret

    ret["comment"] = "Failed to delete virtal network gateway object {0}!".format(name)
    return ret
