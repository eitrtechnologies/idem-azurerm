# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Execution Module

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


async def check_name_availability(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 3.0.0

    Checks whether the container registry name is available for use. The name must contain only alphanumeric characters,
    be globally unique, and between 5 and 50 characters in length.

    :param name: The name of the container registry.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.check_name_availability testrepo

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.registries.check_name_availability(name)
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def create_or_update(
    hub,
    ctx,
    name,
    resource_group,
    sku="Basic",
    admin_user_enabled=False,
    default_action=None,
    virtual_network_rules=None,
    ip_rules=None,
    trust_policy=None,
    quarantine_policy=None,
    retention_policy=None,
    retention_days=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates or updates a container registry with the specified parameters.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param sku: The SKU name of the container registry. Required for registry creation. Possible
        values include: 'Basic', 'Standard', 'Premium'

    :param admin_user_enabled: This value indicates whether the admin user is enabled.

    :param default_action: The default action of allow or deny when no other rules match.
        Possible values include: 'Allow', 'Deny'. Only available for the 'Premium' tier.

    :param virtual_network_rules: A list of virtual network rule dictionaries where one key is the "action"
        of the rule (Allow/Deny) and the other key is the "virtual_network_resource_id" which is the full
        resource ID path of a subnet. Only available for the 'Premium' tier.

    :param ip_rules: A list of IP rule dictionaries where one key is the "action" of the rule (Allow/Deny)
        and the other key is the "ip_address_or_range" which specifies the IP or IP range in CIDR format.
        Only IPV4 addresses are allowed. Only available for the 'Premium' tier.

    :param trust_policy: Accepts boolean True/False or string "enabled"/"disabled" to configure.
        Image publishers can sign their container images and image consumers can verify their integrity.
        Container Registry supports both by implementing Docker's content trust model. Only available
        for the 'Premium' tier.

    :param quarantine_policy: Accepts boolean True/False or string "enabled"/"disabled" to configure.
        To assure a registry only contains images that have been vulnerability scanned, ACR introduces
        the Quarantine pattern. When a registries policy is set to Quarantine Enabled, all images pushed
        to that registry are put in quarantine by default. Only after the image has been verifed, and the
        quarantine flag removed may a subsequent pull be completed. Only available for the 'Premium' tier.

    :param retention_policy: Accepts boolean True/False or string "enabled"/"disabled" to configure.
        Indicates whether retention policy is enabled. Only available for the 'Premium' tier.

    :param retention_days: The number of days to retain an untagged manifest after which it gets purged
        (Range: 0 to 365). Value "0" will delete untagged manifests immediately. Only available for the
        'Premium' tier.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.create_or_update testrepo testgroup

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

    if quarantine_policy is not None:
        if isinstance(quarantine_policy, bool) and not quarantine_policy:
            quarantine_policy = "disabled"
        elif isinstance(quarantine_policy, bool):
            quarantine_policy = "enabled"
        quarantine_policy = {
            "status": quarantine_policy,
        }

    if trust_policy is not None:
        if isinstance(trust_policy, bool) and not trust_policy:
            trust_policy = "disabled"
        elif isinstance(trust_policy, bool):
            trust_policy = "enabled"
        trust_policy = {
            "type": "Notary",
            "status": trust_policy,
        }

    if retention_policy is not None or retention_days is not None:
        if isinstance(retention_policy, bool) and not retention_policy:
            retention_policy = "disabled"
        elif isinstance(retention_policy, bool):
            retention_policy = "enabled"
        retention_policy = {
            "days": retention_days,
            "status": retention_policy,
        }

    if sku.title() == "Premium":
        kwargs["network_rule_set"] = {
            "default_action": default_action,
            "virtual_network_rules": virtual_network_rules,
            "ip_rules": ip_rules,
        }
        kwargs["policies"] = {
            "quarantine_policy": quarantine_policy,
            "trust_policy": trust_policy,
            "retention_policy": retention_policy,
        }
    elif any(
        [
            default_action,
            virtual_network_rules,
            ip_rules,
            quarantine_policy,
            trust_policy,
            retention_policy,
        ]
    ):
        log.error("The configured options are only available in the Premium SKU.")
        return {
            "error": "The configured options are only available in the Premium SKU."
        }

    try:
        regmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerregistry",
            "Registry",
            tags=tags,
            sku={"name": sku},
            admin_user_enabled=admin_user_enabled,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        reg = regconn.registries.create(
            registry_name=name, resource_group_name=resource_group, registry=regmodel
        )
        reg.wait()
        result = reg.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets the properties of the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.get testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.registries.get(
            registry_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get_build_source_upload_url(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Get the upload location for the user to be able to upload the source.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.get_build_source_upload_url testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.registries.get_build_source_upload_url(
            registry_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists all the container registries under the specified subscription or resource group.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.list

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        if resource_group:
            registries = await hub.exec.azurerm.utils.paged_object_to_list(
                regconn.registries.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            registries = await hub.exec.azurerm.utils.paged_object_to_list(
                regconn.registries.list()
            )
        for registry in registries:
            result[registry["name"]] = registry
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_credentials(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists the login credentials for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.list_credentials testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        creds = regconn.registries.list_credentials(
            registry_name=name, resource_group_name=resource_group
        )
        result = creds.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_usages(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists the quota usages for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.list_usages testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        usages = regconn.registries.list_usages(
            registry_name=name, resource_group_name=resource_group
        )
        result = usages.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def regenerate_credential(
    hub, ctx, name, resource_group, credential="password", **kwargs
):
    """
    .. versionadded:: 3.0.0

    Regenerates one of the login credentials for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param credential: Specifies name of the password which should be regenerated. Possible values
        include: 'password', 'password2'.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.regenerate_credential testrepo testgroup credential=password2

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.registries.regenerate_credential(
            registry_name=name, resource_group_name=resource_group, name=credential
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Deletes a container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.delete testrepo testgroup

    """
    result = False
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.registries.delete(
            registry_name=name, resource_group_name=resource_group
        )
        ret.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def import_image(
    hub,
    ctx,
    name,
    resource_group,
    source_image,
    source_resource_id=None,
    source_registry_uri=None,
    source_username=None,
    source_password=None,
    target_tags=None,
    untagged_target_repositories=None,
    mode=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Copies an image to this container registry from the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param source_image: Repository name of the source image. Specify an image by repository ('hello-world').
        This will use the 'latest' tag. Specify an image by tag ('hello-world:latest'). Specify an image by
        sha256-based manifest digest ('hello-world@sha256:abc123').

    :param source_resource_id: The resource identifier of the source Azure Container Registry.

    :param source_registry_uri: The address of the source registry (e.g. 'docker.io').

    :param source_username: The username to authenticate with the source registry.

    :param source_password: The password used to authenticate with the source registry.

    :param target_tags: List of strings of the form repo[:tag]. When tag is omitted the source will be
        used (or 'latest' if source tag is also omitted).

    :param untagged_target_repositories: List of strings of repository names to do a manifest only copy.
        No tag will be created.

    :param mode: When Force, any existing target tags will be overwritten. When NoForce, any existing
        target tags will fail the operation before any copying begins. Possible values include: 'NoForce',
        'Force'. Default value: 'NoForce'.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.import_image testrepo testgroup library/hello-world:latest
                                                        source_registry_uri=docker.io

    """
    result = False

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    source_credentials = None

    if source_password:
        source_credentials = {
            "username": source_username,
            "password": source_password,
        }

    if not target_tags:
        index = source_image.find("@")
        if index > 0:
            target_tags = [source_image[:index]]
        else:
            target_tags = [source_image]

    try:
        importmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerregistry",
            "ImportImageParameters",
            source={
                "source_image": source_image,
                "resource_id": source_resource_id,
                "registry_uri": source_registry_uri,
                "credentials": source_credentials,
            },
            target_tags=target_tags,
            untagged_target_repositories=untagged_target_repositories,
            mode=mode,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        ret = regconn.registries.import_image(
            registry_name=name,
            resource_group_name=resource_group,
            parameters=importmodel,
        )
        ret.wait()
        result = True
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def schedule_run(
    hub,
    ctx,
    name,
    resource_group,
    run_type,
    is_archive_enabled=None,
    task_name=None,
    task_file_path=None,
    values_file_path=None,
    encoded_task_content=None,
    encoded_values_content=None,
    image_names=None,
    is_push_enabled=None,
    no_cache=None,
    target=None,
    values_dict=None,
    timeout=None,
    platform_os=None,
    platform_arch=None,
    platform_variant=None,
    agent_num_cores=None,
    source_location=None,
    credential_login_mode=None,
    credential_login_server=None,
    username=None,
    password=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Schedules a new run based on the request parameters and add it to the run queue.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param run_type: The type of run to be scheduled. Must be FileTaskRun, TaskRun, EncodedTaskRun, or DockerBuild.

    :param is_archive_enabled: The value that indicates whether archiving is enabled for the run or not.

    :param task_name: (TaskRun REQUIRED) The name of task against which run has to be queued.

    :param task_file_path: (FileTaskRun, DockerBuild REQUIRED) The template/definition file (or Dockerfile) path
        relative to the source.

    :param values_file_path: (FileTaskRun) The values/parameters file path relative to the source.

    :param encoded_task_content: (EncodedTaskRun REQUIRED) Base64 encoded value of the template/definition file content.

    :param encoded_values_content: (DockerBuild) Base64 encoded value of the parameters/values file content.

    :param image_names: (DockerBuild) A list of strings containing the fully qualified image names including the
        repository and tag.

    :param is_push_enabled: (DockerBuild) The value of this property indicates whether the image built should be pushed
        to the registry or not. SDK default value: True.

    :param no_cache: (DockerBuild) The value of this property indicates whether the image cache is enabled or not. SDK
        default value: False.

    :param target: (DockerBuild) The name of the target build stage for the docker build.

    :param values_dict: The collection of overridable values or arguments that can be passed when running a task. This
        is a list of dictionaries containing the following keys: 'name', 'value', and 'is_secret'.

    :param timeout: (FileTaskRun, DockerBuild, EncodedTaskRun) Run timeout in seconds. SDK default value: 3600.

    :param platform_os: (FileTaskRun, DockerBuild, EncodedTaskRun REQUIRED) The platform OS property against which the
        run has to happen. Accepts 'Windows' or 'Linux'.

    :param platform_arch: (FileTaskRun, DockerBuild, EncodedTaskRun REQUIRED) The platform architecture property against
        which the run has to happen. Accepts 'amd64', 'x86', or 'arm'.

    :param platform_variant: (FileTaskRun, DockerBuild, EncodedTaskRun REQUIRED) The platform CPU variant property
        against which the run has to happen. Accepts 'v6', 'v7', or 'v8'.

    :param agent_num_cores: (FileTaskRun, DockerBuild, EncodedTaskRun) The CPU configuration in terms of number of cores
        required for the run.

    :param source_location: (FileTaskRun, DockerBuild, EncodedTaskRun) The URL(absolute or relative) of the source
        context.  It can be an URL to a tar or git repository. If it is relative URL, the relative path should be
        obtained from calling get_build_source_upload_url.

    :param credential_login_mode: (FileTaskRun, DockerBuild, EncodedTaskRun) The authentication mode which determines
        the source registry login scope. The credentials for the source registry will be generated using the given
        scope. These credentials will be used to login to the source registry during the run. Possible values include:
        'None', 'Default'.

    :param credential_login_server: (FileTaskRun, DockerBuild, EncodedTaskRun) Describes the registry login server
        (myregistry.azurecr.io) for accessing other custom registries.

    :param username: (FileTaskRun, DockerBuild, EncodedTaskRun) Username for accessing the registry defined in
        credential_login_server.

    :param password: (FileTaskRun, DockerBuild, EncodedTaskRun) Password for accessing the registry defined in
        credential_login_server.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.schedule_run testrepo testgroup TaskRun task_name=testtask

    """
    agent_configuration = None
    credentials = None
    result = {}

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    if not isinstance(run_type, str) and run_type.upper() not in [
        "FILETASKRUN",
        "TASKRUN",
        "ENCODEDTASKRUN",
        "DOCKERBUILD",
    ]:
        result = {
            "error": "Invalid run type. Must be FileTaskRun, TaskRun, EncodedTaskRun, or DockerBuild."
        }
        return result

    if credential_login_server:
        credentials = {
            "source_registry": {
                "login_mode": credential_login_mode,
                "custom_registries": {
                    credential_login_server: {
                        "username": username,
                        "password": password,
                    }
                },
            }
        }

    if agent_num_cores:
        agent_configuration = {"cpu": agent_num_cores}

    if run_type.upper() == "FILETASKRUN":
        try:
            runmodel = await hub.exec.azurerm.utils.create_object_model(
                "containerregistry",
                "FileTaskRunRequest",
                is_archive_enabled=is_archive_enabled,
                type="FileTaskRunRequest",
                task_file_path=task_file_path,  # REQUIRED
                values_file_path=values_file_path,
                values=values_dict,
                timeout=timeout,
                platform={
                    "os": platform_os,
                    "architecture": platform_arch,
                    "variant": platform_variant,
                },  # REQUIRED
                agent_configuration=agent_configuration,
                source_location=source_location,
                credentials=credentials,
                **kwargs,
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

    elif run_type.upper() == "TASKRUN":
        try:
            runmodel = await hub.exec.azurerm.utils.create_object_model(
                "containerregistry",
                "TaskRunRequest",
                is_archive_enabled=is_archive_enabled,
                type="TaskRunRequest",
                task_name=task_name,  # REQUIRED
                values=values_dict,
                **kwargs,
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

    elif run_type.upper() == "ENCODEDTASKRUN":
        try:
            runmodel = await hub.exec.azurerm.utils.create_object_model(
                "containerregistry",
                "EncodedTaskRunRequest",
                is_archive_enabled=is_archive_enabled,
                type="EncodedTaskRunRequest",
                encoded_task_content=encoded_task_content,  # REQUIRED
                encoded_values_content=encoded_values_content,
                values=values_dict,
                timeout=timeout,
                platform={
                    "os": platform_os,
                    "architecture": platform_arch,
                    "variant": platform_variant,
                },  # REQUIRED
                agent_configuration=agent_configuration,
                source_location=source_location,
                credentials=credentials,
                **kwargs,
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

    elif run_type.upper() == "DOCKERBUILD":
        try:
            runmodel = await hub.exec.azurerm.utils.create_object_model(
                "containerregistry",
                "DockerBuildRequest",
                is_archive_enabled=is_archive_enabled,
                type="DockerBuildRequest",
                image_names=image_names,
                is_push_enabled=is_push_enabled,
                no_cache=no_cache,
                docker_file_path=task_file_path,  # REQUIRED
                target=target,
                arguments=values_dict,
                timeout=timeout,
                platform={
                    "os": platform_os,
                    "architecture": platform_arch,
                    "variant": platform_variant,
                },  # REQUIRED
                agent_configuration=agent_configuration,
                source_location=source_location,
                credentials=credentials,
                **kwargs,
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

    try:
        ret = regconn.registries.schedule_run(
            registry_name=name,
            resource_group_name=resource_group,
            run_request=runmodel,
        )
        ret.wait()
        result = ret.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
