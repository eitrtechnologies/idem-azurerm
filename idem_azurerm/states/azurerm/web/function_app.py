# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Function App State Module

.. versionadded:: VERSION

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


# Azure libs
HAS_LIBS = False
try:
    from msrestazure.tools import is_valid_resource_id

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


async def present(
    hub,
    ctx,
    name,
    resource_group,
    server_farm_id=None,
    plan_name=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: VERSION

    Ensure that a Function App exists. An App Service Plan will be built for the Function App unless the server_farm_id
        parameter is specified.

    :param name: The name of the Function App.

    :param resource_group: The name of the resource group of the Function App.

    :param server_farm_id: The resource ID of the App Service Plan used by the Function App. If this parameter is not 
        provided then an App Service Plan will be built automatically for your Function App.
  
    :param plan_name: The name of the App Service Plan to create when the server_farm_id parameter is not specified.
        Defaults to "ASP-{name}"

    :param tags: A dictionary of strings representing tag metadata for the Function App.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure function app exists:
            azurerm.web.function_app.present:
                - name: my_app
                - resource_group: my_group
                - server_farm_id: my_id
                - tags:
                    "owner": "EITR Technologies"
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

    if server_farm_id and not is_valid_resource_id(server_farm_id):
        log.error("The specified server_farm_id is invalid.")
        ret["comment"] = "The specified server_farm_id is invalid."
        return ret

    if not server_farm_id:
        if not plan_name:
            plan_name = f"ASP-{name}"

        plan = await hub.exec.azurerm.web.app_service_plan.get(
            ctx, name=plan_name, resource_group=resource_group
        )

        if "error" in plan:
            plan = await hub.exec.azurerm.web.app_service_plan.create_or_update(
                ctx,
                name=plan_name,
                resource_group=resource_group,
                kind="functionapp",
                reserved=True,
                sku="Y1",
                **connection_auth,
            )

            if "error" in plan:
                log.error(
                    f"Unable to create the App Service Plan {plan_name} in the resource group {resource_group}."
                )
                ret[
                    "comment"
                ] = f"Unable to create the App Service Plan {plan_name} in the resource group {resource_group}."
                return ret

        server_farm_id = plan["id"]

    function_app = await hub.exec.azurerm.web.app.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in function_app:
        action = "update"
        tag_changes = differ.deep_diff(function_app.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if function_app.get("server_farm_id") != server_farm_id:
            ret["changes"]["server_farm_id"] = {
                "new": server_farm_id,
                "old": function_app.get("server_farm_id"),
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Function App {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Function App {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "server_farm_id": server_farm_id,
                "tags": tags,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Function App {0} would be created.".format(name)
        ret["result"] = None
        return ret

    app_kwargs = kwargs.copy()
    app_kwargs.update(connection_auth)

    function_app = await hub.exec.azurerm.web.app.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        tags=tags,
        server_farm_id=server_farm_id,
        kind="functionapp",
        **app_kwargs,
    )

    if "error" not in function_app:
        ret["result"] = True
        ret["comment"] = f"Function App {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Function App {1}! ({2})".format(
        action, name, function_app.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: VERSION

    Ensure a Function App does not exist within the specified resource group.

    :param name: The name of the Function App.

    :param resource_group: The name of the resource group of the Function App.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure function app is absent:
            azurerm.web.function_app.absent:
                - name: my_app
                - resource_group: my_group
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

    function_app = await hub.exec.azurerm.web.app.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in function_app:
        ret["result"] = True
        ret["comment"] = "Function App {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Function App {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": function_app,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.web.app.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Function App {0} has been deleted.".format(name)
        ret["changes"] = {"old": function_app, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Function App {0}!".format(name)
    return ret
