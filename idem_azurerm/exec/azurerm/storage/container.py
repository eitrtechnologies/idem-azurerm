# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Blob Container Operations Execution Module

.. versionadded:: 2.0.0

.. versionchanged:: 3.0.0, 4.0.0

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
import datetime
import sys

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.storage  # pylint: disable=unused-import
    from azure.storage.blob import BlobClient, BlobServiceClient, ContainerClient
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import SerializationError
    from azure.core.exceptions import HttpResponseError, ResourceExistsError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def _blob_properties_as_dict(blob_properties):
    result = {}
    props = [
        "name",
        "container",
        "snapshot",
        "blob_type",
        "metadata",
        "last_modified",
        "etag",
        "size",
        "append_blob_committed_block_count",
        "page_blob_sequence_number",
        "server_encrypted",
        "copy",
        "content_settings",
        "lease",
        "blob_tier",
        "blob_tier_change_time",
        "blob_tier_inferred",
        "deleted",
        "deleted_time",
        "remaining_retention_days",
        "creation_time",
        "archive_status",
        "encryption_key_sha256",
        "request_server_encrypted",
    ]
    for prop in props:
        val = getattr(blob_properties, prop)
        if isinstance(val, datetime.datetime):
            val = val.isoformat()
        result[prop] = val
    return result


