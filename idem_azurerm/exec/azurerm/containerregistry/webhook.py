# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Webhook Execution Module

.. versionadded:: 3.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

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

"""
# Python libs
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.containerregistry  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass


__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


async def create_or_update(
    hub,
    ctx,
    name,
    registry_name,
    resource_group,
    service_uri,
    actions,
    custom_headers=None,
    status=None,
    scope=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates a webhook for a container registry with the specified parameters.

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

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.webhook.create_or_update testhook testrepo testgroup

    """
    result = {}

    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            ctx, resource_group, **kwargs
        )

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {
                "error": "Unable to determine location from resource group specified."
            }
        kwargs["location"] = rg_props["location"]

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    try:
        hookmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerregistry",
            "WebhookCreateParameters",
            service_uri=service_uri,
            actions=actions,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        hook = regconn.webhooks.create(
            webhook_name=name,
            registry_name=registry_name,
            resource_group_name=resource_group,
            webhook_create_parameters=hookmodel,
        )
        hook.wait()
        result = hook.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(
    hub, ctx, name, registry_name, resource_group, callback_config=False, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Gets the properties of the specified webhook.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param callback_config: Gets the configuration of service URI and custom headers for the webhook.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.webhook.get testhook testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.webhooks.get(
            webhook_name=name,
            registry_name=registry_name,
            resource_group_name=resource_group,
        )
        result = ret.as_dict()
        if callback_config:
            ret = regconn.webhooks.get_callback_config(
                webhook_name=name,
                registry_name=registry_name,
                resource_group_name=resource_group,
            )
            result.update(ret.as_dict())
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def ping(hub, ctx, name, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Triggers a ping event to be sent to the webhook.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.webhook.ping testhook testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.webhooks.ping(
            webhook_name=name,
            registry_name=registry_name,
            resource_group_name=resource_group,
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists all the webhooks for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.webhook.list testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        hooks = await hub.exec.azurerm.utils.paged_object_to_list(
            regconn.webhooks.list(
                registry_name=name, resource_group_name=resource_group
            )
        )
        for hook in hooks:
            result[hook["name"]] = hook
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_events(hub, ctx, name, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists recent events for the specified webhook.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.list_events testhook testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        events = await hub.exec.azurerm.utils.paged_object_to_list(
            regconn.webhooks.list_events(
                webhook_name=name,
                registry_name=registry_name,
                resource_group_name=resource_group,
            )
        )
        for event in events:
            result[event["id"]] = event
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Deletes a webhook from a container registry.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.webhook.delete testhook testrepo testgroup

    """
    result = False
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.webhooks.delete(
            webhook_name=name,
            registry_name=registry_name,
            resource_group_name=resource_group,
        )
        ret.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
