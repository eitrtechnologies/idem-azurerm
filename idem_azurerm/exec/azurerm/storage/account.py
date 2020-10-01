# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Storage Account Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def check_name_availability(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 2.0.0

    Checks that the storage account name is valid and is not already in use.

    :param name: The name of the storage account.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.check_name_availability test_name

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        status = storconn.storage_accounts.check_name_availability(name=name)

        result = status.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create(
    hub,
    ctx,
    name,
    resource_group,
    sku,
    kind,
    location,
    custom_domain=None,
    network_rule_set=None,
    access_tier=None,
    azure_files_identity_based_auth=None,
    https_traffic_only=None,
    hns_enabled=None,
    large_file_shares=None,
    routing_preference=None,
    blob_public_access=None,
    minimum_tls_version=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Asynchronously creates a new storage account with the specified parameters. If an account is already created and a
    subsequent create request is issued with different properties, the account properties will be updated. If an
    account is already created and a subsequent create or update request is issued with the exact same set of
    properties, the request will succeed.

    :param name: The name of the storage account being created. Storage account names must be between 3 and 24
        characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param sku: The name of the storage account SKU. Possible values include: 'Standard_LRS', 'Standard_GRS',
        'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS', 'Premium_ZRS', 'Standard_GZRS', and 'Standard_RAGZRS'.

    :param kind: Indicates the type of storage account. Possible values include: 'Storage', 'StorageV2', 'BlobStorage',
        'FileStorage', and 'BlockBlobStorage'.

    :param location: Gets or sets the location of the resource. This will be one of the supported and registered Azure
        Geo Regions (e.g. West US, East US, Southeast Asia, etc.). The geo region of a resource cannot be changed once
        it is created, but if an identical geo region is specified on update, the request will succeed.

    :param custom_domain: User domain assigned to the storage account. Valid parameters are:

        - ``name``: Required. Gets or sets the custom domain name assigned to the storage account. Name is the CNAME
          source. To clear the existing custom domain, use an empty string for this property.
        - ``use_sub_domain_name``: Indicates whether indirect CName validation is enabled. Default value is False.
          This should only be set on updates.

    :param network_rule_set: A dictionary representing a NetworkRuleSet object.

    :param access_tier: The access tier is used for billing. Required for when the ``kind`` parameter is set to
        "BlobStorage". Possible values include: "Hot" and "Cool".

    :param azure_files_identity_based_auth: A dictionary representing an AzureFilesIdentityBasedAuthentication object.
        Provides the identity based authentication settings for Azure Files.

    :param https_traffic_only: Allows https traffic only to storage service if set to True. The default value is True.

    :param hns_enabled: A boolean flag specifying whether the account hierarchical namespace is enabled.

    :param large_file_shares: Allow large file shares if sets to 'Enabled'. It cannot be disabled once it is enabled.
        Possible values include: 'Disabled', 'Enabled'.

    :param routing_preference: A dictionary representing a RoutingPreference object. Maintains information about the
        network routing choice opted by the user for data transfer.

    :param blob_public_access: A boolean flag specifying whether public access is allowed to all blobs or containers in
        the storage account. The default value is True.

    :param minimum_tls_version: Set the minimum TLS version to be permitted on requests to storage. The default
        interpretation is TLS 1.0 for this property. Possible values include: 'TLS1_0', 'TLS1_1', 'TLS1_2'.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.create test_name test_group test_sku test_kind test_location

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    sku = {"name": sku}

    try:
        accountmodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "StorageAccountCreateParameters",
            sku=sku,
            kind=kind,
            location=location,
            custom_domain=custom_domain,
            network_rule_set=network_rule_set,
            access_tier=access_tier,
            azure_files_identity_based_authentication=azure_files_identity_based_auth,
            enable_https_traffic_only=https_traffic_only,
            is_hns_enabled=hns_enabled,
            large_file_shares_state=large_file_shares,
            routing_preference=routing_preference,
            allow_blob_public_access=blob_public_access,
            minimum_tls_version=minimum_tls_version,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        account = storconn.storage_accounts.create(
            account_name=name,
            resource_group_name=resource_group,
            parameters=accountmodel,
        )

        account.wait()
        result = account.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Delete a storage account.

    :param name: The name of the storage account being deleted.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.delete test_name test_group

    """
    result = False
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        account = storconn.storage_accounts.delete(
            account_name=name, resource_group_name=resource_group
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)

    return result


async def failover(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Failover request can be triggered for a storage account in case of availability issues. The failover occurs from
    the storage account's primary cluster to secondary cluster for RA-GRS accounts. The secondary cluster will
    become primary after failover.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.failover test_name test_group

    """
    result = False
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        account = storconn.storage_accounts.failover(
            account_name=name, resource_group_name=resource_group
        )

        account.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)

    return result