async def get_client(
    hub, ctx, client_type, account, resource_group, container=None, blob=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Load the specified blob service, container, or blob client and return a BlobServiceClient, ContainerClient, or
    BlobClient object, respectively.

    :param client_type: The type of client to create. Possible values are "BlobService", "Blob", and "Container".

    :param account: The name of the storage account.

    :param resource_group: The name of the resource group containing the specified storage account.

    :param container: The name of the container.

    :param blob: The name of the blob.

    """
    result = {}
    storage_acct = await hub.exec.azurerm.storage.account.get_properties(
        ctx, name=account, resource_group=resource_group
    )

    if "error" in storage_acct:
        raise sys.exit(
            f"The storage account {account} does not exist within the specified resource group {resource_group}."
        )

    # Retrieves the connection keys for the storage account
    storage_acct_keys = await hub.exec.azurerm.storage.account.list_keys(
        ctx, name=account, resource_group=resource_group
    )
    if "error" not in storage_acct_keys:
        storage_acct_key = storage_acct_keys["keys"][0]["value"]
        # Builds the connection string for the blob service client using the account access key
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={account};AccountKey={storage_acct_key};EndpointSuffix=core.windows.net"
    else:
        raise sys.exit(
            f"Unable to get the account access key for the specified storage account {account} within the given resource group {resource_group}."
        )

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        if client_type.lower() == "blobservice":
            return blob_service_client
        if client_type.lower() == "container":
            container_client = blob_service_client.get_container_client(container)
            return container_client
        if client_type.lower() == "blob":
            blob_client = blob_service_client.get_blob_client(
                container=container, blob=blob
            )
            return blob_client
    except Exception as exc:
        raise sys.exit("error: " + str(exc))


async def clear_legal_hold(hub, ctx, name, account, resource_group, tags, **kwargs):
    """
    .. versionadded:: 2.0.0

    Clears legal hold tags. Clearing the same or non-existent tag results in an idempotent operation. ClearLegalHold
    clears out only the specified tags in the request.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param tags: Each tag should be 3 to 23 alphanumeric characters and is normalized to lower case at SRP.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.clear_legal_hold test_name test_account test_group test_tags

    """
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        hold = storconn.blob_containers.clear_legal_hold(
            container_name=name,
            resource_group_name=resource_group,
            account_name=account,
            tags=tags,
        )

        result = hold.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create(
    hub,
    ctx,
    name,
    account,
    resource_group,
    public_access,
    default_encryption_scope=None,
    deny_encryption_scope_override=None,
    metadata=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Creates a new container under the specified account as described by request body. The container resource includes
    metadata and properties for that container. It does not include a list of the blobs contained by the container.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param public_access: Specifies whether data in the container may be accessed publicly and the level of access.
        Possible values include: "Container", "Blob", "None".

    :param default_encryption_scope: Set the default encryption scope for the container to use for all writes.

    :param deny_encryption_scope_override: A boolean flag representing whether or not to block the override of the
        encryption scope from the container default.

    :param metadata: A dictionary of name-value pairs to associate with the container as metadata.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.create test_name test_account test_group test_access

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        containermodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "BlobContainer",
            default_encryption_scope=default_encryption_scope,
            deny_encryption_scope_override=deny_encryption_scope_override,
            public_access=public_access,
            metadata=metadata,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        container = storconn.blob_containers.create(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            blob_container=containermodel,
            **kwargs,
        )

        result = container.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (SerializationError, TypeError) as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def create_or_update_immutability_policy(
    hub,
    ctx,
    name,
    account,
    resource_group,
    immutability_period,
    if_match=None,
    protected_append_writes=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Creates or updates an unlocked immutability policy. ETag in If-Match is honored if given but not required for this
    operation. The container must be of account kind 'StorageV2' in order to utilize an immutability policy.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param immutability_period: The immutability period for the blobs in the container since the policy
        creation (in days).

    :param if_match: The entity state (ETag) version of the immutability policy to update. A value of "*" can be used
        to apply the operation only if the immutability policy already exists. If omitted, this operation will always
        be applied. It is important to note that any ETag must be passed as a string that includes double quotes.
        For example, '"8d7b4bb4d393b8c"' is a valid string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is
        not. Defaults to None.

    :param protected_append_writes: A boolean value specifying whether new blocks can be written to an append
        blob while maintaining immutability protection and compliance. Only new blocks can be added and any existing
        blocks cannot be modified or deleted. This property can only be changed for unlocked time-based retention
        policies.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.create_or_update_immutability_policy test_name test_account test_group test_period

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        policy = storconn.blob_containers.create_or_update_immutability_policy(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            immutability_period_since_creation_in_days=immutability_period,
            if_match=if_match,
            allow_protected_append_writes=protected_append_writes,
            **kwargs,
        )

        result = policy.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (SerializationError, TypeError) as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def upload_blob(
    hub,
    ctx,
    name,
    container,
    account,
    resource_group,
    file_path,
    blob_type="BlockBlob",
    overwrite=False,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates a new blob from a data source with automatic chunking.

    :param name: The blob with which to interact.

    :param container: The name of the blob container.

    :param account: The name of the storage account.

    :param resource_group: The name of the resource group.

    :param file_path: The path of the file to upload to the specified BlobContainer.

    :param blob_type: The type of the blob. Possible values include: "BlockBlob", "PageBlob" or "AppendBlob".
        The default value is "BlockBlob".

    :param overwrite: Whether the blob to be uploaded should overwrite the current data. If True, upload_blob will
        overwrite the existing data. If set to False, the operation will fail with ResourceExistsError. The exception
        to the above is with Append blob types. If set to False and the data already exists, an error will not be raised
        and the data will be appended to the existing blob. If set True, then the existing append blob will be deleted,
        and a new one created. Defaults to False.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.upload_blob test_name test_container test_account test_group test_path

    """
    result = {}

    blobconn = await hub.exec.azurerm.storage.container.get_client(
        ctx,
        client_type="Blob",
        account=account,
        resource_group=resource_group,
        container=container,
        blob=name,
        **kwargs,
    )

    try:
        with open(file_path, "rb") as data:
            container = blobconn.upload_blob(
                data=data, blob_type=blob_type, overwrite=overwrite, **kwargs
            )

        result = container
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (HttpResponseError, ResourceExistsError, FileNotFoundError) as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, account, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes specified container under its account.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.delete test_name test_account test_group

    """
    result = False
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        container = storconn.blob_containers.delete(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)

    return result


async def delete_immutability_policy(
    hub, ctx, name, account, resource_group, if_match, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Aborts an unlocked immutability policy. The response of delete has immutabilityPeriodSinceCreationInDays set to 0.
    ETag in If-Match is required for this operation. Deleting a locked immutability policy is not allowed, only way
    is to delete the container after deleting all blobs inside the container.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param if_match: The entity state (ETag) version of the immutability policy to update. It is important to note that
        the ETag must be passed as a string that includes double quotes. For example, '"8d7b4bb4d393b8c"' is a valid
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.delete_immutability_policy test_name test_account test_group test_if_match

    """
    result = False
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        policy = storconn.blob_containers.delete_immutability_policy(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            if_match=if_match,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)

    return result


async def extend_immutability_policy(
    hub, ctx, name, account, resource_group, immutability_period, if_match, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Extends the immutabilityPeriodSinceCreationInDays of a locked immutabilityPolicy. The only action allowed on a
    Locked policy will be this action. ETag in If-Match is required for this operation.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param immutability_period: The immutability period for the blobs in the container since the policy
        creation, in days.

    :param if_match: The entity state (ETag) version of the immutability policy to update. It is important to note that
        the ETag must be passed as a string that includes double quotes. For example, '"8d7b4bb4d393b8c"' is a valid
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.extend_immutability_policy test_name test_account test_group test_period test_if_match

    """
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        policy = storconn.blob_containers.extend_immutability_policy(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            immutability_period_since_creation_in_days=immutability_period,
            if_match=if_match,
            **kwargs,
        )

        result = policy
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, account, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets properties of a specified container.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.get test_name test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        container = storconn.blob_containers.get(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
        )

        result = container.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_immutability_policy(
    hub, ctx, name, account, resource_group, if_match=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Gets the existing immutability policy along with the corresponding ETag in response headers and body.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param if_match: The entity state (ETag) version of the immutability policy to update. It is important to note that
        the ETag must be passed as a string that includes double quotes. For example, '"8d7b4bb4d393b8c"' is a valid
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not. Defaults to None.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.get_immutability_policy test_name test_account test_group test_if_match

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        policy = storconn.blob_containers.get_immutability_policy(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            if_match=if_match,
        )

        result = policy.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def lease(
    hub,
    ctx,
    name,
    account,
    resource_group,
    lease_action,
    lease_duration=None,
    break_period=None,
    proposed_lease_id=None,
    lease_id=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    The Lease Container operation establishes and manages a lock on a container for delete operations. The lock duration
    can be 15 to 60 seconds, or can be infinite.

    :param container: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param lease_action: The lease action. Possible values include: 'Acquire', 'Renew', 'Change', 'Release', and
        'Break'.

    :param lease_duration: Specifies the duration of the lease, in seconds, or negative one (-1) for a lease that never
        expires. Required for the lease action "acquire".

    :param break_period: For a break action, proposed duration the lease should continue before it is broken, in
        seconds, between 0 and 60.

    :param proposed_lease_id: Proposed lease ID, in a GUID string format. Required for the lease action "change" and
        optional for the lease action "acquire".

    :param lease_id: Identifies the lease. Can be specified in any valid GUID string format.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.list test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        leasemodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "LeaseContainerRequest",
            action=lease_action,
            lease_id=lease_id,
            break_period=break_period,
            lease_duration=lease_duration,
            proposed_lease_id=proposed_lease_id,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        lease = storconn.blob_containers.lease(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            parameters=leasemodel,
        )

        result = lease.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(
    hub,
    ctx,
    account,
    resource_group,
    maxpagesize=None,
    list_filter=None,
    include_soft_deleted=True,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Lists all containers and does not support a prefix like data plane. Also SRP today does not return continuation
    token.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param maxpagesize: Specified maximum number of containers that can be included in the list.

    :param list_filter: When specified, only container names starting with the filter will be listed.

    :param include_soft_deleted: A boolean value representing whether to include the properties for soft deleted blob
        containers. Defaults to True.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.list test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        containers = await hub.exec.azurerm.utils.paged_object_to_list(
            storconn.blob_containers.list(
                account_name=account,
                resource_group_name=resource_group,
                maxpagesize=maxpagesize,
                filter=list_filter,
                include=include_soft_deleted,
                **kwargs,
            )
        )

        for container in containers:
            result[container["name"]] = container
    except (CloudError, AttributeError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_blobs(hub, ctx, name, account, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Get all blobs under the specified container.

    :param name: The name of the blob container.

    :param account: The name of the storage account.

    :param resource_group: The name of the resource_group.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.list_blobs test_name test_account test_group

    """
    result = {}
    containerconn = await hub.exec.azurerm.storage.container.get_client(
        ctx,
        client_type="Container",
        account=account,
        resource_group=resource_group,
        container=name,
        **kwargs,
    )

    try:
        blobs = containerconn.list_blobs()

        for blob in blobs:
            blob_props = _blob_properties_as_dict(blob)
            result[blob_props["name"]] = blob_props
    except (CloudError, AttributeError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except HttpResponseError as exc:
        result = {"error": str(exc)}

    return result


async def lock_immutability_policy(
    hub, ctx, name, account, resource_group, if_match, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Sets the ImmutabilityPolicy to Locked state. The only action allowed on a Locked policy is ExtendImmutabilityPolicy
    action. ETag in If-Match is required for this operation.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param if_match: The entity state (ETag) version of the immutability policy to update. It is important to note that
        the ETag must be passed as a string that includes double quotes. For example, '"8d7b4bb4d393b8c"' is a valid
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.lock_immutability_policy test_name test_account test_group test_if_match

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        policy = storconn.blob_containers.lock_immutability_policy(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            if_match=if_match,
            **kwargs,
        )

        result = policy
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def set_legal_hold(hub, ctx, name, account, resource_group, tags, **kwargs):
    """
    .. versionadded:: 2.0.0

    Sets legal hold tags. Setting the same tag results in an idempotent operation. SetLegalHold follows an append
    pattern and does not clear out the existing tags that are not specified in the request.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param tags: Each tag should be 3 to 23 alphanumeric characters and is normalized to lower case at SRP.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.set_legal_hold test_name test_account test_group test_tags

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        hold = storconn.blob_containers.set_legal_hold(
            container_name=name,
            resource_group_name=resource_group,
            account_name=account,
            tags=tags,
        )

        result = hold.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update(
    hub,
    ctx,
    name,
    account,
    resource_group,
    public_access,
    default_encryption_scope=None,
    deny_encryption_scope_override=None,
    metadata=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Updates container properties as specified in request body. Properties not mentioned in the request will be
    unchanged. Update fails if the specified container doesn't already exist.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param public_access: Specifies whether data in the container may be accessed publicly and the level of access.
        Possible values include: "Container", "Blob", "None".

    :param default_encryption_scope: Set the default encryption scope for the container to use for all writes.

    :param deny_encryption_scope_override: A boolean flag representing whether or not to block the override
        of the encryption scope from the container default.

    :param metadata: A dictionary of name-value pairs to associate with the container as metadata.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.container.update test_name test_account test_group test_access

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        containermodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "BlobContainer",
            default_encryption_scope=default_encryption_scope,
            deny_encryption_scope_override=deny_encryption_scope_override,
            public_access=public_access,
            metadata=metadata,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        container = storconn.blob_containers.update(
            container_name=name,
            account_name=account,
            resource_group_name=resource_group,
            blob_container=containermodel,
        )

        result = container.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (TypeError, SerializationError) as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result
