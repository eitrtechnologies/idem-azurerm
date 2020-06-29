# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key Vault Secret State Module

.. versionadded:: 2.4.0

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

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging

log = logging.getLogger(__name__)

TREQ = {"present": {"require": ["states.azurerm.keyvault.vault.present",]}}


async def present(
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
    version=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.4.0

    Ensure the specified secret exists within the given key vault. Requires secrets/set permission. Secret properties
    can be specified as keyword arguments.

    :param name: The name of the secret. Secret names can only contain alphanumeric characters and dashes.

    :param value: The value of the secret.

    :param vault_url: The URL of the vault that the client will access.

    :param content_type: An arbitrary string indicating the type of the secret.

    :param enabled: Whether the secret is enabled for use.

    :param expires_on: When the secret will expire, in UTC. This parameter must be a string representation of a Datetime
        object in ISO-8601 format.

    :param not_before: The time before which the secret cannot be used, in UTC. This parameter must be a string
        representation of a Datetime object in ISO-8601 format.

    :param tags: A dictionary of strings can be passed as tag metadata to the secret.

    :param version: By default, a new version of the secret will not be created if the name is already in use UNLESS
        the value of the secret is changed. Secret properties will be updated on the latest version unless otherwise
        specified with this parameter. Set ``version`` to ``new`` in order to forse the creation of a new secret
        version.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure secret exists:
            azurerm.keyvault.secret.present:
                - name: secretname
                - value: supersecret
                - content_type: "text/plain"
                - vault_url: "https://myvault.vault.azure.net/"
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

    secret = await hub.exec.azurerm.keyvault.secret.get_secret(
        ctx=ctx,
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in secret:
        action = "update"
        if value != secret.get("value"):
            ret["changes"]["value"] = {
                "old": "REDACTED_OLD_VALUE",
                "new": "REDACTED_NEW_VALUE",
            }

        if tags:
            tag_changes = differ.deep_diff(
                secret.get("properties", {}).get("tags", {}) or {}, tags or {}
            )
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        if content_type:
            if (
                content_type.lower()
                != (secret.get("properties", {}).get("content_type", "") or "").lower()
            ):
                ret["changes"]["content_type"] = {
                    "old": secret.get("properties", {}).get("content_type"),
                    "new": content_type,
                }

        if enabled is not None:
            if enabled != secret.get("properties", {}).get("enabled"):
                ret["changes"]["enabled"] = {
                    "old": secret.get("properties", {}).get("enabled"),
                    "new": enabled,
                }

        if expires_on:
            if expires_on != secret.get("properties", {}).get("expires_on"):
                ret["changes"]["expires_on"] = {
                    "old": secret.get("properties", {}).get("expires_on"),
                    "new": expires_on,
                }

        if not_before:
            if not_before != secret.get("properties", {}).get("not_before"):
                ret["changes"]["not_before"] = {
                    "old": secret.get("properties", {}).get("not_before"),
                    "new": not_before,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Secret {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Secret {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "name": {"new": name},
            "value": {"new": "REDACTED_VALUE"},
        }

        if tags:
            ret["changes"]["tags"] = {"new": tags}
        if content_type:
            ret["changes"]["content_type"] = {"new": content_type}
        if enabled is not None:
            ret["changes"]["enabled"] = {"new": enabled}
        if expires_on:
            ret["changes"]["expires_on"] = {"new": expires_on}
        if not_before:
            ret["changes"]["not_before"] = {"new": not_before}

    if ctx["test"]:
        ret["comment"] = "Secret {0} would be created.".format(name)
        ret["result"] = None
        return ret

    secret_kwargs = kwargs.copy()
    secret_kwargs.update(connection_auth)
    secret = {}

    if ret["changes"].get("value"):
        secret = await hub.exec.azurerm.keyvault.secret.set_secret(
            ctx=ctx, name=name, value=value, vault_url=vault_url, **secret_kwargs
        )

    if [key for key in ret["changes"] if key not in ["name", "value"]]:
        secret = await hub.exec.azurerm.keyvault.secret.update_secret_properties(
            ctx=ctx,
            name=name,
            vault_url=vault_url,
            version=version,
            content_type=content_type,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
            **secret_kwargs,
        )

    if "error" not in secret:
        ret["result"] = True
        ret["comment"] = f"Secret {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Secret {1}! ({2})".format(
        action, name, secret.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, vault_url, purge=False, wait=False, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 2.4.0

    Ensure the specified secret does not exist within the given key vault.

    :param name: The name of the secret to delete.

    :param vault_url: The URL of the vault that the client will access.

    :param purge: Permanently deletes a deleted secret. Possible only in vaults with soft-delete enabled. Performs an
        irreversible deletion of the specified secret, without possibility for recovery. The operation is not available
        if the ``recovery_level`` does not specify 'Purgeable'.

    :param wait: When this method returns, Key Vault has begun deleting the secret. Deletion may take several seconds in
        a vault with soft-delete enabled. Setting this parameter to ``True`` enables you to wait for deletion to
        complete.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key is absent:
            azurerm.keyvault.secret.absent:
                - name: secretname
                - vault_url: "https://myvault.vault.azure.net/"

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "delete"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    secret = await hub.exec.azurerm.keyvault.secret.get_secret(
        ctx=ctx,
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in secret:
        action = "purge"
        if purge:
            secret = await hub.exec.azurerm.keyvault.secret.get_deleted_secret(
                ctx=ctx,
                name=name,
                vault_url=vault_url,
                azurerm_log_level="info",
                **connection_auth,
            )
        if "error" in secret:
            ret["result"] = True
            ret["comment"] = f"Secret {name} was not found."
            return ret

    if ctx["test"]:
        ret["comment"] = f"Secret {name} would be {action}d."
        ret["result"] = None
        ret["changes"] = {
            "old": secret,
            "new": {},
        }
        return ret

    if action == "delete":
        deleted = await hub.exec.azurerm.keyvault.secret.delete_secret(
            ctx=ctx, name=name, vault_url=vault_url, wait=wait, **connection_auth
        )

    if purge:
        action = "purge"
        deleted = await hub.exec.azurerm.keyvault.secret.purge_deleted_secret(
            ctx=ctx, name=name, vault_url=vault_url, **connection_auth
        )

    if deleted:
        ret["result"] = True
        ret["comment"] = f"Secret {name} has been {action}d."
        ret["changes"] = {"old": secret, "new": {}}
        return ret

    ret["comment"] = f"Failed to {action} Secret {name}!"
    return ret
