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

    Lists all the container registries under the specified subscription or resource group.

    :param name: Checks whether the container registry name is available for use. The name must contain only
        alphanumeric characters, be globally unique, and between 5 and 50 characters in length.

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


async def create(
    hub,
    ctx,
    name,
    resource_group,
    sku="Basic",
    admin_user_enabled=False,
    default_action=None,
    virtual_network_rules=None,
    ip_rules=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates a container registry with the specified parameters.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param sku: The SKU name of the container registry. Required for registry creation. Possible
        values include: 'Classic', 'Basic', 'Standard', 'Premium'

    :param admin_user_enabled: This value that indicates whether the admin user is enabled.

    :param default_action: The default action of allow or deny when no other rules match.
        Possible values include: 'Allow', 'Deny'. Not available for 'Basic' tier.

    :param virtual_network_rules: A list of virtual network rule dictionaries where one key is the "action"
        of the rule (Allow/Deny) and the other key is the "virtual_network_resource_id" which is the full
        resource ID path of a subnet. Not available for 'Basic' tier.

    :param ip_rules: A list of IP rule dictionaries where one key is the "action" of the rule (Allow/Deny)
        and the other key is the "ip_address_or_range" which specifies the IP or IP range in CIDR format.
        Only IPV4 addresses are allowed. Not available for 'Basic' tier.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.create testrepo testgroup

    """
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

    result = {}

    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )

    if sku.title() != "Basic":
        kwargs["network_rule_set"] = {
            "default_action": default_action,
            "virtual_network_rules": virtual_network_rules,
            "ip_rules": ip_rules,
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


async def list_policies(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Lists the policies for the specified container registry.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.containerregistry.registry.list_policies testrepo testgroup

    """
    result = {}
    regconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerregistry", **kwargs
    )
    try:
        policies = regconn.registries.list_policies(
            registry_name=name, resource_group_name=resource_group
        )
        result = policies.as_dict()
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
        include: 'password', 'password2'

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
