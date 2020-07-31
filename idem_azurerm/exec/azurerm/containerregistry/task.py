# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Task Execution Module

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
    task_type,
    platform_os,
    platform_arch,
    platform_variant=None,
    context_path=None,
    context_access_token=None,
    task_file_path=None,
    image_names=None,
    is_push_enabled=None,
    no_cache=None,
    target=None,
    encoded_task_content=None,
    encoded_values_content=None,
    values_file_path=None,
    values_dict=None,
    agent_num_cores=None,
    status=None,
    trigger=None,
    timeout=None,
    credential_login_mode=None,
    credential_login_server=None,
    credential_username=None,
    credential_password=None,
    identity_principal_id=None,
    identity_tenant_id=None,
    identity_type=None,
    user_assigned_identities=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates a task for a container registry with the specified parameters.

    :param name: The name of the webhook.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param task_type: The type of task to be scheduled. Must be 'DockerBuildStep', 'EncodedTaskStep', or 'FileTaskStep'.

    :param platform_os: The platform OS property against which the task has to happen. Accepts 'Windows' or 'Linux'.

    :param platform_arch: The platform architecture property against which the task has to happen.
        Accepts 'amd64', 'x86', or 'arm'

    :param platform_variant: The platform CPU variant property against which the run has to happen.
        Accepts 'v6', 'v7', or 'v8'

    :param context_path: (DockerBuildStep, EncodedTaskStep, FileTaskStep) The URL(absolute or relative) of the source
        context for the task step. The build context for the step of the task should be a well formed absolute URI or
        there should be only one source trigger for the task.

    :param context_access_token: (DockerBuildStep, EncodedTaskStep, FileTaskStep) The token (git PAT or SAS token of
        storage account blob) associated with the context for a step.

    :param task_file_path: (DockerBuildStep, FileTaskStep REQUIRED) The template/definition file path relative to the
        source.

    :param image_names: (DockerBuildStep) A list of strings containing the fully qualified image names including the
        repository and tag.

    :param is_push_enabled: (DockerBuildStep) The value of this property indicates whether the image built should be
        pushed to the registry or not. SDK default value: True

    :param no_cache: (DockerBuildStep) The value of this property indicates whether the image cache is enabled or not.
        SDK default value: False

    :param target: (DockerBuildStep) The name of the target build stage for the docker build.

    :param encoded_task_content: (EncodedTaskStep REQUIRED) Base64 encoded value of the template/definition file
        content.

    :param encoded_values_content: (EncodedTaskStep) Base64 encoded value of the parameters/values file content.

    :param values_file_path: (FileTaskStep) The values/parameters file path relative to the source context.

    :param values_dict: The collection of overridable values or arguments that can be passed when running a task. This
        is a list of dictionaries containing the following keys: 'name', 'value', and 'is_secret'

    :param agent_num_cores: The CPU configuration in terms of number of cores required for the run.

    :param trigger: The properties that describe all triggers for the task. This is a dictionary containing trigger
        information as described in the documentation for the
        `Azure Python SDK <https://docs.microsoft.com/en-us/python/api/azure-mgmt-containerregistry/azure.mgmt.containerregistry.v2019_04_01.models.triggerproperties?view=azure-python>`_

    :param status: The current status of task. Possible values include: 'Disabled', 'Enabled'

    :param timeout: Run timeout in seconds. Default value: 3600

    :param credential_login_mode: The authentication mode which determines the source registry login scope. The
        credentials for the source registry will be generated using the given scope. These credentials will be used to
        login to the source registry during the run. Possible values include: 'None', 'Default'

    :param credential_login_server: Describes the registry login server (myregistry.azurecr.io) for accessing other
        custom registries.

    :param credential_username: Username for accessing the registry defined in credential_login_server

    :param credential_password: Password for accessing the registry defined in credential_login_server

    :param identity_principal_id: The principal ID of resource identity.

    :param identity_tenant_id: The tenant ID of resource.

    :param identity_type: The identity type. Possible values include: 'SystemAssigned', 'UserAssigned'

    :param user_assigned_identities: The list of user identities associated with the resource. The user identity
        dictionary key references will be ARM resource ids in the form:
        ``/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{identityName}``

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.task.create_or_update taskname testrepo testgroup FileTaskStep Linux amd64 v7 \
        context_path="https://eitr.tech/some/path" task_file_path="src/task.sh"

    """
    agent_configuration = None
    credentials = None
    identity = None
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

    if agent_num_cores:
        agent_configuration = {"cpu": agent_num_cores}

    if credential_login_server:
        credentials = {
            "source_registry": {
                "login_mode": credential_login_mode,
                "custom_registries": {
                    credential_login_server: {
                        "username": credential_username,
                        "password": credential_password,
                    }
                },
            }
        }

    if identity_principal_id or user_assigned_identities:
        identity = {
            "principal_id": identity_principal_id,
            "tenant_id": identity_tenant_id,
            "type": identity_type,
            "user_assigned_identities": user_assigned_identities,
        }

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    try:
        stepmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerregistry",
            task_type,
            context_path=context_path,
            context_access_token=context_access_token,
            type=task_type,
            image_names=image_names,
            is_push_enabled=is_push_enabled,
            no_cache=no_cache,
            task_file_path=task_file_path,
            docker_file_path=task_file_path,
            target=target,
            arguments=values_dict,
            values=values_dict,
            encoded_task_content=encoded_task_content,
            encoded_values_content=encoded_values_content,
            values_file_path=values_file_path,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        taskmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerregistry",
            "Task",
            identity=identity,
            credentials=credentials,
            status=status,
            step=stepmodel,
            platform={
                "os": platform_os,
                "architecture": platform_arch,
                "variant": platform_variant,
            },
            agent_configuration=agent_configuration,
            timeout=timeout,
            trigger=trigger,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        task = regconn.tasks.create(
            task_name=name,
            registry_name=registry_name,
            resource_group_name=resource_group,
            task_create_parameters=taskmodel,
        )
        task.wait()
        result = task.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, registry_name, resource_group, details=False, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets the properties of the specified task.

    :param name: The name of the container registry task.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param details: Boolean flag to enable return of extended information that includes all secrets.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.task.get taskname testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        if details:
            ret = regconn.tasks.get_details(
                task_name=name,
                registry_name=registry_name,
                resource_group_name=resource_group,
            )
        else:
            ret = regconn.tasks.get(
                task_name=name,
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

    Lists all the tasks for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.task.list testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        tasks = await hub.exec.azurerm.utils.paged_object_to_list(
            regconn.tasks.list(registry_name=name, resource_group_name=resource_group)
        )
        for task in tasks:
            result[task["name"]] = task
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Deletes a task from a container registry.

    :param name: The name of the container registry task.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.task.delete taskname testrepo testgroup

    """
    result = False
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.tasks.delete(
            task_name=name,
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
