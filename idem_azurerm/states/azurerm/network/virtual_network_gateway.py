# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Gateway State Module

.. versionadded:: 1.0.0

.. versionchanged:: 3.0.0, 4.0.0

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
    vgw2_group=None,
    local_network_gateway2=None,
    lgw2_group=None,
    peer=None,
    connection_protocol=None,
    shared_key=None,
    enable_bgp=None,
    ipsec_policy=None,
    use_policy_based_traffic_selectors=None,
    routing_weight=None,
    express_route_gateway_bypass=None,
    authorization_key=None,
    use_local_azure_ip_address=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a virtual network gateway connection exists.

    :param name:
        The name of the virtual network gateway connection.

    :param resource_group:
        The name of the resource group associated with the virtual network gateway connection.

    :param virtual_network_gateway:
        The name of the virtual network gateway that will be the first endpoint of the connection. This value is
        immutable once set.

    :param connection_type:
        The gateway connection type. Possible values include: "IPsec", "Vnet2Vnet", "ExpressRoute". This value is
        immutable once set.

    :param virtual_network_gateway2:
        The name of the virtual network gateway that will be used as the second endpoint for the connection. Required
        for a connection type of "Vnet2Vnet". This value is immutable once set.

    :param vgw2_group: The resource group for the virtual network gateway passed as the ``virtual_network_gateway2``
        parameter. If this parameter is not specified it will default to the same resource group as the virtual network
        gateway specified in the ``virtual_network_gateway`` parameter.

    :param local_network_gateway2:
        The valid Resource ID representing a LocalNetworkGateway Object that will be used as the second endpoint for
        the connection. Required for a connection type of "IPSec". This value is immutable once set.

    :param lgw2_group: The resource group for the local network gateway passed as the ``local_network_gateway2``
        parameter. If this parameter is not specified it will default to the same resource group as the virtual network
        gateway specified in the ``virtual_network_gateway`` parameter.

    :param peer:
        The valid Resource ID representing a ExpressRouteCircuit Object that will be used as the second endpoint for
        the connection. Required for a connection type of "ExpressRoute". This value is immutable once set.

    :param shared_key:
        The shared key for the connection. Required for a connection type of "IPsec" or "Vnet2Vnet". Defaults to a
        randomly generated key.

    :param ipsec_policy:
        A dictionary representing an IpsecPolicy object that is considered by this connection as the IPSec Policy.
        Required for a connection type of "IPSec". Valid parameters include:

          - ``sa_life_time_seconds``: (Optional) The IPSec Security Association (also called Quick Mode or Phase 2 SA)
            lifetime in seconds for a site to site VPN tunnel.
          - ``sa_data_size_kilobytes``: (Optional) The IPSec Security Association (also called Quick Mode or Phase 2 SA)
            payload size in KB for a site to site VPN tunnel.
          - ``ipsec_encryption``: (Required) The IPSec encryption algorithm (IKE phase 1). Possible values include:
            'None', 'DES', 'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES128', 'GCMAES192', 'GCMAES256'.
          - ``ipsec_integrity``: (Required) The IPSec integrity algorithm (IKE phase 1). Possible values include:
            'MD5', 'SHA1', 'SHA256', 'GCMAES128', 'GCMAES192', 'GCMAES256'.
          - ``ike_encryption``: (Required) The IKE encryption algorithm (IKE phase 2). Possible values include: 'DES',
            'DES3', 'AES128', 'AES192', 'AES256', 'GCMAES256', 'GCMAES128'
          - ``ike_integrity``: (Required) The IKE integrity algorithm (IKE phase 2). Possible values include: 'MD5',
            'SHA1', 'SHA256', 'SHA384', 'GCMAES256', 'GCMAES128'.
          - ``dh_group``: (Required) The DH Group used in IKE Phase 1 for initial SA. Possible values include: 'None',
            'DHGroup1', 'DHGroup2', 'DHGroup14', 'DHGroup2048', 'ECP256', 'ECP384', 'DHGroup24'.
          - ``pfs_group``: (Required) The Pfs Group used in IKE Phase 2 for new child SA. Possible values include:
            'None', 'PFS1', 'PFS2', 'PFS2048', 'ECP256', 'ECP384', 'PFS24', 'PFS14', 'PFSMM'.

    :param connection_protocol:
        The connection protocol used for this connection. Possible values include: "IKEv2" and "IKEv1".

    :param enable_bgp:
        A boolean representing whether BGP is enabled for this virtual network gateway connection. Both
        endpoints of the connection must have BGP enabled and may not have the same ASN values. Cannot be enabled while
        use_policy_based_traffic_selectors is enabled. Defaults to False.

    :param use_policy_based_traffic_selectors:
        A boolean value representing whether to enable policy-based traffic selectors for a connection. Cannot be
        enabled at the same time as BGP. Requires that IPSec policies for the gateway connection are defined. Can only
        be used with a connction type of "IPSec".

    :param routing_weight:
        An integer representing the routing weight.

    :param express_route_gateway_bypass:
        A boolean value representing whether or not to bypass the ExpressRoute Gateway for data forwarding. Can only
        be used with a connection type of "ExpressRoute".

    :param authorization_key:
        The ExpressRoute Circuit authorization key. Required for a connection type of "ExpressRoute".

    :param use_local_azure_ip_address:
        A boolean value specifying whether or not to use a private local Azure IP for the connection.

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
                - virtual_network_gateway: virtual_gateway1
                - connection_type: 'Vnet2Vnet'
                - virtual_network_gateway2: virtual_gateway2
                - enable_bgp: False
                - shared_key: 'key'
                - tags:
                    contact_name: Elmer Fudd Gantry

        Ensure virtual network gateway IPSec connection exists:
            azurerm.network.virtual_network_gateway.connection_present:
                - name: connection1
                - resource_group: group1
                - virtual_network_gateway: virtual_gateway
                - connection_type: 'IPSec'
                - local_network_gateway2: local_gateway
                - enable_bgp: False
                - shared_key: 'key'
                - use_policy_based_traffic_selectors: True
                - ipsec_policy:
                    sa_life_time_seconds: 300
                    sa_data_size_kilobytes: 1024
                    ipsec_encryption: 'DES'
                    ipsec_integrity: 'SHA256'
                    ike_encryption: 'DES'
                    ike_integrity: 'SHA256'
                    dh_group: 'None'
                    pfs_group: 'None'
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

        if use_local_azure_ip_address is not None:
            if use_local_azure_ip_address != gateway.get("use_local_azure_ip_address"):
                ret["changes"]["use_local_azure_ip_address"] = {
                    "old": gateway.get("use_local_azure_ip_address"),
                    "new": use_local_azure_ip_address,
                }

        if connection_type.lower() == "ipsec":
            if ipsec_policy:
                if not isinstance(ipsec_policy, dict):
                    ret[
                        "comment"
                    ] = "ipsec_policy must be provided as a single dictionary!"
                    return ret

                if len(connection.get("ipsec_policies", [])) == 1:
                    existing_policy = connection.get("ipsec_policies")[0]

                    for key in ipsec_policy.keys():
                        if ipsec_policy[key] != existing_policy.get(key):
                            ret["changes"]["ipsec_policies"] = {
                                "old": connection.get("ipsec_policies", []),
                                "new": [ipsec_policy],
                            }
                            break

                else:
                    ret["changes"]["ipsec_policies"] = {
                        "old": connection.get("ipsec_policies", []),
                        "new": [ipsec_policy],
                    }

            if use_policy_based_traffic_selectors is not None:
                if use_policy_based_traffic_selectors != connection.get(
                    "use_policy_based_traffic_selectors"
                ):
                    ret["changes"]["use_policy_based_traffic_selectors"] = {
                        "old": connection.get("use_policy_based_traffic_selectors"),
                        "new": use_policy_based_traffic_selectors,
                    }

        if connection_type.lower() == "vnet2vnet" or connection_type.lower() == "ipsec":
            if enable_bgp is not None and enable_bgp != connection.get("enable_bgp"):
                ret["changes"]["enable_bgp"] = {
                    "old": connection.get("enable_bgp"),
                    "new": enable_bgp,
                }

            if shared_key and shared_key != connection.get("shared_key"):
                ret["changes"]["shared_key"] = {
                    "new": "REDACTED",
                }

        if connection_type.lower() == "expressroute":
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

    if ctx["test"]:
        ret[
            "comment"
        ] = "Virtual network gateway connection {0} would be created.".format(name)
        ret["result"] = None
        return ret

    connection_kwargs = kwargs.copy()
    connection_kwargs.update(connection_auth)

    if action == "create" or len(ret["changes"]) > 1 or not tag_changes:
        if connection_type.lower() == "ipsec":
            con = await hub.exec.azurerm.network.virtual_network_gateway.connection_create_or_update(
                ctx=ctx,
                name=name,
                resource_group=resource_group,
                virtual_network_gateway=virtual_network_gateway,
                connection_type=connection_type,
                connection_protocol=connection_protocol,
                enable_bgp=enable_bgp,
                shared_key=shared_key,
                ipsec_policies=[ipsec_policy],
                local_network_gateway2=local_network_gateway2,
                use_policy_based_traffic_selectors=use_policy_based_traffic_selectors,
                use_local_azure_ip_address=use_local_azure_ip_address,
                lgw2_group=lgw2_group,
                tags=tags,
                **connection_kwargs,
            )

        if connection_type.lower() == "vnet2vnet":
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
                vgw2_group=vgw2_group,
                use_local_azure_ip_address=use_local_azure_ip_address,
                tags=tags,
                **connection_kwargs,
            )

    # no idea why create_or_update doesn't work for tags
    if action == "update" and tag_changes:
        con = await hub.exec.azurerm.network.virtual_network_gateway.connection_update_tags(
            ctx,
            name=name,
            resource_group=resource_group,
            tags=tags,
            **connection_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": con}
        if ret["changes"]["new"].get("shared_key"):
            ret["changes"]["new"]["shared_key"] = "REDACTED"

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
    gateway_type,
    sku,
    vpn_type=None,
    enable_bgp=None,
    active_active=None,
    bgp_settings=None,
    address_prefixes=None,
    generation=None,
    enable_dns_forwarding=None,
    enable_private_ip_address=None,
    polling=True,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 3.0.0, 4.0.0

    Ensure a virtual network gateway exists.

    :param name:
        Name of the virtual network gateway.

    :param resource_group:
        The resource group associated with the virtual network gateway.

    :param virtual_network:
        The virtual network associated with the virtual network gateway.

    :param ip_configurations:
        A list of dictionaries representing valid VirtualNetworkGatewayIPConfiguration objects. It is important to note
        that if the active_active key word argument is specified and active_active is disabled, then only one IP
        configuration object is permitted. If active_active is enabled, then at least two IP configuration dictionaries
        are required. Valid parameters for a VirtualNetworkGatewayIPConfiguration object are:

        - ``name``: The name of the VirtualNetworkGatewayIPConfiguration object that is unique within
          the resource group.
        - ``public_ip_address``: The name of an existing public IP address that will be assigned to the object.
        - ``private_ip_allocation_method``: The private IP allocation method. Possible values are:
          "Static" and "Dynamic".
        - ``subnet``: The name of an existing subnet inside of which the IP configuration will reside.

    :param gateway_type:
        The type of this virtual network gateway. Possible values include: "Vpn" and "ExpressRoute". The gateway type
        is immutable once set.

    :param sku:
        The name of the Gateway SKU. Possible values include: 'Basic', 'HighPerformance', 'Standard',
        'UltraPerformance', 'VpnGw1', 'VpnGw2', 'VpnGw3', 'VpnGw4', 'VpnGw5', 'VpnGw1AZ', 'VpnGw2AZ', 'VpnGw3AZ',
        'VpnGw4AZ', 'VpnGw5AZ', 'ErGw1AZ', 'ErGw2AZ', and 'ErGw3AZ'.

    :param vpn_type:
        The type of this virtual network gateway. Possible values include: "PolicyBased" and "RouteBased".
        The vpn type is immutable once set.

    :param enable_bgp:
        A boolean value specifying whether BGP is enabled for this virtual network gateway.

    :param active_active:
        A boolean value specifying whether active-active mode is enabled for this virtual network gateway.

    :param bgp_settings:
        A dictionary representing a valid BgpSettings object, which stores the virtual network gateway's
        BGP speaker settings. Valid parameters include:

        - ``asn``: The BGP speaker's Autonomous System Number.
        - ``bgp_peering_address``: The BGP peering address and BGP identifier of this BGP speaker.
        - ``peer_weight``: The weight added to routes learned from this BGP speaker.

    :param address_prefixes:
        A list of CIDR blocks which can be used by subnets within the virtual network. Represents the
        custom routes address space specified by the the customer for virtual network gateway and VpnClient.

    :param generation:
        The generation for this virtual network gateway. This parameter may only be set if the ``gateway_type``
        parameter is set to "Vpn". Possible values include: "None", "Generation1", and "Generation2".

    :param enable_dns_forwarding:
        A boolean value specifying whether DNS forwarding is enabled.

    :param enable_private_ip_address:
        A boolean value specifying whether a private IP needs to be enabled on this gateway for connections.

    :param polling:
        An optional boolean flag representing whether a Poller will be used during the creation of the Virtual
        Network Gateway. If set to True, a Poller will be used by this operation and the module will not return until
        the Virtual Network Gateway has completed its creation process and has been successfully provisioned. If set to
        False, the module will return once the Virtual Network Gateway has successfully begun its creation process.
        Defaults to True.

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

        if sku != gateway.get("sku").get("name"):
            ret["changes"]["sku"] = {
                "old": gateway.get("sku"),
                "new": {"name": sku, "tier": sku},
            }

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

        if active_active is not None and active_active != gateway.get("active_active"):
            ret["changes"]["active_active"] = {
                "old": gateway.get("active_active"),
                "new": active_active,
            }

        if enable_bgp is not None and enable_bgp != gateway.get("enable_bgp"):
            ret["changes"]["enable_bgp"] = {
                "old": gateway.get("enable_bgp"),
                "new": enable_bgp,
            }

        if generation:
            if generation != gateway.get("vpn_gateway_generation"):
                ret["changes"]["vpn_gateway_generation"] = {
                    "old": gateway.get("vpn_gateway_generation"),
                    "new": generation,
                }

        if enable_dns_forwarding is not None:
            if enable_dns_forwarding != gateway.get("enable_dns_forwarding"):
                ret["changes"]["enable_dns_forwarding"] = {
                    "old": gateway.get("enable_dns_forwarding"),
                    "new": enable_dns_forwarding,
                }

        if enable_private_ip_address is not None:
            if enable_private_ip_address != gateway.get("enable_private_ip_address"):
                ret["changes"]["enable_private_ip_address"] = {
                    "old": gateway.get("enable_private_ip_address"),
                    "new": enable_private_ip_address,
                }

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
        vpn_gateway_generation=generation,
        enable_dns_forwarding=enable_dns_forwarding,
        enable_private_ip_address=enable_private_ip_address,
        polling=polling,
        **gateway_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": gateway}

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
