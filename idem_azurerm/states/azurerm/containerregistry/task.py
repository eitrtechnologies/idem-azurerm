# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Task State Module

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

        Ensure container registry task exists:
            azurerm.containerregistry.task.present:
                - name: testtask
                - registry_name: testrepo
                - resource_group: testgroup
                - task_type: DockerBuildStep
                - platform_os: Linux
                - platform_arch: amd64
                - context_path: "https://github.com/Azure-Samples/acr-build-helloworld-node"
                - task_file_path: Dockerfile
                - image_names:
                    - "testrepo:helloworldnode"
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

        Ensure container registry task is absent:
            azurerm.containerregistry.task.absent:
                - name: testtask
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
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Ensure a container registry task exists.

    :param name: The name of the task.

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

    :param tags: A dictionary of strings can be passed as tag metadata to the object.

    Example usage:

    .. code-block:: yaml

        Ensure container registry task exists:
            azurerm.containerregistry.task.present:
                - name: testtask
                - registry_name: testrepo
                - resource_group: testgroup
                - task_type: DockerBuildStep
                - platform_os: Linux
                - platform_arch: amd64
                - context_path: "https://github.com/Azure-Samples/acr-build-helloworld-node"
                - task_file_path: Dockerfile
                - image_names:
                    - "testrepo:helloworldnode"
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
        "task_type",
        "platform_os",
        "platform_arch",
        "platform_variant",
        "context_path",
        "context_access_token",
        "task_file_path",
        "image_names",
        "is_push_enabled",
        "no_cache",
        "target",
        "encoded_task_content",
        "encoded_values_content",
        "values_file_path",
        "values_dict",
        "agent_num_cores",
        "status",
        "trigger",
        "timeout",
        "credential_login_mode",
        "credential_login_server",
        "credential_username",
        "credential_password",
        "identity_principal_id",
        "identity_tenant_id",
        "identity_type",
        "user_assigned_identities",
        "tags",
    ]:
        value = locals()[param]
        if value is not None:
            new[param] = value

    # get existing container registry task if present
    task = await hub.exec.azurerm.containerregistry.task.get(
        ctx,
        name,
        registry_name,
        resource_group,
        details=True,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in task:
        action = "update"

        # task_type changes
        if not task_type.upper().startswith(task["step"]["type"].upper()):
            ret["changes"]["task_type"] = {
                "old": task["step"]["type"],
                "new": task_type,
            }

        # platform_os changes
        if platform_os.upper() != task["platform"]["os"].upper():
            ret["changes"]["platform_os"] = {
                "old": task["platform"]["os"],
                "new": platform_os,
            }

        # platform_arch changes
        if platform_arch.upper() != task["platform"]["architecture"].upper():
            ret["changes"]["platform_arch"] = {
                "old": task["platform"]["architecture"],
                "new": platform_arch,
            }

        # platform_variant changes
        if (
            platform_variant
            and platform_variant.upper() != task["platform"].get("variant", "").upper()
        ):
            ret["changes"]["platform_variant"] = {
                "old": task["platform"].get("variant"),
                "new": platform_variant,
            }

        # timeout changes
        if timeout and int(timeout) != task["timeout"]:
            ret["changes"]["timeout"] = {
                "old": task["timeout"],
                "new": timeout,
            }

        # status changes
        if status and status.upper() != task.get("status", "").upper():
            ret["changes"]["status"] = {
                "old": task.get("platform"),
                "new": status,
            }

        # is_push_enabled changes
        if is_push_enabled is not None and is_push_enabled != task["step"].get(
            "is_push_enabled"
        ):
            ret["changes"]["is_push_enabled"] = {
                "old": task["step"].get("is_push_enabled"),
                "new": is_push_enabled,
            }

        # no_cache changes
        if no_cache is not None and no_cache != task["step"].get("no_cache"):
            ret["changes"]["no_cache"] = {
                "old": task["step"].get("no_cache"),
                "new": no_cache,
            }

        # context_path changes
        if context_path and context_path != task["step"].get("context_path"):
            ret["changes"]["context_path"] = {
                "old": task["step"].get("context_path"),
                "new": context_path,
            }

        # context_access_token changes
        if context_access_token and context_access_token != task["step"].get(
            "context_access_token"
        ):
            ret["changes"]["context_access_token"] = {
                "old": task["step"].get("context_access_token"),
                "new": context_access_token,
            }

        # task_file_path changes
        old_file_path = task["step"].get("docker_file_path") or task["step"].get(
            "task_file_path"
        )
        if task_file_path and task_file_path != old_file_path:
            ret["changes"]["task_file_path"] = {
                "old": old_file_path,
                "new": task_file_path,
            }

        # target changes
        if target and target != task["step"].get("target"):
            ret["changes"]["target"] = {
                "old": task["step"].get("target"),
                "new": target,
            }

        # encoded_task_content changes
        if encoded_task_content and encoded_task_content != task["step"].get(
            "encoded_task_content"
        ):
            ret["changes"]["encoded_task_content"] = {
                "old": task["step"].get("encoded_task_content"),
                "new": encoded_task_content,
            }

        # encoded_values_content changes
        if encoded_values_content and encoded_values_content != task["step"].get(
            "encoded_values_content"
        ):
            ret["changes"]["encoded_values_content"] = {
                "old": task["step"].get("encoded_values_content"),
                "new": encoded_values_content,
            }

        # values_file_path changes
        if values_file_path and values_file_path != task["step"].get(
            "values_file_path"
        ):
            ret["changes"]["values_file_path"] = {
                "old": task["step"].get("values_file_path"),
                "new": values_file_path,
            }

        # values_dict changes
        if values_dict:
            old_vals = task["step"].get("arguments") or task["step"].get("values", {})
            val_diff = differ.deep_diff(old_vals, values_dict)
            if val_diff:
                ret["changes"]["values_dict"] = val_diff

        # agent_num_cores changes
        old_cores = task.get("agent_configuration", {}).get("cpu")
        if agent_num_cores and int(agent_num_cores) != old_cores:
            ret["changes"]["agent_num_cores"] = {
                "old": task["agent_num_cores"],
                "new": agent_num_cores,
            }

        # trigger changes
        if trigger:
            trig_diff = differ.deep_diff(task.get("trigger", {}), trigger)
            if trig_diff:
                ret["changes"]["trigger"] = trig_diff

        # credentials changes
        if credential_login_server:
            credentials = {
                "source_registry": {"custom_registries": {credential_login_server: {}}}
            }
            if credential_login_mode:
                credentials["source_registry"]["login_mode"] = credential_login_mode
            if credential_username:
                credentials["source_registry"]["custom_registries"][
                    credential_login_server
                ]["username"] = credential_username
            if credential_password:
                credentials["source_registry"]["custom_registries"][
                    credential_login_server
                ]["username"] = credential_password

            cred_diff = differ.deep_diff(task.get("credentials", {}), credentials)
            if cred_diff:
                ret["changes"]["credentials"] = cred_diff

        # identity_principal_id changes
        old_prid = task.get("identity", {}).get("principal_id")
        if identity_principal_id and identity_principal_id != old_prid:
            ret["changes"]["identity_principal_id"] = {
                "old": old_prid,
                "new": identity_principal_id,
            }

        # identity_tenant_id changes
        old_tnid = task.get("identity", {}).get("tenant_id")
        if identity_tenant_id and identity_tenant_id != old_tnid:
            ret["changes"]["identity_tenant_id"] = {
                "old": old_tnid,
                "new": identity_tenant_id,
            }

        # identity_type changes
        old_idtype = task.get("identity", {}).get("type")
        if identity_type and identity_type != old_idtype:
            ret["changes"]["identity_type"] = {
                "old": old_idtype,
                "new": identity_type,
            }

        # user_assigned_identities changes
        if user_assigned_identities:
            old_uai = task.get("identity", {}).get("user_assigned_identities", [])
            comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
                old_uai, user_assigned_identities, key_name="principal_id"
            )

            if comp.get("changes"):
                ret["changes"]["user_assigned_identities"] = comp["changes"]

        # image_names changes
        old_img = sorted(task["step"].get("image_names", []))
        images = sorted(image_names or [])
        if old_img != images:
            ret["changes"]["image_names"] = {
                "old": old_img,
                "new": image_names,
            }

        # tag changes
        tag_diff = differ.deep_diff(task.get("tags", {}), tags or {})
        if tag_diff:
            ret["changes"]["tags"] = tag_diff

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Container registry task {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["comment"] = "Container registry task {0} would be updated.".format(
                name
            )
            ret["result"] = None
            return ret

    elif ctx["test"]:
        ret["comment"] = "Container registry task {0} would be created.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": {},
            "new": new,
        }
        return ret

    task_kwargs = kwargs.copy()
    task_kwargs.update(connection_auth)

    task = await hub.exec.azurerm.containerregistry.task.create_or_update(
        ctx=ctx,
        name=name,
        registry_name=registry_name,
        resource_group=resource_group,
        task_type=task_type,
        platform_os=platform_os,
        platform_arch=platform_arch,
        platform_variant=platform_variant,
        context_path=context_path,
        context_access_token=context_access_token,
        task_file_path=task_file_path,
        image_names=image_names,
        is_push_enabled=is_push_enabled,
        no_cache=no_cache,
        target=target,
        encoded_task_content=encoded_task_content,
        encoded_values_content=encoded_values_content,
        values_file_path=values_file_path,
        values_dict=values_dict,
        agent_num_cores=agent_num_cores,
        status=status,
        trigger=trigger,
        timeout=timeout,
        credential_login_mode=credential_login_mode,
        credential_login_server=credential_login_server,
        credential_username=credential_username,
        credential_password=credential_password,
        identity_principal_id=identity_principal_id,
        identity_tenant_id=identity_tenant_id,
        identity_type=identity_type,
        user_assigned_identities=user_assigned_identities,
        tags=tags,
        **task_kwargs,
    )

    if "error" not in task:
        ret["result"] = True
        ret["comment"] = f"Container registry task {name} has been {action}d."
        if not ret["changes"]:
            ret["changes"] = {"old": {}, "new": new}
        return ret

    ret["comment"] = "Failed to {0} container registry task {1}! ({2})".format(
        action, name, task.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, registry_name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Ensure a task does not exist in a container registry.

    :param name: Name of the task.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    .. code-block:: yaml

        Ensure container registry task is absent:
            azurerm.containerregistry.task.absent:
                - name: testtask
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

    task = await hub.exec.azurerm.containerregistry.task.get(
        ctx,
        name,
        registry_name,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in task:
        ret["result"] = True
        ret["comment"] = "Container registry task {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Container registry task {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": task,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.containerregistry.task.delete(
        ctx, name, registry_name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Container registry task {0} has been deleted.".format(name)
        ret["changes"] = {"old": task, "new": {}}
        return ret

    ret["comment"] = "Failed to delete container registry task {0}!".format(name)
    return ret
