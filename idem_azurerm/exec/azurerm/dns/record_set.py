# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) DNS Record Set Execution Module

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

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.dns.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, zone_name, resource_group, record_type, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Creates or updates a record set within a DNS zone.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type: The type of DNS record in this record set. Record sets of type SOA can be updated but not
        created (they are created when the DNS zone is created). Possible values include: 'A', 'AAAA', 'CAA', 'CNAME',
        'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    CLI Example:

    .. code-block:: bash

        azurerm.dns.record_set.create_or_update myhost myzone testgroup A arecords='[{ipv4_address: 10.0.0.1}]' ttl=300

    """
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)

    try:
        record_set_model = await hub.exec.azurerm.utils.create_object_model(
            "dns", "RecordSet", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        record_set = dnsconn.record_sets.create_or_update(
            relative_record_set_name=name,
            zone_name=zone_name,
            resource_group_name=resource_group,
            record_type=record_type,
            parameters=record_set_model,
            if_match=kwargs.get("if_match"),
            if_none_match=kwargs.get("if_none_match"),
        )
        result = record_set.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, zone_name, resource_group, record_type, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes a record set from a DNS zone. This operation cannot be undone.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type: The type of DNS record in this record set. Record sets of type SOA cannot be deleted (they are
        deleted when the DNS zone is deleted). Possible values include: 'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR',
        'SOA', 'SRV', 'TXT'

    CLI Example:

    .. code-block:: bash

        azurerm.dns.record_set.delete myhost myzone testgroup A

    """
    result = False
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        record_set = dnsconn.record_sets.delete(
            relative_record_set_name=name,
            zone_name=zone_name,
            resource_group_name=resource_group,
            record_type=record_type,
            if_match=kwargs.get("if_match"),
        )
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, zone_name, resource_group, record_type, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a dictionary representing a record set's properties.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type: The type of DNS record in this record set. Possible values include: 'A', 'AAAA', 'CAA', 'CNAME',
        'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    CLI Example:

    .. code-block:: bash

        azurerm.dns.record_set.get '@' myzone testgroup SOA

    """
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        record_set = dnsconn.record_sets.get(
            relative_record_set_name=name,
            zone_name=zone_name,
            resource_group_name=resource_group,
            record_type=record_type,
        )
        result = record_set.as_dict()

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_type(
    hub,
    ctx,
    zone_name,
    resource_group,
    record_type,
    top=None,
    recordsetnamesuffix=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Lists the record sets of a specified type in a DNS zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type: The type of record sets to enumerate. Possible values include: 'A', 'AAAA', 'CAA', 'CNAME',
        'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param top: The maximum number of record sets to return. If not specified, returns up to 100 record sets.

    :param recordsetnamesuffix: The suffix label of the record set name that has to be used to filter the record set
        enumerations.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.record_set.list_by_type myzone testgroup SOA

    """
    result = {}
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        record_sets = await hub.exec.azurerm.utils.paged_object_to_list(
            dnsconn.record_sets.list_by_type(
                zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
                top=top,
                recordsetnamesuffix=recordsetnamesuffix,
            )
        )

        for record_set in record_sets:
            result[record_set["name"]] = record_set
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_dns_zone(
    hub, ctx, zone_name, resource_group, top=None, recordsetnamesuffix=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Lists all record sets in a DNS zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param top: The maximum number of record sets to return. If not specified, returns up to 100 record sets.

    :param recordsetnamesuffix: The suffix label of the record set name that has to be used to filter the record set
        enumerations.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.record_set.list_by_dns_zone myzone testgroup

    """
    result = {}
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        record_sets = await hub.exec.azurerm.utils.paged_object_to_list(
            dnsconn.record_sets.list_by_dns_zone(
                zone_name=zone_name,
                resource_group_name=resource_group,
                top=top,
                recordsetnamesuffix=recordsetnamesuffix,
            )
        )

        for record_set in record_sets:
            result[record_set["name"]] = record_set
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
