# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Replication Execution Module

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
    hub, ctx, location, registry_name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates a replication for a container registry with the specified parameters.

    :param location: The location of the replica. This cannot be changed after the resource is created and is also
        used for the replica name.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.replication.create_or_update eastus2 testrepo testgroup

    """
    result = {}

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    try:
        repl = regconn.replications.create(
            replication_name=location,
            registry_name=registry_name,
            resource_group_name=resource_group,
            location=location,
            tags=tags,
        )
        repl.wait()
        result = repl.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, location, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets the properties of the specified replication.

    :param location: The location of the replica.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.replication.get eastus2 testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.replications.get(
            replication_name=location,
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


async def list_(hub, ctx, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists all the replications for the specified container registry.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.replication.list testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        repls = await hub.exec.azurerm.utils.paged_object_to_list(
            regconn.replications.list(
                registry_name=registry_name, resource_group_name=resource_group
            )
        )
        for repl in repls:
            result[repl["name"]] = repl
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, location, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Deletes a replication from a container registry.

    :param location: The location of the replica.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.replication.delete repl testrepo testgroup

    """
    result = False
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.replications.delete(
            replication_name=location,
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
