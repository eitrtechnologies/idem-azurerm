# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Peering Execution Module

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


async def list_(hub, ctx, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all peerings associated with a virtual network.

    :param virtual_network: The virtual network name for which to list peerings.

    :param resource_group: The resource group name for the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_peering.list testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        peerings = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.virtual_network_peerings.list(
                resource_group_name=resource_group, virtual_network_name=virtual_network
            )
        )

        for peering in peerings:
            result[peering["name"]] = peering
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a virtual network peering object.

    :param name: The name of the virtual network peering object to delete.

    :param virtual_network: The virtual network name containing the
        peering object.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_peering.delete peer1 testnet testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        peering = netconn.virtual_network_peerings.delete(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            virtual_network_peering_name=name,
        )
        peering.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific virtual network peering object.

    :param name: The name of the virtual network peering to query.

    :param virtual_network: The virtual network name containing the
        peering object.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_peering.get peer1 testnet testgroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        peering = netconn.virtual_network_peerings.get(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            virtual_network_peering_name=name,
        )

        result = peering.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(
    hub,
    ctx,
    name,
    remote_virtual_network,
    virtual_network,
    resource_group,
    remote_vnet_group=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Create or update a virtual network peering object.

    :param name: The name assigned to the peering object being created or updated.

    :param remote_virtual_network: A valid name of a virtual network with which to peer.

    :param remote_vnet_group: The resource group of the remote virtual network. Defaults to
        the same resource group as the "local" virtual network.

    :param virtual_network: The virtual network name containing the
        peering object.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_peering.create_or_update peer1 \
                  remotenet testnet testgroup remote_vnet_group=remotegroup

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    # Use Remote Virtual Network name to link to the ID of an existing object
    remote_vnet = await hub.exec.azurerm.network.virtual_network.get(
        ctx=ctx,
        name=remote_virtual_network,
        resource_group=(remote_vnet_group or resource_group),
        **kwargs,
    )
    if "error" not in remote_vnet:
        remote_virtual_network = {"id": str(remote_vnet["id"])}

    try:
        peermodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VirtualNetworkPeering",
            remote_virtual_network=remote_virtual_network,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        peering = netconn.virtual_network_peerings.create_or_update(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            virtual_network_peering_name=name,
            virtual_network_peering_parameters=peermodel,
        )
        peering.wait()
        peer_result = peering.result()
        result = peer_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result
