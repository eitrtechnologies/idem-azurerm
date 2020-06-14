# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Configuration Operations State Module

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
    value=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensures that a specific configuration setting exists with the given value for a specific PostgreSQL server. A list
        of configuration settings that can be updated for the given server can be found by using the list_by_server
        operation below. Additionally, all possible values for each individual configuration setting can be found
        using that module.

    :param name: The name of the server configuration.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param value: Value of the configuration. Defaults to None.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure configuration setting exists:
            azurerm.postgresql.configuration.present:
                - name: my_rule
                - server_name: my_server
                - resource_group: my_rg
                - value: config_value
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

    config = await hub.exec.azurerm.postgresql.configuration.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in config:
        action = "update"
        if value:
            if value != config.get("value"):
                ret["changes"]["value"] = {"old": config.get("value"), "new": value}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Configuration Setting {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Configuration Setting {0} would be updated.".format(name)
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

        if value:
            ret["changes"]["new"]["value"] = value

    if ctx["test"]:
        ret["comment"] = "Configuration Setting {0} would be created.".format(name)
        ret["result"] = None
        return ret

    config_kwargs = kwargs.copy()
    config_kwargs.update(connection_auth)

    config = await hub.exec.azurerm.postgresql.configuration.create_or_update(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        value=value,
        **config_kwargs,
    )

    if "error" not in config:
        ret["result"] = True
        ret["comment"] = f"Configuraton Setting {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Configuration Setting {1}! ({2})".format(
        action, name, config.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret
