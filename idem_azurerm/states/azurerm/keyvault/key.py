# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key State Module

.. versionadded:: 2.0.0

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

TREQ = {"present": {"require": ["states.azurerm.keyvault.vault.present"]}}


async def present(
    hub,
    ctx,
    name,
    key_type,
    vault_url,
    key_operations=None,
    size=None,
    curve=None,
    hardware_protected=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensure the specified key exists within the given key vault. Requires keys/create permission. Key properties can be
    specified as keyword arguments.

    :param name: The name of the new key. Key names can only contain alphanumeric characters and dashes.

    :param key_type: The type of key to create. Possible values include: 'ec', 'ec_hsm', 'oct', 'rsa', 'rsa_hsm'.

    :param vault_url: The URL of the vault that the client will access.

    :param key_operations: A list of permitted key operations. Possible values include: 'decrypt', 'encrypt',
        'sign', 'unwrap_key', 'verify', 'wrap_key'.

    :param size: RSA key size in bits, for example 2048, 3072, or 4096. Applies to RSA keys only.

    :param curve: Elliptic curve name. Defaults to the NIST P-256 elliptic curve. Possible values include:
        "P-256", "P-256K", "P-384", "P-521".

    :param enabled: Whether the key is enabled for use.

    :param expires_on: When the key will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: The time before which the key can not be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: Application specific metadata in the form of key-value pairs.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key exists:
            azurerm.keyvault.key.present:
                - name: my_key
                - key_type: my_type
                - vault_url: my_vault
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

    key = await hub.exec.azurerm.keyvault.key.get_key(
        ctx=ctx,
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if key_type != "oct":
        key_type = key_type.upper().replace("_", "-")

    if "error" not in key:
        action = "update"
        if tags:
            tag_changes = differ.deep_diff(
                key.get("properties", {}).get("tags", {}) or {}, tags or {}
            )
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        if isinstance(key_operations, list):
            if sorted(key_operations) != sorted(key.get("key_operations", [])):
                ret["changes"]["key_operations"] = {
                    "old": key.get("key_operations"),
                    "new": key_operations,
                }

        if enabled is not None:
            if enabled != key.get("properties", {}).get("enabled"):
                ret["changes"]["enabled"] = {
                    "old": key.get("properties", {}).get("enabled"),
                    "new": enabled,
                }

        if hardware_protected is not None:
            if enabled != key.get("properties", {}).get("hardware_protected"):
                ret["changes"]["hardware_protected"] = {
                    "old": key.get("properties", {}).get("hardware_protected"),
                    "new": hardware_protected,
                }

        if expires_on:
            if expires_on != key.get("properties", {}).get("expires_on"):
                ret["changes"]["expires_on"] = {
                    "old": key.get("properties", {}).get("expires_on"),
                    "new": expires_on,
                }

        if not_before:
            if not_before != key.get("properties", {}).get("not_before"):
                ret["changes"]["not_before"] = {
                    "old": key.get("properties", {}).get("not_before"),
                    "new": not_before,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Key {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Key {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Key {0} would be created.".format(name)
        ret["result"] = None
        return ret

    key_kwargs = kwargs.copy()
    key_kwargs.update(connection_auth)

    key = await hub.exec.azurerm.keyvault.key.create_key(
        ctx=ctx,
        name=name,
        vault_url=vault_url,
        key_type=key_type,
        tags=tags,
        key_operations=key_operations,
        enabled=enabled,
        hardware_protected=hardware_protected,
        not_before=not_before,
        expires_on=expires_on,
        size=size,
        curve=curve,
        **key_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": key}

    if "error" not in key:
        ret["result"] = True
        ret["comment"] = f"Key {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Key {1}! ({2})".format(
        action, name, key.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, vault_url, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensure the specified key does not exist within the given key vault.

    :param name: The name of the key to delete.

    :param vault_url: The URL of the vault that the client will access.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key is absent:
            azurerm.keyvault.key.absent:
                - name: my_key
                - vault_url: my_vault

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

    key = await hub.exec.azurerm.keyvault.key.get_key(
        ctx=ctx,
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in key:
        ret["result"] = True
        ret["comment"] = "Key {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Key {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": key,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.keyvault.key.begin_delete_key(
        ctx=ctx, name=name, vault_url=vault_url, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Key {0} has been deleted.".format(name)
        ret["changes"] = {"old": key, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Key {0}!".format(name)
    return ret
