# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Instance Group Execution Module

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
    import azure.mgmt.containerinstance  # pylint: disable=unused-import
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
    resource_group,
    containers,
    os_type,
    restart_policy="OnFailure",
    identity=None,
    image_registry_credentials=None,
    ip_address=None,
    volumes=None,
    diagnostics=None,
    network_profile=None,
    dns_config=None,
    sku=None,
    encryption_properties=None,
    init_containers=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Create or update container groups with specified configurations. This is an EXTREMELY complex module. I wouldn't
    recommend attempting to use this on the command line...

    Consult the `SDK documentation <
    https://docs.microsoft.com/en-us/python/api/azure-mgmt-containerinstance/azure.mgmt.containerinstance.models.containergroup?view=azure-python
    >`_ for more information about the objects passed to the parameters in this module.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    :param containers: A list of the containers within the container group.

    - **name**: Required. The user-provided name of the container instance.
    - **image**: Required. The name of the image used to create the container instance.
    - **resources**:
        **requests**:
            **memory_in_gb**: Required. The memory request in GB of this container instance.

            **cpu**: Required. The CPU request of this container instance.

            **gpu**: The GPU request of this container instance.
        **limits**:
            **memory_in_gb**: The memory limit in GB of this container instance.

            **cpu**: The CPU limit of this container instance.

            **gpu**: The GPU limit of this container instance.
    - **command**: A list of commands to execute within the container instance in exec form.
    - **ports**: A list of the dictionaries of exposed ports on the container instance.
      (``{"protocol": "TCP", "port": 80}``)
    - **environment_variables**: A list of environment variables to set in the container instance.
        **name**: Required if environment_variables is used. The name of the environment variable.

        **value**: The value of the environment variable.

        **secure_value**: The value of the secure environment variable.
    - **volume_mounts**: A list of volume mounts available to the container instance.
        **name**: Required if volume_mounts is used. The name of the volume mount.

        **mount_path**: Required if volume_mounts is used. The path within the container where the volume should
        be mounted. Must not contain colon (:).

        **read_only**: Boolean flag indicating whether the volume mount is read-only.
    - **liveness_probe**:
            **exec_property**:
                **command**: The commands to execute within the container.
            **http_get**:
                **path**: The path to probe.

                **port**: Required if http_get is used. The port number to probe.

                **scheme**: The scheme. Possible values include: 'http', 'https'
            **initial_delay_seconds**: The initial delay seconds.

            **period_seconds**: The period seconds.

            **failure_threshold**: The failure threshold.

            **success_threshold**: The success threshold.

            **timeout_seconds**: The timeout seconds.
    - **readiness_probe**:
            **exec_property**:
                **command**: The commands to execute within the container.
            **http_get**:
                **path**: The path to probe.

                **port**: Required if http_get is used. The port number to probe.

                **scheme**: The scheme. Possible values include: 'http', 'https'
            **initial_delay_seconds**: The initial delay seconds.

            **period_seconds**: The period seconds.

            **failure_threshold**: The failure threshold.

            **success_threshold**: The success threshold.

            **timeout_seconds**: The timeout seconds.

    :param os_type: The operating system type required by the containers in the container group. Possible values
        include: 'Windows', 'Linux'

    :param restart_policy: Restart policy for all containers within the container group. Possible values are:
    - ``Always``: Always restart
    - ``OnFailure``: Restart on failure
    - ``Never``: Never restart

    :param identity: A dictionary defining a ContainerGroupIdentity object which represents the identity for the
        container group.

    :param image_registry_credentials: A list of dictionaries defining ImageRegistryCredential objects for the image
        registry credentials.

    :param ip_address: A dictionary defining an IpAddress object which represents the IP address for the container
        group. Possible keys are:
    - ``ports``: Required if ip_address is used. The list of ports exposed on the container group.
    - ``type``: Required if ip_address is used. Specifies if the IP is exposed to the public internet or private VNET.
      Possible values include: 'Public', 'Private'
    - ``ip``: The IP exposed to the public internet.
    - ``dns_name_label``: The Dns name label for the IP.

    :param volumes: The list of dictionaries representing Volume objects that can be mounted by containers in this
        container group.

    :param diagnostics: A dictionary defining a ContainerGroupDiagnostics object which represents the diagnostic
        information for the container group.

    :param network_profile: A dictionary defining a ContainerGroupNetworkProfile object which represents the network
        profile information for the container group.

    :param dns_config: A dictionary defining a DnsConfiguration object which represents the DNS config information for
        the container group.

    :param sku: The SKU for a container group. Possible values include: 'Standard', 'Dedicated'

    :param encryption_properties: A dictionary defining an EncryptionProperties object which represents the encryption
        properties for the container group.

    :param init_containers: A list of dictionaries defining InitContainerDefinition objects which represent the init
        containers for the container group.

    :param tags: The tags of the resource.

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

    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )

    try:
        grpmodel = await hub.exec.azurerm.utils.create_object_model(
            "containerinstance",
            "ContainerGroup",
            containers=containers,
            os_type=os_type,
            restart_policy=restart_policy,
            identity=identity,
            image_registry_credentials=image_registry_credentials,
            ip_address=ip_address,
            volumes=volumes,
            diagnostics=diagnostics,
            network_profile=network_profile,
            dns_config=dns_config,
            sku=sku,
            encryption_properties=encryption_properties,
            init_containers=init_containers,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        grp = conconn.container_groups.create_or_update(
            container_group_name=name,
            resource_group_name=resource_group,
            container_group=grpmodel,
        )
        grp.wait()
        result = grp.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def update(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Updates container group tags with specified values.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.update containergroup resourcegroup tags='{"owner": "me"}'

    """
    result = {}

    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )

    try:
        grp = conconn.container_groups.update(
            container_group_name=name, resource_group_name=resource_group, tags=tags,
        )
        result = grp.as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets the properties of the specified container group in the specified subscription and resource group. The operation
    returns the properties of each container group including containers, image registry credentials, restart policy, IP
    address type, OS type, state, and volumes.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.get containergroup resourcegroup

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.container_groups.get(
            container_group_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Get a list of container groups in the specified subscription. This operation returns properties of each container
    group including containers, image container credentials, restart policy, IP address type, OS type, state, and
    volumes.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.list

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        if resource_group:
            groups = await hub.exec.azurerm.utils.paged_object_to_list(
                conconn.container_groups.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            groups = await hub.exec.azurerm.utils.paged_object_to_list(
                conconn.container_groups.list()
            )
        for group in groups:
            result[group["name"]] = group
    except (CloudError, Exception) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Delete the specified container group in the specified subscription and resource group. The operation does not delete
    other resources provided by the user, such as volumes.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.delete containergroup resourcegroup

    """
    result = False
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.container_groups.delete(
            container_group_name=name, resource_group_name=resource_group
        )
        ret.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def restart(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Restarts all containers in a container group in place. If container image has updates, new image will be downloaded.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.restart containergroup resourcegroup

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.container_groups.restart(
            container_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def start(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Starts all containers in a container group. Compute resources will be allocated and billing will start.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.start containergroup resourcegroup

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.container_groups.start(
            container_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def stop(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Stops all containers in a container group. Compute resources will be deallocated and billing will stop.

    :param name: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.group.stop containergroup resourcegroup

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.container_groups.stop(
            container_name=name, resource_group_name=resource_group
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
