# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Blob Container State Module

.. versionadded:: 2.0.0

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

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.storage.account.present",
        ]
    }
}


async def present(
    hub,
    ctx,
    name,
    account,
    resource_group,
    public_access=None,
    metadata=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a blob container exists.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param public_access: Specifies whether data in the container may be accessed publicly and the level of access.
        Possible values include: 'Container', 'Blob', 'None'. Defaults to None.

    :param metadata: A dictionary of name-value pairs to associate with the container as metadata. Defaults to None.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure blob container exists:
            azurerm.storage.container.present:
                - name: my_container
                - account: my_account
                - resource_group: my_rg
                - public_access: 'Blob'
                - connection_auth: {{ profile }}

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

    container = await hub.exec.azurerm.storage.container.get(
        ctx, name, account, resource_group, **connection_auth
    )

    if "error" not in container:
        action = "update"

        metadata = metadata or {}
        metadata_changes = differ.deep_diff(container.get("metadata", {}), metadata)
        if metadata_changes:
            ret["changes"]["metadata"] = metadata_changes

        if public_access and public_access != container.get("public_access"):
            ret["changes"]["public_access"] = {
                "old": container.get("public_access"),
                "new": public_access,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Blob container {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Blob container {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "account": account,
                "resource_group": resource_group,
            },
        }

        if public_access:
            ret["changes"]["new"]["public_access"] = public_access
        if metadata:
            ret["changes"]["new"]["metadata"] = metadata

    if ctx["test"]:
        ret["comment"] = "Blob container {0} would be created.".format(name)
        ret["result"] = None
        return ret

    container_kwargs = kwargs.copy()
    container_kwargs.update(connection_auth)

    if action == "create":
        container = await hub.exec.azurerm.storage.container.create(
            ctx=ctx,
            name=name,
            account=account,
            resource_group=resource_group,
            public_access=public_access,
            metadata=metadata,
            **container_kwargs,
        )

    else:
        container = await hub.exec.azurerm.storage.container.update(
            ctx=ctx,
            name=name,
            account=account,
            resource_group=resource_group,
            public_access=public_access,
            metadata=metadata,
            **container_kwargs,
        )

    if "error" not in container:
        ret["result"] = True
        ret["comment"] = f"Blob container {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} blob container {1}! ({2})".format(
        action, name, container.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def immutability_policy_present(
    hub,
    ctx,
    name,
    account,
    resource_group,
    immutability_period,
    if_match=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensures that the immutability policy of a specified blob container exists. The container must be of account kind
        'StorageV2' in order to utilize an immutability policy.

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
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not. Defaults to None.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure immutability policy exists:
            azurerm.storage.container.immutability_policy_present:
                - name: my_container
                - account: my_account
                - resource_group: my_rg
                - immutability_period: 10
                - connection_auth: {{ profile }}

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

    policy = await hub.exec.azurerm.storage.container.get_immutability_policy(
        ctx, name, account, resource_group, if_match, **connection_auth
    )

    if "error" not in policy:
        action = "update"

        if immutability_period != policy.get(
            "immutability_period_since_creation_in_days"
        ):
            ret["changes"]["immutability_period_since_creation_in_days"] = {
                "old": policy.get("immutability_period_since_creation_in_days"),
                "new": immutability_period,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret[
                "comment"
            ] = "The immutability policy of the blob container {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "The immutability policy of the blob container {0} would be updated.".format(
                name
            )
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "account": account,
                "resource_group": resource_group,
                "immutability_period_since_creation_in_days": immutability_period,
            },
        }

        if if_match:
            ret["changes"]["new"]["if_match"] = if_match

    if ctx["test"]:
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} would be created.".format(
            name
        )
        ret["result"] = None
        return ret

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(connection_auth)

    policy = await hub.exec.azurerm.storage.container.create_or_update_immutability_policy(
        ctx=ctx,
        name=name,
        account=account,
        resource_group=resource_group,
        if_match=if_match,
        immutability_period=immutability_period,
        **policy_kwargs,
    )

    if "error" not in policy:
        ret["result"] = True
        ret[
            "comment"
        ] = f"The immutability policy of the blob container {name} has been {action}d."
        return ret

    ret[
        "comment"
    ] = "Failed to {0} the immutability policy of the blob container {1}! ({2})".format(
        action, name, policy.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, account, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Ensures a specified blob container does not exist.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml
        Ensure blob container is absent:
            azurerm.storage.container.absent:
                - name: my_container
                - account: my_account
                - resource_group: my_rg
                - connection_auth: {{ profile }}

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

    container = await hub.exec.azurerm.storage.container.get(
        ctx, name, account, resource_group, **connection_auth
    )

    if "error" in container:
        ret["result"] = True
        ret["comment"] = "Blob container {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Blob container {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": container,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.storage.container.delete(
        ctx, name, account, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Blob container {0} has been deleted.".format(name)
        ret["changes"] = {"old": container, "new": {}}
        return ret

    ret["comment"] = "Failed to delete blob container {0}!".format(name)
    return ret


async def immutability_policy_absent(
    hub,
    ctx,
    name,
    account,
    resource_group,
    if_match=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensures that the immutability policy of a specified blob container does not exist.

    :param name: The name of the blob container within the specified storage account. Blob container names must be
        between 3 and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-)
        character must be immediately preceded and followed by a letter or number.

    :param account: The name of the storage account within the specified resource group. Storage account names must be
        between 3 and 24 characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group within the user's subscription. The name is case insensitive.

    :param if_match: The entity state (ETag) version of the immutability policy to update. It is important to note that
        the ETag must be passed as a string that includes double quotes. For example, '"8d7b4bb4d393b8c"' is a valid
        string to pass as the if_match parameter, but "8d7b4bb4d393b8c" is not. Defaults to None.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml
        Ensure immutability policy is absent:
            azurerm.storage.container.absent:
                - name: my_container
                - account: my_account
                - resource_group: my_rg
                - if_match: '"my_etag"'
                - connection_auth: {{ profile }}

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

    policy = await hub.exec.azurerm.storage.container.get_immutability_policy(
        ctx, name, account, resource_group, if_match, **connection_auth
    )

    if "error" in policy:
        ret["result"] = True
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} was not found.".format(
            name
        )
        return ret

    if ctx["test"]:
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} would be deleted.".format(
            name
        )
        ret["result"] = None
        ret["changes"] = {
            "old": policy,
            "new": {},
        }
        return ret

    if not if_match:
        if_match = policy.get("etag")

    deleted = await hub.exec.azurerm.storage.container.delete_immutability_policy(
        ctx, name, account, resource_group, if_match, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} has been deleted.".format(
            name
        )
        ret["changes"] = {"old": policy, "new": {}}
        return ret

    ret[
        "comment"
    ] = "Failed to delete the immutability policy of the blob container {0}!".format(
        name
    )
    return ret
