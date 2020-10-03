# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Load Balancer State Module

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
    sku=None,
    frontend_ip_configurations=None,
    backend_address_pools=None,
    load_balancing_rules=None,
    probes=None,
    inbound_nat_rules=None,
    inbound_nat_pools=None,
    outbound_rules=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a load balancer exists.

    :param name:
        Name of the load balancer.

    :param resource_group:
        The resource group assigned to the load balancer.

    :param sku:
        The load balancer SKU, which can be 'Basic' or 'Standard'. This property cannot be changed once the
        load balancer is created.

    :param frontend_ip_configurations:
        A list of dictionaries representing valid FrontendIPConfiguration objects. A frontend IP
        configuration can be either private (using private IP address and subnet parameters) or public (using a
        reference to a public IP address object). Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``private_ip_address``: The private IP address of the IP configuration. Required if
          ``private_ip_allocation_method`` is 'Static'.
        - ``private_ip_allocation_method``: The Private IP allocation method. Possible values are: 'Static', 'Dynamic'.
        - ``subnet``: Name of an existing subnet inside of which the frontend IP will reside.
        - ``public_ip_address``: Name of an existing public IP address which will be assigned to the frontend IP object.

    :param backend_address_pools:
        A list of dictionaries representing valid BackendAddressPool objects. Inbound traffic is randomly
        load balanced across IPs in the backend IPs. Valid parameters include:

        - ``name``: (Required) The name of the resource that is unique within the set of backend address pools used
          by the load balancer.
        - ``load_balancer_backend_addresses``: A list of LoadBalancerBackendAddress objects.

    :param probes:
        A list of dictionaries representing valid Probe objects. Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``protocol``: The protocol of the endpoint. Possible values are 'Http' or 'Tcp'. If 'Tcp' is specified, a
          received ACK is required for the probe to be successful. If 'Http' is specified, a 200 OK response from the
          specified URI is required for the probe to be successful.
        - ``port``: The port for communicating the probe. Possible values range from 1 to 65535, inclusive.
        - ``interval_in_seconds``: The interval, in seconds, for how frequently to probe the endpoint for health status.
          Typically, the interval is slightly less than half the allocated timeout period (in seconds) which allows two
          full probes before taking the instance out of rotation. The default value is 15, the minimum value is 5.
        - ``number_of_probes``: The number of probes where if no response, will result in stopping further traffic from
          being delivered to the endpoint. This values allows endpoints to be taken out of rotation faster or slower
          than the typical times used in Azure.
        - ``request_path``: The URI used for requesting health status from the VM. Path is required if a protocol is
          set to 'Http'. Otherwise, it is not allowed. There is no default value.

    :param load_balancing_rules:
        A list of dictionaries representing valid LoadBalancingRule objects. Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``load_distribution``: The load distribution policy for this rule. Possible values are 'Default', 'SourceIP',
          and 'SourceIPProtocol'.
        - ``frontend_port``: The port for the external endpoint. Port numbers for each rule must be unique within the
          Load Balancer. Acceptable values are between 0 and 65534. Note that value 0 enables 'Any Port'.
        - ``backend_port``: The port used for internal connections on the endpoint. Acceptable values are between 0 and
          65535. Note that value 0 enables 'Any Port'.
        - ``idle_timeout_in_minutes``: The timeout for the TCP idle connection. The value can be set between 4 and 30
          minutes. The default value is 4 minutes. This element is only used when the protocol is set to TCP.
        - ``enable_floating_ip``: Configures a virtual machine's endpoint for the floating IP capability required
          to configure a SQL AlwaysOn Availability Group. This setting is required when using the SQL AlwaysOn
          Availability Groups in SQL server. This setting can't be changed after you create the endpoint.
        - ``disable_outbound_snat``: Configures SNAT for the VMs in the backend pool to use the public IP address
          specified in the frontend of the load balancing rule.
        - ``frontend_ip_configuration``: Name of the frontend IP configuration object used by the load balancing rule
          object.
        - ``backend_address_pool``: Name of the backend address pool object used by the load balancing rule object.
          Inbound traffic is randomly load balanced across IPs in the backend IPs.
        - ``probe``: Name of the probe object used by the load balancing rule object.

    :param inbound_nat_rules:
        A list of dictionaries representing valid InboundNatRule objects. Defining inbound NAT rules on your
        load balancer is mutually exclusive with defining an inbound NAT pool. Inbound NAT pools are referenced from
        virtual machine scale sets. NICs that are associated with individual virtual machines cannot reference an
        Inbound NAT pool. They have to reference individual inbound NAT rules. Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``frontend_ip_configuration``: Name of the frontend IP configuration object used by the inbound NAT rule
          object.
        - ``protocol``: Possible values include 'Udp', 'Tcp', or 'All'.
        - ``frontend_port``: The port for the external endpoint. Port numbers for each rule must be unique within the
          Load Balancer. Acceptable values range from 1 to 65534.
        - ``backend_port``: The port used for the internal endpoint. Acceptable values range from 1 to 65535.
        - ``idle_timeout_in_minutes``: The timeout for the TCP idle connection. The value can be set between 4 and 30
          minutes. The default value is 4 minutes. This element is only used when the protocol is set to TCP.
        - ``enable_floating_ip``: Configures a virtual machine's endpoint for the floating IP capability required
          to configure a SQL AlwaysOn Availability Group. This setting is required when using the SQL AlwaysOn
          Availability Groups in SQL server. This setting can't be changed after you create the endpoint.

    :param inbound_nat_pools:
        A list of dictionaries representing valid InboundNatPool objects. They define an external port range
        for inbound NAT to a single backend port on NICs associated with a load balancer. Inbound NAT rules are created
        automatically for each NIC associated with the Load Balancer using an external port from this range. Defining an
        Inbound NAT pool on your Load Balancer is mutually exclusive with defining inbound NAT rules. Inbound NAT pools
        are referenced from virtual machine scale sets. NICs that are associated with individual virtual machines cannot
        reference an inbound NAT pool. They have to reference individual inbound NAT rules. Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``frontend_ip_configuration``: Name of the frontend IP configuration object used by the inbound NAT pool
          object.
        - ``protocol``: Possible values include 'Udp', 'Tcp', or 'All'.
        - ``frontend_port_range_start``: The first port number in the range of external ports that will be used to
          provide Inbound NAT to NICs associated with a load balancer. Acceptable values range between 1 and 65534.
        - ``frontend_port_range_end``: The last port number in the range of external ports that will be used to
          provide Inbound NAT to NICs associated with a load balancer. Acceptable values range between 1 and 65535.
        - ``backend_port``: The port used for internal connections to the endpoint. Acceptable values are between 1 and
          65535.
        - ``idle_timeout_in_minutes``: The timeout for the TCP idle connection. The value can be set between 4 and 30
          minutes. This element is only used when the protocol is set to TCP. The default value is 4 minutes.
        - ``enable_floating_ip``: A boolean value whether to configure a virtual machine's endpoint for the floating
          IP capability required to configure a SQL AlwaysOn Availability Group. This setting is required when using
          the SQL AlwaysOn Availability Groups in SQL server. This setting can't be changed after you create the
          endpoint.
        - ``enable_tcp_reset``: A boolean value whether to receive bidirectional TCP Reset on TCP flow idle timeout or
          unexpected connection termination. This element is only used when the protocol is set to TCP.

    :param outbound_rules:
        A list of dictionaries representing valid OutboundNatRule objects. Valid parameters are:

        - ``name``: The name of the resource that is unique within a resource group.
        - ``frontend_ip_configuration``: Name of the frontend IP configuration object used by the outbound NAT rule
          object.
        - ``backend_address_pool``: Name of the backend address pool object used by the outbound NAT rule object.
          Outbound traffic is randomly load balanced across IPs in the backend IPs.
        - ``allocated_outbound_ports``: The number of outbound ports to be used for NAT.
        - ``protocol``: The protocol for the outbound rule in load balancer. Possible values include: 'Tcp',
          'Udp', 'All'.
        - ``enable_tcp_reset``: A boolean value whether to receive bidirectional TCP Reset on TCP flow idle timeout or
          unexpected connection termination. This element is only used when the protocol is set to TCP.
        - ``idle_timeout_in_minutes``: The timeout for the TCP idle connection.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the load balancer object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure load balancer exists:
            azurerm.network.load_balancer.present:
                - name: lb1
                - resource_group: group1
                - location: eastus
                - frontend_ip_configurations:
                  - name: lb1_feip1
                    public_ip_address: pub_ip1
                - backend_address_pools:
                  - name: lb1_bepool1
                - probes:
                  - name: lb1_webprobe1
                    protocol: tcp
                    port: 80
                    interval_in_seconds: 5
                    number_of_probes: 2
                - load_balancing_rules:
                  - name: lb1_webprobe1
                    protocol: tcp
                    frontend_port: 80
                    backend_port: 80
                    idle_timeout_in_minutes: 4
                    frontend_ip_configuration: lb1_feip1
                    backend_address_pool: lb1_bepool1
                    probe: lb1_webprobe1
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

    if sku:
        sku = {"name": sku.capitalize()}

    load_bal = await hub.exec.azurerm.network.load_balancer.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in load_bal:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(load_bal.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # sku changes
        if sku:
            sku_changes = differ.deep_diff(load_bal.get("sku", {}), sku)
            if sku_changes:
                log.error(
                    "The sku of a load balancer can only be set at creation time."
                )
                ret["result"] = False
                ret[
                    "comment"
                ] = "The sku of a load balancer can only be set at creation time."
                ret["changes"] = {}
                return ret

        # frontend_ip_configurations changes
        if frontend_ip_configurations:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("frontend_ip_configurations", []),
                frontend_ip_configurations,
                ["public_ip_address", "subnet"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"frontend_ip_configurations" {0}'.format(
                    comp_ret["comment"]
                )
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["frontend_ip_configurations"] = comp_ret["changes"]

        # backend_address_pools changes
        if backend_address_pools:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("backend_address_pools", []), backend_address_pools
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"backend_address_pools" {0}'.format(
                    comp_ret["comment"]
                )
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["backend_address_pools"] = comp_ret["changes"]

        # probes changes
        if probes:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("probes", []), probes
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"probes" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["probes"] = comp_ret["changes"]

        # load_balancing_rules changes
        if load_balancing_rules:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("load_balancing_rules", []),
                load_balancing_rules,
                ["frontend_ip_configuration", "backend_address_pool", "probe"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"load_balancing_rules" {0}'.format(
                    comp_ret["comment"]
                )
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["load_balancing_rules"] = comp_ret["changes"]

        # inbound_nat_rules changes
        if inbound_nat_rules:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("inbound_nat_rules", []),
                inbound_nat_rules,
                ["frontend_ip_configuration"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"inbound_nat_rules" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["inbound_nat_rules"] = comp_ret["changes"]

        # inbound_nat_pools changes
        if inbound_nat_pools:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("inbound_nat_pools", []),
                inbound_nat_pools,
                ["frontend_ip_configuration"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"inbound_nat_pools" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["inbound_nat_pools"] = comp_ret["changes"]

        # outbound_rules changes
        if outbound_rules:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                load_bal.get("outbound_rules", []),
                outbound_rules,
                ["frontend_ip_configuration"],
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"outbound_rules" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["outbound_rules"] = comp_ret["changes"]

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Load balancer {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Load balancer {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Load balancer {0} would be created.".format(name)
        ret["result"] = None
        return ret

    lb_kwargs = kwargs.copy()
    lb_kwargs.update(connection_auth)

    if action == "create" or len(ret["changes"]) > 1 or not tag_changes:
        load_bal = await hub.exec.azurerm.network.load_balancer.create_or_update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            sku=sku,
            tags=tags,
            frontend_ip_configurations=frontend_ip_configurations,
            backend_address_pools=backend_address_pools,
            load_balancing_rules=load_balancing_rules,
            probes=probes,
            inbound_nat_rules=inbound_nat_rules,
            inbound_nat_pools=inbound_nat_pools,
            outbound_rules=outbound_rules,
            **lb_kwargs,
        )

    # no idea why create_or_update doesn't work for tags
    if action == "update" and tag_changes:
        load_bal = await hub.exec.azurerm.network.load_balancer.update_tags(
            ctx, name=name, resource_group=resource_group, tags=tags, **lb_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": load_bal}

    if "error" not in load_bal:
        ret["result"] = True
        ret["comment"] = f"Load balancer {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} load balancer {1}! ({2})".format(
        action, name, load_bal.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a load balancer does not exist in the resource group.

    :param name:
        Name of the load balancer.

    :param resource_group:
        The resource group assigned to the load balancer.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure load balancer absent:
            azurerm.network.load_balancer.absent:
              - name: test_lb
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

    load_bal = await hub.exec.azurerm.network.load_balancer.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in load_bal:
        ret["result"] = True
        ret["comment"] = "Load balancer {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Load balancer {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": load_bal,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.load_balancer.delete(
        ctx, name=name, resource_group=resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Load balancer {0} has been deleted.".format(name)
        ret["changes"] = {"old": load_bal, "new": {}}
        return ret

    ret["comment"] = "Failed to delete load balancer {0}!".format(name)
    return ret
