# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Webhook State Module

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

    .. code-block:: yaml

        Ensure container registry webhook exists:
            azurerm.containerregistry.webhook.present:
                - name: testhook
                - registry_name: testrepo
                - resource_group: testgroup
                - service_uri: http://idem.eitr.tech/webhook
                - actions:
                    - push
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

        Ensure container registry webhook is absent:
            azurerm.containerregistry.webhook.absent:
                - name: testhook
                - registry_name: testrepo
                - resource_group: testgroup

"""
# Import Python libs
from dict_tools import differ
import logging


log = logging.getLogger(__name__)


async def present(
    hub,
    ctx,
    name,
    registry_name,
    resource_group,
    service_uri,
    actions,
    custom_headers=None,
    status="enabled",
    scope=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Ensure a container registry webhook exists.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param service_uri: The service URI for the webhook to post notifications.

    :param actions: The list of actions that trigger the webhook to post notifications. Possible values include
        'chart_delete', 'chart_push', 'delete', 'push', and 'quarantine'

    :param custom_headers: A dictionary of custom headers that will be added to the webhook notifications.

    :param status: The status of the webhook at the time the operation was called. Possible values are 'enabled' and
        'disabled'

    :param scope: The scope of repositories where the event can be triggered. For example, ``foo:>>*<<`` means events
        for all tags under repository ``foo``. ``foo:bar`` means events for ``foo:bar`` only. ``foo`` is equivalent to
        ``foo:latest``. Empty means all events.

    :param tags: A dictionary of strings can be passed as tag metadata to the object.

    Example usage:

    .. code-block:: yaml

        Ensure container registry webhook exists:
            azurerm.containerregistry.webhook.present:
                - name: testhook
                - registry_name: testrepo
                - resource_group: testgroup
                - service_uri: http://idem.eitr.tech/webhook
                - actions:
                    - push
                - status: enabled
                - customer_headers:
                    X-Custom-Header: idem
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"
    new = {}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    # populate dictionary of settings for changes output on creation
    for param in [
        "name",
        "registry_name",
        "resource_group",
        "service_uri",
        "actions",
        "custom_headers",
        "status",
        "scope",
        "tags",
    ]:
        value = locals()[param]
        if value is not None:
            new[param] = value

    # get existing container registry webhook if present
    hook = await hub.exec.azurerm.containerregistry.webhook.get(
        ctx,
        name,
        registry_name,
        resource_group,
        callback_config=True,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in hook:
        action = "update"

        # sku changes
        if service_uri.upper() != hook["service_uri"].upper():
            ret["changes"]["service_uri"] = {
                "old": hook["service_uri"],
                "new": service_uri,
            }

        # actions changes
        old_act = sorted([act.lower() for act in hook["actions"]])
        actions = sorted([act.lower() for act in actions])
        if old_act != actions:
            ret["changes"]["actions"] = {
                "old": old_act,
                "new": actions,
            }

        # custom_headers changes
        head_diff = differ.deep_diff(
            hook.get("custom_headers", {}), custom_headers or {}
        )
        if head_diff:
            ret["changes"]["tags"] = head_diff

        # status changes
        if status.upper() != hook["status"].upper():
            ret["changes"]["status"] = {"old": hook["status"], "new": status}

        # scope changes
        if scope:
            if scope.upper() != hook["scope"].upper():
                ret["changes"]["scope"] = {"old": hook["scope"], "new": scope}

        # tag changes
        tag_diff = differ.deep_diff(hook.get("tags", {}), tags or {})
        if tag_diff:
            ret["changes"]["tags"] = tag_diff

        if not ret["changes"]:
            ret["result"] = True
            ret[
                "comment"
            ] = "Container registry webhook {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Container registry webhook {0} would be updated.".format(
                name
            )
            ret["result"] = None
            return ret

    elif ctx["test"]:
        ret["comment"] = "Container registry webhook {0} would be created.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": {},
            "new": new,
        }
        return ret

    hook_kwargs = kwargs.copy()
    hook_kwargs.update(connection_auth)

    hook = await hub.exec.azurerm.containerregistry.webhook.create_or_update(
        ctx=ctx,
        name=name,
        registry_name=registry_name,
        resource_group=resource_group,
        service_uri=service_uri,
        actions=actions,
        custom_headers=custom_headers,
        status=status,
        scope=scope,
        tags=tags,
        **hook_kwargs,
    )

    if "error" not in hook:
        ret["result"] = True
        ret["comment"] = f"Container registry webhook {name} has been {action}d."
        if not ret["changes"]:
            ret["changes"] = {"old": {}, "new": new}
        return ret

    ret["comment"] = "Failed to {0} container registry webhook {1}! ({2})".format(
        action, name, hook.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, registry_name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Ensure a webhook does not exist in a container registry.

    :param name: Name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    .. code-block:: yaml

        Ensure container registry webhook is absent:
            azurerm.containerregistry.webhook.absent:
                - name: testhook
                - registry_name: testrepo
                - resource_group: testgroup

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

    hook = await hub.exec.azurerm.containerregistry.webhook.get(
        ctx,
        name,
        registry_name,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in hook:
        ret["result"] = True
        ret["comment"] = "Container registry webhook {0} is already absent.".format(
            name
        )
        return ret

    if ctx["test"]:
        ret["comment"] = "Container registry webhook {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": hook,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.containerregistry.webhook.delete(
        ctx, name, registry_name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Container registry webhook {0} has been deleted.".format(name)
        ret["changes"] = {"old": hook, "new": {}}
        return ret

    ret["comment"] = "Failed to delete container registry webhook {0}!".format(name)
    return ret
