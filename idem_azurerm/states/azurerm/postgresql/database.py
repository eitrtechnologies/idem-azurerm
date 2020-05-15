# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Database Operations State Module

.. versionadded:: 2.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-rdbms <https://pypi.org/project/azure-mgmt-rdbms/>`_ >= 1.9.0
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

    database = await hub.exec.azurerm.postgresql.database.get(
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in database:
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

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "server_name": server_name,
                "resource_group": resource_group,
            },
        }

        if charset:
            ret["changes"]["new"]["charset"] = charset
        if collation:
            ret["collation"]["new"]["collation"] = collation

    if ctx["test"]:
        ret["comment"] = "Database {0} would be created.".format(name)
        ret["result"] = None
        return ret

    database_kwargs = kwargs.copy()
    database_kwargs.update(connection_auth)

    database = await hub.exec.azurerm.postgresql.database.create_or_update(
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        charset=charset,
        collation=collation,
        **database_kwargs,
    )

    if "error" not in database:
        ret["result"] = True
        ret["comment"] = "Database {0} has been created.".format(name)
        return ret

    ret["comment"] = "Failed to create Database {0}! ({1})".format(
        name, database.get("error")
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

    database = await hub.exec.azurerm.postgresql.database.get(
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

    elif ctx["test"]:
        ret["comment"] = "Database {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": database,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.postgresql.database.delete(
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
