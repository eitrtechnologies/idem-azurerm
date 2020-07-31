# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Instance Group State Module

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

        Ensure container instance group exists:
            azurerm.containerinstance.group.present:
                - name: containergroup
                - resource_group: testgroup
                - containers:
                    - name: mycoolwebcontainer
                      image: "nginx:latest"
                      resources:
                          requests:
                              memory_in_gb: 1
                              cpu: 1
                - os_type: Linux
                - restart_policy: OnFailure
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

        Ensure container instance group is absent:
            azurerm.containerinstance.group.absent:
                - name: containergroup
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
    resource_group,
    containers,
    os_type,
    restart_policy="OnFailure",
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Ensure a container instance group exists.

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
    - ``Never``: Never restart.

    :param tags: A dictionary of strings can be passed as tag metadata to the object.


    Example usage:

    .. code-block:: yaml

        Ensure container instance group exists:
            azurerm.containerinstance.group.present:
                - name: containergroup
                - resource_group: testgroup
                - containers:
                    - name: mycoolwebcontainer
                      image: "nginx:latest"
                      resources:
                          requests:
                              memory_in_gb: 1
                              cpu: 1
                - os_type: Linux
                - restart_policy: OnFailure
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
        "resource_group",
        "containers",
        "os_type",
        "restart_policy",
        "tags",
    ]:
        value = locals()[param]
        if value is not None:
            new[param] = value

    # get existing container instance group if present
    acig = await hub.exec.azurerm.containerinstance.group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in acig:
        action = "update"

        # containers changes
        old_containers = acig["containers"]
        comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
            old_containers, containers
        )
        if comp.get("changes"):
            ret["changes"]["containers"] = comp["changes"]

        # os_type changes
        if os_type.upper() != acig["os_type"].upper():
            ret["changes"]["os_type"] = {"old": acig["os_type"], "new": os_type}

        # restart_policy changes
        if restart_policy.upper() != acig["restart_policy"].upper():
            ret["changes"]["restart_policy"] = {
                "old": acig["restart_policy"],
                "new": restart_policy,
            }

        # tag changes
        tag_diff = differ.deep_diff(acig.get("tags", {}), tags or {})
        if tag_diff:
            ret["changes"]["tags"] = tag_diff

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Container instance group {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["comment"] = "Container instance group {0} would be updated.".format(
                name
            )
            ret["result"] = None
            return ret

    elif ctx["test"]:
        ret["comment"] = "Container instance group {0} would be created.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": {},
            "new": new,
        }
        return ret

    acig_kwargs = kwargs.copy()
    acig_kwargs.update(connection_auth)

    acig = await hub.exec.azurerm.containerinstance.group.create_or_update(
        ctx,
        name,
        resource_group,
        containers=containers,
        os_type=os_type,
        restart_policy=restart_policy,
        tags=tags,
        **acig_kwargs,
    )

    if "error" not in acig:
        ret["result"] = True
        ret["comment"] = f"Container instance group {name} has been {action}d."
        if not ret["changes"]:
            ret["changes"] = {"old": {}, "new": new}
        return ret

    ret["comment"] = "Failed to {0} container instance group {1}! ({2})".format(
        action, name, acig.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Ensure a container instance group does not exist in a resource group.

    :param name: Name of the container instance group.

    :param resource_group: The name of the resource group to which the container instance group belongs.

    .. code-block:: yaml

        Ensure container instance group is absent:
            azurerm.containerinstance.group.absent:
                - name: containergroup
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

    acig = {}

    acig = await hub.exec.azurerm.containerinstance.group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in acig:
        ret["result"] = True
        ret["comment"] = "Container instance group {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Container instance group {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": acig,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.containerinstance.group.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Container instance group {0} has been deleted.".format(name)
        ret["changes"] = {"old": acig, "new": {}}
        return ret

    ret["comment"] = "Failed to delete container instance group {0}!".format(name)
    return ret
