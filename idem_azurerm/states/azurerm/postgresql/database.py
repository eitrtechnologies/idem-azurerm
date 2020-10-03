# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Database Operations State Module

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
import logging

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.postgresql.server.present",
        ]
    }
}


async def present(
    hub,
    ctx,
    name,
    server_name,
    resource_group,
    charset=None,
    collation=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensures that the specified database exists within the given PostgreSQL database.

    :param name: The name of the database.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param charset: The charset of the database. Defaults to None.

    :param collation: The collation of the database. Defaults to None.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure database exists:
            azurerm.postgresql.database.present:
                - name: my_db
                - server_name: my_server
                - resource_group: my_rg

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

    database = await hub.exec.azurerm.postgresql.database.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in database:
        action = "update"
        if charset:
            if charset != database.get("charset"):
                ret["changes"]["charset"] = {
                    "old": database.get("charset"),
                    "new": charset,
                }

        if collation:
            if collation != database.get("collation"):
                ret["changes"]["collation"] = {
                    "old": database.get("collation"),
                    "new": collation,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Database {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Database {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Database {0} would be created.".format(name)
        ret["result"] = None
        return ret

    database_kwargs = kwargs.copy()
    database_kwargs.update(connection_auth)

    database = await hub.exec.azurerm.postgresql.database.create_or_update(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        charset=charset,
        collation=collation,
        **database_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": database}

    if "error" not in database:
        ret["result"] = True
        ret["comment"] = f"Database {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Database {1}! ({2})".format(
        action, name, database.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, server_name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Ensures that the specified database does not exist within the given PostgreSQL server.

    :param name: The name of the database.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure database is absent:
            azurerm.postgresql.database.absent:
                - name: my_rule
                - server_name: my_server
                - resource_group: my_rg

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

    database = await hub.exec.azurerm.postgresql.database.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in database:
        ret["result"] = True
        ret["comment"] = "Database {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Database {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": database,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.postgresql.database.delete(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Database {0} has been deleted.".format(name)
        ret["changes"] = {"old": database, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Database {0}!".format(name)
    return ret
