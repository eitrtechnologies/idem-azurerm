# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Blob Container State Module

.. versionadded:: 2.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as a dictionary of
    keyword arguments to the ``connection_auth`` parameter in order to work properly. Since the authentication
    parameters are sensitive, it's recommended to pass them to the states via pillar.

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

    Example Pillar for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass
            mysubscription:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD

"""
# Python libs
from __future__ import absolute_import
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
    tags=None,
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

    :param tags: A dictionary of strings can be passed as tag metadata to the container object.

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
                - tags:
                    contact_name: Elmer Fudd Gantry
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
        name, account, resource_group, **connection_auth
    )
    existed = False

    if "error" not in container:
        existed = True

        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(
            container.get("tags", {}), tags or {}
        )
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        metadata_changes = await hub.exec.utils.dictdiffer.deep_diff(
            container.get("metadata", {}), metadata or {}
        )
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

        if tags:
            ret["changes"]["new"]["tags"] = tags
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

    if not existed:
        container = await hub.exec.azurerm.storage.container.create(
            name=name,
            account=account,
            resource_group=resource_group,
            tags=tags,
            public_access=public_access,
            metadata=metadata,
            **container_kwargs,
        )

    else:
        container = await hub.exec.azurerm.storage.container.update(
            name=name,
            account=account,
            resource_group=resource_group,
            tags=tags,
            public_access=public_access,
            metadata=metadata,
            **container_kwargs,
        )

    if "error" not in container:
        ret["result"] = True
        ret["comment"] = "Blob container {0} has been created.".format(name)
        return ret

    ret["comment"] = "Failed to create blob container {0}! ({1})".format(
        name, container.get("error")
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
    tags=None,
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

    :param tags: A dictionary of strings can be passed as tag metadata to the container object.

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
                - tags:
                    contact_name: Elmer Fudd Gantry
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
        name, account, resource_group, if_match, **connection_auth
    )

    if "error" not in policy:
        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(
            policy.get("tags", {}), tags or {}
        )
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

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

        if tags:
            ret["changes"]["new"]["tags"] = tags
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
        name=name,
        account=account,
        resource_group=resource_group,
        tags=tags,
        if_match=if_match,
        immutability_period=immutability_period,
        **policy_kwargs,
    )

    if "error" not in policy:
        ret["result"] = True
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} has been created.".format(
            name
        )
        return ret

    ret[
        "comment"
    ] = "Failed to create the immutability policy of the blob container {0}! ({1})".format(
        name, policy.get("error")
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
        name, account, resource_group, **connection_auth
    )

    if "error" in container:
        ret["result"] = True
        ret["comment"] = "Blob container {0} was not found.".format(name)
        return ret

    elif ctx["test"]:
        ret["comment"] = "Blob container {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": container,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.storage.container.delete(
        name, account, resource_group, **connection_auth
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
        name, account, resource_group, if_match, **connection_auth
    )

    if "error" in policy:
        ret["result"] = True
        ret[
            "comment"
        ] = "The immutability policy of the blob container {0} was not found.".format(
            name
        )
        return ret

    elif ctx["test"]:
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
        name, account, resource_group, if_match, **connection_auth
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
