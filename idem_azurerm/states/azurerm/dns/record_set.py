# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) DNS Record Set State Module

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

    .. code-block:: yaml

        Ensure DNS record set exists:
            azurerm.dns.record_set.present:
                - name: web
                - zone_name: contoso.com
                - resource_group: my_rg
                - record_type: A
                - ttl: 300
                - arecords:
                  - ipv4_address: 10.0.0.1
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure DNS record set is absent:
            azurerm.dns.record_set.absent:
                - name: web
                - zone_name: contoso.com
                - resource_group: my_rg
                - record_type: A
                - connection_auth: {{ profile }}

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging

import six

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.dns.zone.present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    zone_name,
    resource_group,
    record_type,
    if_match=None,
    if_none_match=None,
    etag=None,
    metadata=None,
    ttl=None,
    arecords=None,
    aaaa_records=None,
    mx_records=None,
    ns_records=None,
    ptr_records=None,
    srv_records=None,
    txt_records=None,
    cname_record=None,
    soa_record=None,
    caa_records=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a record set exists in a DNS zone.

    :param name:
        The name of the record set, relative to the name of the zone.

    :param zone_name:
        Name of the DNS zone (without a terminating dot).

    :param resource_group:
        The resource group assigned to the DNS zone.

    :param record_type:
        The type of DNS record in this record set. Record sets of type SOA can be updated but not created
        (they are created when the DNS zone is created). Possible values include: 'A', 'AAAA', 'CAA', 'CNAME',
        'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param if_match:
        The etag of the record set. Omit this value to always overwrite the current record set. Specify the last-seen
        etag value to prevent accidentally overwritting any concurrent changes.

    :param if_none_match:
        Set to '*' to allow a new record set to be created, but to prevent updating an existing record set. Other values
        will be ignored.

    :param etag:
        The etag of the record set. `Etags <https://docs.microsoft.com/en-us/azure/dns/dns-zones-records#etags>`_ are
        used to handle concurrent changes to the same resource safely.

    :param metadata:
        A dictionary of strings can be passed as tag metadata to the record set object.

    :param ttl:
        The TTL (time-to-live) of the records in the record set. Required when specifying record information.

    :param arecords:
        The list of A records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.arecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param aaaa_records:
        The list of AAAA records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.aaaarecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param mx_records:
        The list of MX records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.mxrecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param ns_records:
        The list of NS records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.nsrecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param ptr_records:
        The list of PTR records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.ptrrecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param srv_records:
        The list of SRV records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.srvrecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param txt_records:
        The list of TXT records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.txtrecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param cname_record:
        The CNAME record in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.cnamerecord?view=azure-python>`_
        to create a dictionary representing the record object.

    :param soa_record:
        The SOA record in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.soarecord?view=azure-python>`_
        to create a dictionary representing the record object.

    :param caa_records:
        The list of CAA records in the record set. View the
        `Azure SDK documentation <https://docs.microsoft.com/en-us/python/api/azure.mgmt.dns.models.caarecord?view=azure-python>`_
        to create a list of dictionaries representing the record objects.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure record set exists:
            azurerm.dns.record_set.present:
                - name: web
                - zone_name: contoso.com
                - resource_group: my_rg
                - record_type: A
                - ttl: 300
                - arecords:
                  - ipv4_address: 10.0.0.1
                - metadata:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    record_vars = [
        "arecords",
        "aaaa_records",
        "mx_records",
        "ns_records",
        "ptr_records",
        "srv_records",
        "txt_records",
        "cname_record",
        "soa_record",
        "caa_records",
    ]

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    rec_set = await hub.exec.azurerm.dns.record_set.get(
        ctx,
        name,
        zone_name,
        resource_group,
        record_type,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in rec_set:
        action = "update"
        metadata_changes = differ.deep_diff(rec_set.get("metadata", {}), metadata or {})
        if metadata_changes:
            ret["changes"]["metadata"] = metadata_changes

        for record_str in record_vars:
            # pylint: disable=eval-used
            record = eval(record_str)
            if record:
                if not ttl:
                    ret[
                        "comment"
                    ] = "TTL is required when specifying record information!"
                    return ret
                if not rec_set.get(record_str):
                    ret["changes"] = {"new": {record_str: record}}
                    continue
                if record_str[-1] != "s":
                    if not isinstance(record, dict):
                        ret[
                            "comment"
                        ] = "{0} record information must be specified as a dictionary!".format(
                            record_str
                        )
                        return ret
                    for k, v in record.items():
                        if v != rec_set[record_str].get(k):
                            ret["changes"] = {"new": {record_str: record}}
                elif record_str[-1] == "s":
                    if not isinstance(record, list):
                        ret[
                            "comment"
                        ] = "{0} record information must be specified as a list of dictionaries!".format(
                            record_str
                        )
                        return ret
                    local, remote = [
                        sorted(config) for config in (record, rec_set[record_str])
                    ]
                    for idx, local_dict in enumerate(local):
                        for key, val in local_dict.items():
                            local_val = val
                            remote_val = remote[idx].get(key)
                            if isinstance(local_val, six.string_types):
                                local_val = local_val.lower()
                            if isinstance(remote_val, six.string_types):
                                remote_val = remote_val.lower()
                            if local_val != remote_val:
                                ret["changes"] = {"new": {record_str: record}}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Record set {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Record set {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "zone_name": zone_name,
                "resource_group": resource_group,
                "record_type": record_type,
                "etag": etag,
                "metadata": metadata,
                "ttl": ttl,
            },
        }
        for record in record_vars:
            # pylint: disable=eval-used
            if eval(record):
                # pylint: disable=eval-used
                ret["changes"]["new"][record] = eval(record)

    if ctx["test"]:
        ret["comment"] = "Record set {0} would be created.".format(name)
        ret["result"] = None
        return ret

    rec_set_kwargs = kwargs.copy()
    rec_set_kwargs.update(connection_auth)

    rec_set = await hub.exec.azurerm.dns.record_set.create_or_update(
        ctx=ctx,
        name=name,
        zone_name=zone_name,
        resource_group=resource_group,
        record_type=record_type,
        if_match=if_match,
        if_none_match=if_none_match,
        etag=etag,
        ttl=ttl,
        metadata=metadata,
        arecords=arecords,
        aaaa_records=aaaa_records,
        mx_records=mx_records,
        ns_records=ns_records,
        ptr_records=ptr_records,
        srv_records=srv_records,
        txt_records=txt_records,
        cname_record=cname_record,
        soa_record=soa_record,
        caa_records=caa_records,
        **rec_set_kwargs,
    )

    if "error" not in rec_set:
        ret["result"] = True
        ret["comment"] = f"Record set {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} record set {1}! ({2})".format(
        action, name, rec_set.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub,
    ctx,
    name,
    zone_name,
    resource_group,
    record_type,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a record set does not exist in the DNS zone.

    :param name:
        Name of the record set.

    :param zone_name:
        Name of the DNS zone.

    :param resource_group:
        The resource group assigned to the DNS zone.

    :param record_type:
        The type of DNS record in this record set. Record sets of type SOA can be updated but not created
        (they are created when the DNS zone is created). Possible values include: 'A', 'AAAA', 'CAA', 'CNAME',
        'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    rec_set = await hub.exec.azurerm.dns.record_set.get(
        ctx,
        name,
        zone_name,
        resource_group,
        record_type,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in rec_set:
        ret["result"] = True
        ret["comment"] = "Record set {0} was not found in zone {1}.".format(
            name, zone_name
        )
        return ret

    if ctx["test"]:
        ret["comment"] = "Record set {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": rec_set,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.dns.record_set.delete(
        ctx, name, zone_name, resource_group, record_type, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Record set {0} has been deleted.".format(name)
        ret["changes"] = {"old": rec_set, "new": {}}
        return ret

    ret["comment"] = "Failed to delete record set {0}!".format(name)
    return ret
