# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key Execution Module

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
import datetime
import logging

# Azure libs
HAS_LIBS = False
try:
    from azure.keyvault.keys import KeyClient
    from azure.core.exceptions import (
        ResourceNotFoundError,
        HttpResponseError,
        ResourceExistsError,
    )
    from msrest.exceptions import ValidationError, SerializationError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def get_key_client(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Load the key client and return a KeyClient object.

    :param vault_url: The URL of the vault that the client will access.
    """
    credential = await hub.exec.azurerm.utils.get_identity_credentials(ctx, **kwargs)

    key_client = KeyClient(vault_url=vault_url, credential=credential)

    return key_client


def _key_as_dict(key):
    result = {}
    attrs = ["id", "key_operations", "key_type", "name", "properties"]
    for attr in attrs:
        val = getattr(key, attr)
        if attr == "properties":
            val = _key_properties_as_dict(val)
        result[attr] = val
    return result


def _key_properties_as_dict(key_properties):
    result = {}
    props = [
        "created_on",
        "enabled",
        "expires_on",
        "id",
        "managed",
        "name",
        "not_before",
        "recovery_level",
        "tags",
        "updated_on",
        "vault_url",
        "version",
    ]
    for prop in props:
        val = getattr(key_properties, prop)
        if isinstance(val, datetime.datetime):
            val = val.isoformat()
        result[prop] = val
    return result


async def backup_key(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Back up a key in a protected form useable only by Azure Key Vault. Requires key/backup permission. This is intended
        to allow copying a key from one vault to another. Both vaults must be owned by the same Azure subscription.
        Also, backup / restore cannot be performed across geopolitical boundaries. For example, a backup from a vault
        in a USA region cannot be restored to a vault in an EU region.

    :param name: The name of the key to back up.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.backup_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        backup = kconn.backup_key(name=name)

        result = backup
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def begin_delete_key(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Delete all versions of a key and its cryptographic material. Requires keys/delete permission. If the vault has
        soft-delete enabled, deletion may take several seconds to complete.

    :param name: The name of the key to delete.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.begin_delete_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.begin_delete_key(name=name)

        key.wait()
        result = _key_as_dict(key.result())
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def begin_recover_deleted_key(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Recover a deleted key to its latest version. Possible only in a vault with soft-delete enabled. Requires
        keys/recover permission. If the vault does not have soft-delete enabled, the begin_delete_key operation is permanent,
        and this method will raise an error. Attempting to recover a non-deleted key will also raise an error.

    :param name: The name of the deleted key to recover.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.begin_recover_deleted_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.begin_recover_deleted_key(name=name)

        key.wait()
        result = _key_as_dict(key.result())
    except HttpResponseError as exc:
        result = {"error": str(exc)}

    return result


async def create_ec_key(
    hub,
    ctx,
    name,
    vault_url,
    curve=None,
    key_operations=None,
    hardware_protected=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Create a new elliptic curve key or, if name is already in use, create a new version of the key. Requires the
        keys/create permission. Key properties can be specified as keyword arguments.

    :param name: The name of the new key. Key names can only contain alphanumeric characters and dashes.

    :param vault_url: The URL of the vault that the client will access.

    :param curve: (Optional) Elliptic curve name. Defaults to the NIST P-256 elliptic curve. Possible values include:
        "P-256", "P-256K", "P-384", "P-521".

    :param key_operations: (Optional) A list of permitted key operations. Possible values include: 'decrypt', 'encrypt',
        'sign', 'unwrap_key', 'verify', 'wrap_key'.

    :param hardware_protected: (Optional) A boolean value specifying whether the key should be created in a hardware
        security module. Defaults to False.

    :param enabled: (Optional) A boolean value specifying whether the key is enabled for use.

    :param expires_on: (Optional) When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: (Optional) The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: (Optional) Application specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.create_ec_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.create_ec_key(
            name=name,
            curve=curve,
            key_operations=key_operations,
            hardware_protected=hardware_protected,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
        )

        result = _key_as_dict(key)
    except (ValidationError, HttpResponseError) as exc:
        result = {"error": str(exc)}

    return result


async def create_key(
    hub,
    ctx,
    name,
    key_type,
    vault_url,
    key_operations=None,
    size=None,
    curve=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Create a key or, if name is already in use, create a new version of the key. Requires keys/create permission.
        Key properties can be specified as keyword arguments.

    :param name: The name of the new key. Key names can only contain alphanumeric characters and dashes.

    :param key_type: The type of key to create. Possible values include: 'ec', 'ec_hsm', 'oct', 'rsa', 'rsa_hsm'.

    :param vault_url: The URL of the vault that the client will access.

    :param key_operations: (Optional) A list of permitted key operations. Possible values include: 'decrypt', 'encrypt',
        'sign', 'unwrap_key', 'verify', 'wrap_key'.

    :param size: (Optional) RSA key size in bits, for example 2048, 3072, or 4096. Applies to RSA keys only.

    :param curve: (Optional) Elliptic curve name. Defaults to the NIST P-256 elliptic curve. Possible values include:
        "P-256", "P-256K", "P-384", "P-521".

    :param enabled: (Optional) Whether the key is enabled for use.

    :param expires_on: (Optional) When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: (Optional) The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: (Optional) Application specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.create_key test_name test_type test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    if key_type != "oct":
        key_type = key_type.upper().replace("_", "-")

    try:
        key = kconn.create_key(
            name=name,
            key_type=key_type,
            enabled=enabled,
            size=size,
            curve=curve,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
            key_operations=key_operations,
        )

        result = _key_as_dict(key)
    except (ValidationError, HttpResponseError) as exc:
        result = {"error": str(exc)}

    return result


async def create_rsa_key(
    hub,
    ctx,
    name,
    vault_url,
    size=None,
    key_operations=None,
    hardware_protected=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Create a new RSA key or, if name is already in use, create a new version of the key. Requires the keys/create
        permission. Key properties can be specified as keyword arguments.

    :param name: The name of the new key. Key names can only contain alphanumeric characters and dashes.

    :param vault_url: The URL of the vault that the client will access.

    :param size: (Optional) Key size in bits, for example 2048, 3072, or 4096.

    :param key_operations: (Optional) A list of permitted key operations. Possible values include: 'decrypt', 'encrypt',
        'sign', 'unwrap_key', 'verify', 'wrap_key'.

    :param hardware_protected: (Optional) A boolean value specifying whether the key should be created in a hardware
        security module. Defaults to False.

    :param enabled: (Optional) Whether the key is enabled for use.

    :param expires_on: (Optional) When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: (Optional) The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: (Optional) Application specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.create_rsa_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.create_rsa_key(
            name=name,
            key_operations=key_operations,
            size=size,
            hardware_protected=hardware_protected,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
        )

        result = _key_as_dict(key)
    except (ValidationError, HttpResponseError) as exc:
        result = {"error": str(exc)}

    return result


async def get_deleted_key(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Get a deleted key. Possible only in a vault with soft-delete enabled. Requires keys/get permission.

    :param name: The name of the key.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.get_deleted_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.get_deleted_key(name=name)

        result = _key_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def get_key(hub, ctx, name, vault_url, version=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Get a key's attributes and, if it's an asymmetric key, its public material. Requires keys/get permission.

    :param name: The name of the key to get.

    :param vault_url: The URL of the vault that the client will access.

    :param version: (Optional) Used to specify the version of the key to get. If not specified, gets the latest
        version of the key.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.get_key test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.get_key(name=name, version=version)

        result = _key_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def import_key(
    hub,
    ctx,
    name,
    vault_url,
    hardware_protected=None,
    enabled=None,
    not_before=None,
    expires_on=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Import a key created externally. Requires keys/import permission. If name is already in use, the key will be
        imported as a new version. Parameters used to build a JSONWebKey object will be passed to this module. More
        information about some of those parameters can be found at the following link:
        https://tools.ietf.org/html/draft-ietf-jose-json-web-key-18.

    :param name: The name of the imported key.

    :param vault_url: The URL of the vault that the client will access.

    :param hardware_protected: (Optional) A boolean value specifying whether the key should be created in a hardware
        security module. Defaults to False.

    :param enabled: (Optional) A boolean value specifying whether the key is enabled for use.

    :param expires_on: (Optional) When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: (Optional) The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: (Optional) Application specific metadata in the form of key-value pairs.

    Additional parameters passed as keyword arguments are used to build a JSONWebKey object will be passed to this
        module. Below some of those parameters are defined. More information about some of those parameters can be
        found at the following link: https://tools.ietf.org/html/draft-ietf-jose-json-web-key-18.

    :param kid: Key identifier.

    :param kty: Key type. Possible values inclide: 'ec', 'ec_hsm', 'oct', 'rsa', 'rsa_hsm'.

    :param key_ops: A list of allow operations for the key. Possible elements of the list include: 'decrypt',
        'encrypt', 'sign', 'unwrap_key', 'verify', 'wrap_key'

    :param n: RSA modulus.

    :param e: RSA public exponent.

    :param d: RSA private exponent, or the D component of the EC private key.

    :param dp: RSA private key parameter.

    :param dq: RSA private key parameter.

    :param qi: RSA private key parameter.

    :param p: RSA secret prime.

    :param q: RSA secret prime, with p < q.

    :param k: Symmetric key.

    :param t: HSM Token, used with 'Bring Your Own Key'.

    :param crv: Elliptic curve name. Posible values include: 'p_256', 'p_256_k', 'p_384', and 'p_521'.

    :param x: X component of an EC public key.

    :param y: Y component of an EC public key.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.import_key test_name test_vault test_webkey_params

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    if kwargs["key_type"] != "oct":
        kwargs["key_type"] = kwargs.get("key_type").upper().replace("_", "-")

    try:
        keymodel = await hub.exec.azurerm.utils.create_object_model(
            "keyvault-keys", "JsonWebKey", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        key = kconn.import_key(
            name=name,
            hardware_protected=hardware_protected,
            enabled=enabled,
            tags=tags,
            not_before=not_before,
            expires_on=expires_on,
            key=keymodel,
        )

        result = _key_as_dict(key)
    except (HttpResponseError, ResourceNotFoundError) as exc:
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    List identifiers and properties of all keys in the vault. Requires keys/list permission.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.list test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        keys = kconn.list_properties_of_keys()

        for key in keys:
            result[key.name] = _key_properties_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def list_properties_of_key_versions(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    List the identifiers and properties of a key's versions. Requires keys/list permission.

    :param name: The name of the key.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.list_properties_of_key_versions test_name test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        keys = kconn.list_properties_of_key_versions(name=name)

        for key in keys:
            result[key.name] = _key_properties_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def list_deleted_keys(hub, ctx, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all deleted keys, including the public part of each. Possible only in a vault with soft-delete enabled.
        Requires keys/list permission.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.list_deleted_keys test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        keys = kconn.list_deleted_keys()

        for key in keys:
            result[key.name] = _key_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result


async def purge_deleted_key(hub, ctx, name, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Permanently deletes a deleted key. Only possible in a vault with soft-delete enabled. Performs an irreversible
        deletion of the specified key, without possibility for recovery. The operation is not available if the
        recovery_level does not specify 'Purgeable'. This method is only necessary for purging a key before its
        scheduled_purge_date. Requires keys/purge permission.

    :param name: The name of the deleted key to purge.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.purge_deleted_key test_name test_vault

    """
    result = False
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.purge_deleted_key(name=name,)

        result = True
    except HttpResponseError as exc:
        result = {"error": str(exc)}

    return result


async def restore_key_backup(hub, ctx, backup, vault_url, **kwargs):
    """
    .. versionadded:: 2.0.0

    Restore a key backup to the vault. This imports all versions of the key, with its name, attributes, and access
        control policies. If the key's name is already in use, restoring it will fail. Also, the target vault must be
        owned by the same Microsoft Azure subscription as the source vault. Requires keys/restore permission.

    :param backup: A key backup as returned by the backup_key operation.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.restore_key_backup test_backup test_vault

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.restore_key_backup(backup=backup,)

        result = _key_as_dict(key)
    except (ResourceExistsError, SerializationError) as exc:
        result = {"error": str(exc)}

    return result


async def update_key_properties(
    hub,
    ctx,
    name,
    vault_url,
    version=None,
    key_operations=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Change a key's properties (not its cryptographic material). Requires keys/update permission. Key properties that
        need to be updated can be specified as keyword arguments.

    :param name: The name of the key to update.

    :param vault_url: The URL of the vault that the client will access.

    :param version: (Optional) Used to specify the version of the key to update. If no version is specified, the latest
        version of the key will be updated.

    :param key_operations: (Optional) A list of permitted key operations. Possible values include: 'decrypt', 'encrypt',
        'sign', 'unwrap_key', 'verify', 'wrap_key'.

    :param enabled: (Optional) Whether the key is enabled for use.

    :param expires_on: (Optional) When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: (Optional) The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: (Optional) Application specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.update_key_properties test_name test_vault test_version

    """
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(ctx, vault_url, **kwargs)

    try:
        key = kconn.update_key_properties(
            name=name,
            version=version,
            key_operations=key_operations,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
        )

        result = _key_as_dict(key)
    except ResourceNotFoundError as exc:
        result = {"error": str(exc)}

    return result
