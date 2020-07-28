# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry State Module

.. versionadded:: 3.0.0

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

    Example configuration for Azure Resource Manager authentication:

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

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        Ensure container registry exists:
            azurerm.containerregistry.registry.present:
                - name: testrepo
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

        Ensure container registry is absent:
            azurerm.containerregistry.registry.absent:
                - name: other_repo

"""
# Import Python libs
from dict_tools import differ
import logging


log = logging.getLogger(__name__)


async def present(
    hub, ctx, name, resource_group, tags=None, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Ensure a container registry exists.

    :param name: Name of the resource group.

    :param tags: A dictionary of strings can be passed as tag metadata to the object.

    Example usage:

    .. code-block:: yaml

        Ensure container registry exists:
            azurerm.containerregistry.registry.present:
                - name: testrepo
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

    acr = {}

    acr = await hub.exec.azurerm.containerregistry.registry.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in acr:
        action = "update"
        ret["changes"] = differ.deep_diff(group.get("tags", {}), tags or {})

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Container registry {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Container registry {0} tags would be updated.".format(
                name
            )
            ret["result"] = None
            ret["changes"] = {"old": group.get("tags", {}), "new": tags}
            return ret

    elif ctx["test"]:
        ret["comment"] = "Container registry {0} would be created.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": {},
            "new": {"name": name, "tags": tags,},
        }
        return ret

    acr_kwargs = kwargs.copy()
    acr_kwargs.update(connection_auth)

    acr = await hub.exec.azurerm.containerregistry.registry.create_or_update(
        ctx, name, resource_group, tags=tags, **acr_kwargs
    )

    if "error" not in acr:
        ret["result"] = True
        ret["comment"] = f"Container registry {name} has been {action}d."
        ret["changes"] = {"old": {}, "new": acr}
        return ret

    ret["comment"] = "Failed to {0} container registry {1}! ({2})".format(
        action, name, acr.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a container registry does not exist in a resource group.

    :param name: Name of the container registry.

    :param resource_group:

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

    acr = {}

    acr = await hub.exec.azurerm.containerregistry.registry.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in acr:
        ret["result"] = True
        ret["comment"] = "Container registry {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Container registry {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": acr,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.containerregistry.registry.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Container registry {0} has been deleted.".format(name)
        ret["changes"] = {"old": acr, "new": {}}
        return ret

    ret["comment"] = "Failed to delete container registry {0}!".format(name)
    return ret
