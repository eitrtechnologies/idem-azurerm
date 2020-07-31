# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry Run Execution Module

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


async def get(
    hub, ctx, run_id, registry_name, resource_group, log_link=False, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Gets the detailed information for a given run.

    :param run_id: The run ID.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param log_link: If True, gets a link to download the run logs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.run.get id testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.runs.get(
            run_id=run_id,
            registry_name=registry_name,
            resource_group_name=resource_group,
        )
        result = ret.as_dict()
        if log_link:
            url = regconn.runs.get_log_sas_url(
                run_id=run_id,
                registry_name=registry_name,
                resource_group_name=resource_group,
            )
            result.update(url.as_dict())
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_(
    hub, ctx, registry_name, resource_group, list_filter=None, limit=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Lists all the runs for the specified container registry.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param list_filter: The runs filter to apply on the operation. Arithmetic operators are not supported. The allowed
        string function is 'contains'. All logical operators except 'Not', 'Has', 'All' are allowed.

    :param limit: Limits the maximum number of runs to return.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.run.list testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        runs = await hub.exec.azurerm.utils.paged_object_to_list(
            regconn.runs.list(
                registry_name=registry_name,
                resource_group_name=resource_group,
                filter=list_filter,
                top=limit,
            )
        )
        for run in runs:
            result[run["run_id"]] = run
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def cancel(hub, ctx, run_id, registry_name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Cancel an existing run.

    :param run_id: The run ID.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.run.cancel id testrepo testgroup

    """
    result = False
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        ret = regconn.runs.cancel(
            run_id=run_id,
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


async def update(
    hub, ctx, run_id, registry_name, resource_group, is_archive_enabled=None, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Patch the run properties.

    :param run_id: The run ID.

    :param registry_name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param is_archive_enabled: The value that indicates whether archiving is enabled or not.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.run.update id testrepo testgroup is_archive_enabled=False

    """
    result = {}

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    try:
        run = regconn.runs.update(
            run_id=run_id,
            registry_name=registry_name,
            resource_group_name=resource_group,
            is_archive_enabled=is_archive_enabled,
        )
        run.wait()
        result = run.result().as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerregistry", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