async def get_properties(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Returns the properties for the specified storage account including but not limited to name, SKU name, location,
    and account status. The ListKeys operation should be used to retrieve storage keys.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.get_properties test_name test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        props = storconn.storage_accounts.get_properties(
            account_name=name, resource_group_name=resource_group
        )

        result = props.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Lists all the storage accounts available under the subscription. Note that storage keys are not returned; use the
    ListKeys operation for this.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        if resource_group:
            accounts = await hub.exec.azurerm.utils.paged_object_to_list(
                storconn.storage_accounts.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            accounts = await hub.exec.azurerm.utils.paged_object_to_list(
                storconn.storage_accounts.list()
            )

        for account in accounts:
            result[account["name"]] = account
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_account_sas(
    hub,
    ctx,
    name,
    resource_group,
    services,
    resource_types,
    permissions,
    shared_access_expiry_time,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    List SAS credentials of a storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param services: The signed services accessible with the account SAS. Possible values include: Blob (b), Queue (q),
        Table (t), File (f). Possible values include: 'b', 'q', 't', 'f'.

    :param resource_types: The signed resource types that are accessible with the account SAS. Service (s): Access to
        service-level APIs; Container (c): Access to container-level APIs; Object (o): Access to object-level APIs for
        blobs, queue messages, table entities, and files. Possible values include: 's', 'c', 'o'.

    :param permissions: The signed permissions for the account SAS. Possible values include: Read (r), Write (w), Delete
        (d), List (l), Add (a), Create (c), Update (u) and Process (p). Possible values include: 'r', 'd', 'w', 'l',
        'a', 'c', 'u', 'p'.

    :param shared_access_expiry_time: The time at which the shared access signature becomes invalid. This parameter
        must be a string representation of a Datetime object in ISO-8601 format.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_account_sas test_name test_group test_services test_types test_perms test_time

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        accountmodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "AccountSasParameters",
            permissions=permissions,
            shared_access_expiry_time=shared_access_expiry_time,
            resource_types=resource_types,
            services=services,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        creds = storconn.storage_accounts.list_account_sas(
            account_name=name,
            resource_group_name=resource_group,
            parameters=accountmodel,
        )

        result = creds.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_keys(hub, ctx, name, resource_group, expand=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Lists the access keys or Kerberos keys (if active directory enabled) for the specified storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param expand: Specifies type of the key to be listed. Possible values include: 'kerb'. Defaults to None.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_keys test_name test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)
    try:
        keys = storconn.storage_accounts.list_keys(
            account_name=name, resource_group_name=resource_group, expand=expand
        )

        result = keys.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_service_sas(
    hub,
    ctx,
    name,
    resource_group,
    canonicalized_resource,
    permissions,
    shared_access_expiry_time,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    List service SAS credentials of a specific resource.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param canonicalized_resource: The canonical path to the signed resource.

    :param permissions: The signed permissions for the service SAS. Possible values include: Read (r), Write (w),
        Delete (d), List (l), Add (a), Create (c), Update (u) and Process (p). Possible values include: 'r', 'd', 'w',
        'l', 'a', 'c', 'u', 'p'.

    :param shared_access_expiry_time: The time at which the shared access signature becomes invalid. This parameter
        must be a string representation of a Datetime object in ISO-8601 format.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_service_sas test_name test_group test_resource test_perms test_time

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        servicemodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "ServiceSasParameters",
            permissions=permissions,
            canonicalized_resource=canonicalized_resource,
            shared_access_expiry_time=shared_access_expiry_time,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        creds = storconn.storage_accounts.list_service_sas(
            account_name=name,
            resource_group_name=resource_group,
            parameters=servicemodel,
        )

        result = creds.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def regenerate_key(hub, ctx, name, resource_group, key_name, **kwargs):
    """
    .. versionadded:: 2.0.0

    Regenerates one of the access keys or Kerberos keys for the specified storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param key_name: The name of storage keys that want to be regenerated. Possible values are key1, key2, kerb1, kerb2.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.renegerate_key test_name test_group test_key

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        keys = storconn.storage_accounts.regenerate_key(
            resource_group_name=resource_group,
            account_name=name,
            key_name=key_name,
            **kwargs,
        )

        result = keys.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
