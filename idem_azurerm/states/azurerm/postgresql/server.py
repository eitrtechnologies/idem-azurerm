# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Operations State Module

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

TREQ = {"present": {"require": ["states.azurerm.resource.group.present",]}}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    location,
    sku=None,
    version=None,
    ssl_enforcement=None,
    storage_profile=None,
    login=None,
    login_password=None,
    create_mode="Default",
    force_password=False,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a specified PostgreSQL Server exists.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param location: The location the resource resides in.

    :param sku: The name of the SKU (pricing tier) of the server. Typically, the name of the sku is in the form
        tier_family_cores, e.g. B_Gen4_1, GP_Gen5_8.

    :param version: Server version. Possible values include: '9.5', '9.6', '10', '10.0', '10.2', '11'.

    :param ssl_enforcement: Enable ssl enforcement or not when connect to server.
        Possible values include: 'Enabled', 'Disabled'.

    :param storage_profile: A dictionary representing the storage profile of a server. Parameters include:
        - ``backup_retention_days``: Backup retention days for the server.
        - ``geo_redundant_backup``: Enable Geo-redundant or not for server backup. Possible values include:
            'Enabled', 'Disabled'.
        - ``storage_mb``: Max storage allowed for a server.
        - ``storage_autogrow``: Enable Storage Auto Grow. Possible values include: 'Enabled', 'Disabled'

    :param login: The administrator's login name of a server. Can only be specified when the server is being created
        (and is required for creation).

    :param login_password: The password of the administrator login.

    :param force_password: A Boolean flag that represents whether or not the password should be updated. If it is set
        to True, then the password will be updated if the server already exists. If it is set to False, then the
        password will not be updated unless other parameters also need to be updated. Defaults to False.

    :param tags: A dictionary of strings can be passed as tag metadata to the server.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure server exists:
            azurerm.postgresql.server.present:
                - name: my_server
                - resource_group: my_rg
                - location: my_location
                - login: my_login
                - login_password: my_password
                - tags:
                    contact_name: Elmer Fudd Gantry
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

    if sku and not isinstance(sku, dict):
        sku = {"name": sku}

    server = await hub.exec.azurerm.postgresql.server.get(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in server:
        action = "update"

        if tags:
            tag_changes = differ.deep_diff(server.get("tags", {}), tags or {})
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        if sku:
            if sku.get("name") != server.get("sku", {}).get("name"):
                ret["changes"]["sku"] = {
                    "old": server.get("sku").get("name"),
                    "new": sku.get("name"),
                }

        if storage_profile:
            profile_changes = differ.deep_diff(
                server.get("storage_profile", {}), storage_profile
            )
            if profile_changes:
                ret["changes"]["storage_profile"] = profile_changes

        if version:
            if version != server.get("version"):
                ret["changes"]["version"] = {
                    "old": server.get("version"),
                    "new": version,
                }

        if ssl_enforcement:
            if ssl_enforcement != server.get("ssl_enforcement"):
                ret["changes"]["ssl_enforcement"] = {
                    "old": server.get("ssl_enforcement"),
                    "new": ssl_enforcement,
                }

        if force_password:
            ret["changes"]["administrator_login_password"] = {"new": "REDACTED"}
        elif ret["changes"]:
            ret["changes"]["administrator_login_password"] = {"new": "REDACTED"}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Server {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Server {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "location": location,
                "create_mode": create_mode,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if sku:
            ret["changes"]["new"]["sku"] = sku
        if version:
            ret["changes"]["new"]["version"] = version
        if create_mode:
            ret["changes"]["new"]["create_mode"] = create_mode
        if ssl_enforcement:
            ret["changes"]["new"]["ssl_enforcement"] = ssl_enforcement
        if storage_profile:
            ret["changes"]["new"]["storage_profile"] = storage_profile
        if login:
            ret["changes"]["new"]["administrator_login"] = login
        if login_password:
            ret["changes"]["new"]["administrator_login_password"] = "REDACTED"  # nosec

    if ctx["test"]:
        ret["comment"] = "Server {0} would be created.".format(name)
        ret["result"] = None
        return ret

    server_kwargs = kwargs.copy()
    server_kwargs.update(connection_auth)

    if action == "create":
        server = await hub.exec.azurerm.postgresql.server.create(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            location=location,
            sku=sku,
            version=version,
            ssl_enforcement=ssl_enforcement,
            storage_profile=storage_profile,
            login=login,
            login_password=login_password,
            create_mode=create_mode,
            tags=tags,
            **server_kwargs,
        )
    else:
        server = await hub.exec.azurerm.postgresql.server.update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            sku=sku,
            version=version,
            ssl_enforcement=ssl_enforcement,
            storage_profile=storage_profile,
            login_password=login_password,
            tags=tags,
            **server_kwargs,
        )

    if "error" not in server:
        ret["result"] = True
        ret["comment"] = f"Server {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Server {1}! ({2})".format(
        action, name, server.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a specified PostgreSQL Server does not exist.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure server is absent:
            azurerm.postgresql.server.absent:
                - name: my_server
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

    server = await hub.exec.azurerm.postgresql.server.get(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in server:
        ret["result"] = True
        ret["comment"] = "Server {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Server {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": server,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.postgresql.server.delete(
        ctx=ctx, name=name, resource_group=resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Server {0} has been deleted.".format(name)
        ret["changes"] = {"old": server, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Server {0}!".format(name)
    return ret
