# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key Vault Secret Execution Module

.. versionadded:: 2.4.0

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
import datetime
import logging

# Azure libs
HAS_LIBS = False
try:
    from azure.keyvault.secrets import SecretClient
    from azure.core.exceptions import (
        ResourceNotFoundError,
        HttpResponseError,
        ResourceExistsError,
    )
    from msrest.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


async def get_secret_client(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Load the secret client and return a SecretClient object.

    :param vault_url: The URL of the vault that the client will access.

    """
    credential = await hub.exec.azurerm.utils.get_identity_credentials(ctx, **kwargs)

    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    return secret_client


def _secret_as_dict(secret):
    """
    Helper function to turn a KeyVaultSecret object into a dictionary.
    """
    result = {}
    attrs = ["id", "value", "name", "properties"]
    for attr in attrs:
        try:
            val = getattr(secret, attr)
            if attr == "properties":
                val = _secret_properties_as_dict(val)
            result[attr] = val
        except AttributeError:
            pass
    return result


def _secret_properties_as_dict(props):
    """
    Helper function to turn a SecretProperties object into a dictionary.
    """
    result = {}
    attrs = [
        "content_type",
        "created_on",
        "enabled",
        "expires_on",
        "id",
        "key_id",
        "name",
        "not_before",
        "recovery_level",
        "tags",
        "updated_on",
        "vault_url",
        "version",
    ]
    for attr in attrs:
        try:
            val = getattr(props, attr)
            if isinstance(val, datetime.datetime):
                val = val.isoformat()
            result[attr] = val
        except AttributeError:
            pass
    return result


async def backup_secret(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Back up a secret in a protected form useable only by Azure Key Vault. Requires secrets/backup permission. This is
    intended to allow copying a secret from one vault to another. Both vaults must be owned by the same Azure
    subscription. Also, backup/restore cannot be performed across geopolitical boundaries. For example, a backup from a
    vault in a US region cannot be restored to a vault in an EU region.

    :param name: The name of the secret to back up.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.backup_secret secretname https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        result = sconn.backup_secret(name=name,)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def delete_secret(hub, ctx, name, vault_url, wait=False, **kwargs):
    """
    .. versionadded:: 2.4.0

    Delete all versions of a secret. Requires secrets/delete permission.

    :param name: The name of the secret to delete.

    :param vault_url: The URL of the vault that the client will access.

    :param wait: When this method returns, Key Vault has begun deleting the secret. Deletion may take several seconds in
        a vault with soft-delete enabled. Setting this parameter to ``True`` enables you to wait for deletion to
        complete.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.delete_secret secretname https://myvault.vault.azure.net/

    """
    result = False
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.begin_delete_secret(name=name,)

        if wait:
            secret.wait()

        result = True
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def recover_deleted_secret(hub, ctx, name, vault_url, wait=False, **kwargs):
    """
    .. versionadded:: 2.4.0

    Recover a deleted secret to its latest version. Possible only in a vault with soft-delete enabled. If the vault does
    not have soft-delete enabled, ``delete_secret`` is permanent, and this method will return an error. Attempting to
    recover a non-deleted secret will also return an error.

    Requires the secrets/recover permission.

    :param name: The name of the deleted secret to recover.

    :param vault_url: The URL of the vault that the client will access.

    :param wait: When this method returns, Key Vault has begun recovering the secret. Recovery may take several seconds.
        Setting this parameter to ``True`` enables you to wait for recovery to complete.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.recover_deleted_secret secretname https://myvault.vault.azure.net/

    """
    result = False
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.begin_recover_deleted_secret(name=name,)

        if wait:
            secret.wait()

        result = True
    except HttpResponseError as exc:
        result = {"error": str(exc)}

    return result


async def get_deleted_secret(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Get a deleted secret. Possible only in vaults with soft-delete enabled. Requires secrets/get permission.

    :param name: The name of the deleted secret.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.get_deleted_secret secretname https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.get_deleted_secret(name=name,)

        result = _secret_as_dict(secret)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def get_secret(hub, ctx, name, vault_url, version=None, **kwargs):
    """
    .. versionadded:: 2.4.0

    Get a secret. Requires the secrets/get permission.

    :param name: The name of the secret to get.

    :param vault_url: The URL of the vault that the client will access.

    :param version: An optional parameter used to specify the version of the secret to get. If not specified, gets the
        latest version of the secret.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.get_secret secretname https://myvault.vault.azure.net/ test_version

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.get_secret(name=name, version=version,)

        result = _secret_as_dict(secret)
    except (HttpResponseError, ResourceNotFoundError) as exc:
        result = {"error": str(exc)}

    return result


async def list_deleted_secrets(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Lists all deleted secrets. Possible only in vaults with soft-delete enabled. Requires secrets/list permission.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.list_deleted_secrets https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secrets = sconn.list_deleted_secrets()

        for secret in secrets:
            result[secret.name] = _secret_as_dict(secret)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def list_properties_of_secret_versions(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    List properties of all versions of a secret, excluding their values. Requires secrets/list permission.

    List items don't include secret values. Use ``get_secret`` to get a secret's value.

    :param name: The name of the secret.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.list_properties_of_secret_versions secretname https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secrets = sconn.list_properties_of_secret_versions(name=name,)

        for secret in secrets:
            result[secret.name] = _secret_properties_as_dict(secret)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def list_properties_of_secrets(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    List identifiers and attributes of all secrets in the vault. Requires secrets/list permission.

    List items don't include secret values. Use ``get_secret`` to get a secret's value.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.list_properties_of_secrets https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secrets = sconn.list_properties_of_secrets()

        for secret in secrets:
            result[secret.name] = _secret_properties_as_dict(secret)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def purge_deleted_secret(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Permanently deletes a deleted secret. Possible only in vaults with soft-delete enabled.

    Performs an irreversible deletion of the specified secret, without possibility for recovery. The operation is not
    available if the recovery_level does not specify 'Purgeable'. This method is only necessary for purging a secret
    before its scheduled_purge_date.

    Requires secrets/purge permission.

    :param name: The name of the deleted secret to purge.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.purge_deleted_secret secretname https://myvault.vault.azure.net/

    """
    result = False
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.purge_deleted_secret(name=name,)

        result = True
    except HttpResponseError as exc:
        result = {"error": str(exc)}

    return result


async def restore_secret_backup(hub, ctx, backup, vault_url, **kwargs):
    """
    .. versionadded:: 2.4.0

    Restore a backed up secret. Requires the secrets/restore permission. If the secret's name is already in use,
    restoring it will fail. Also, the target vault must be owned by the same Microsoft Azure subscription as the source
    vault.

    :param backup: A secret backup as returned by the ``backup_secret`` execution module.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.restore_secret_backup secretbackup https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.restore_secret_backup(backup=backup,)

        result = _secret_as_dict(secret)
    except (ResourceExistsError, SerializationError) as exc:
        result = {"error": str(exc)}

    return result


async def set_secret(
    hub,
    ctx,
    name,
    value,
    vault_url,
    content_type=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.4.0

    .. versionchanged:: 4.0.0

    Set a secret value. If name is in use, create a new version of the secret. If not, create a new secret. Requires
    secrets/set permission.

    :param name: The name of the secret to set.

    :param value: The value of the secret to set.

    :param vault_url: The URL of the vault that the client will access.

    :param content_type: An arbitrary string indicating the type of the secret.

    :param enabled: Whether the secret is enabled for use.

    :param expires_on: When the secret will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: The time before which the secret cannot be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: A dictionary of strings can be passed as tag metadata to the secret.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.set_secret test_name test_secret https://myvault.vault.azure.net/

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.set_secret(
            name=name,
            value=value,
            content_type=content_type,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
        )

        result = _secret_as_dict(secret)
    except (
        HttpResponseError,
        ResourceNotFoundError,
        ResourceExistsError,
        SerializationError,
    ) as exc:
        result = {"error": str(exc)}

    return result


async def update_secret_properties(
    hub,
    ctx,
    name,
    vault_url,
    version=None,
    content_type=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.4.0

    Update properties of a secret other than its value. Requires secrets/set permission. This method updates properties
    of the secret, such as whether it's enabled, but can't change the secret's value. Use ``set_secret`` to change the
    secret's value.

    :param name: The name of the secret.

    :param vault_url: The URL of the vault that the client will access.

    :param version: An optional parameter used to specify the version of the secret to update. If no version is
        specified, the latest version of the secret will be updated.

    :param content_type: An arbitrary string indicating the type of the secret.

    :param enabled: Whether the secret is enabled for use.

    :param expires_on: When the secret will expire, in UTC. This parameter must be a string representation of a Datetime
        object in ISO-8601 format.

    :param not_before: The time before which the secret can not be used, in UTC. This parameter must be a string
        representation of a Datetime object in ISO-8601 format.

    :param tags: Application specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.secret.update_secret_properties secretname https://myvault.vault.azure.net/ enabled=False

    """
    result = {}
    sconn = await hub.exec.azurerm.keyvault.secret.get_secret_client(
        ctx, vault_url, **kwargs
    )

    try:
        secret = sconn.update_secret_properties(
            name=name,
            version=version,
            content_type=content_type,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
        )

        result = _secret_as_dict(secret)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result
