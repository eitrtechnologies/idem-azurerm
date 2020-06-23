# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Policy Execution Module

.. versionadded:: 1.0.0

.. versionchanged:: 2.3.2

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
from __future__ import absolute_import
from json import loads, dumps
from uuid import UUID
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from azure.mgmt.resource.policy.models import ErrorResponseException
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def assignment_delete(hub, ctx, name, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a policy assignment.

    :param name: The name of the policy assignment to delete.

    :param scope: The scope of the policy assignment.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.assignment_delete testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852

    """
    result = False
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        # pylint: disable=unused-variable
        policy = polconn.policy_assignments.delete(
            policy_assignment_name=name, scope=scope
        )
        result = True
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)

    return result


async def assignment_create(hub, ctx, name, scope, definition_name, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.3.2

    Create a policy assignment.

    :param name: The name of the policy assignment to create.

    :param scope: The scope of the policy assignment.

    :param definition_name: The name of the policy definition to assign.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.assignment_create testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852 testpolicy

    """
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)

    definition = await hub.exec.azurerm.resource.policy.definition_get(
        ctx=ctx, name=definition_name, **kwargs
    )

    if "error" not in definition:
        definition_id = str(definition["id"])

        prop_kwargs = {"policy_definition_id": definition_id}

        policy_kwargs = kwargs.copy()
        policy_kwargs.update(prop_kwargs)

        try:
            policy_model = await hub.exec.azurerm.utils.create_object_model(
                "resource.policy", "PolicyAssignment", **policy_kwargs
            )
        except TypeError as exc:
            result = {
                "error": "The object model could not be built. ({0})".format(str(exc))
            }
            return result

        try:
            policy = polconn.policy_assignments.create(
                scope=scope, policy_assignment_name=name, parameters=policy_model
            )
            result = policy.as_dict()
        except (CloudError, ErrorResponseException) as exc:
            if hasattr(exc, "error"):
                exc = exc.error
            await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
            result = {"error": str(exc)}
        except SerializationError as exc:
            result = {
                "error": "The object model could not be parsed. ({0})".format(str(exc))
            }
    else:
        result = {
            "error": 'The policy definition named "{0}" could not be found.'.format(
                definition_name
            )
        }

    return result


async def assignment_get(hub, ctx, name, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific policy assignment.

    :param name: The name of the policy assignment to query.

    :param scope: The scope of the policy assignment.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.assignment_get testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852

    """
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        policy = polconn.policy_assignments.get(
            policy_assignment_name=name, scope=scope
        )
        result = policy.as_dict()
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def assignments_list_for_resource_group(
    hub, ctx, resource_group, **kwargs
):  # pylint: disable=invalid-name
    """
    .. versionadded:: 1.0.0

    List all policy assignments for a resource group.

    :param resource_group: The resource group name to list policy assignments within.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.assignments_list_for_resource_group testgroup

    """
    result = {}
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        policy_assign = await hub.exec.azurerm.utils.paged_object_to_list(
            polconn.policy_assignments.list_for_resource_group(
                resource_group_name=resource_group, filter=kwargs.get("filter")
            )
        )

        for assign in policy_assign:
            result[assign["name"]] = assign
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def assignments_list(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all policy assignments for a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.assignments_list

    """
    result = {}
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        policy_assign = await hub.exec.azurerm.utils.paged_object_to_list(
            polconn.policy_assignments.list()
        )

        for assign in policy_assign:
            result[assign["name"]] = assign
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def definition_create_or_update(
    hub, ctx, name, policy_rule, **kwargs
):  # pylint: disable=invalid-name
    """
    .. versionadded:: 1.0.0

    Create or update a policy definition.

    :param name: The name of the policy definition to create or update.

    :param policy_rule: A dictionary defining the
        `policy rule <https://docs.microsoft.com/en-us/azure/azure-policy/policy-definition#policy-rule>`_.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.definition_create_or_update testpolicy '{...rule definition..}'

    """
    if not isinstance(policy_rule, dict):
        result = {"error": "The policy rule must be a dictionary!"}
        return result

    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)

    # Convert OrderedDict to dict
    prop_kwargs = {"policy_rule": loads(dumps(policy_rule))}

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(prop_kwargs)

    try:
        policy_model = await hub.exec.azurerm.utils.create_object_model(
            "resource.policy", "PolicyDefinition", **policy_kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        policy = polconn.policy_definitions.create_or_update(
            policy_definition_name=name, parameters=policy_model
        )
        result = policy.as_dict()
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def definition_delete(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a policy definition.

    :param name: The name of the policy definition to delete.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.definition_delete testpolicy

    """
    result = False
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        # pylint: disable=unused-variable
        policy = polconn.policy_definitions.delete(policy_definition_name=name)
        result = True
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)

    return result


async def definition_get(hub, ctx, name, policy_type=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.3.2

    Get details about a specific policy definition.

    :param name: The name of the policy definition to query.

    :param policy_type: Set to "BuiltIn" to get a built-in policy definition.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.definition_get testpolicy

    """
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)

    try:
        if not policy_type:
            UUID(name, version=4)
            policy_type = "BuiltIn"
    except ValueError:
        pass

    try:
        if policy_type and policy_type.lower() == "builtin":
            policy_def = polconn.policy_definitions.get_built_in(
                policy_definition_name=name
            )
        else:
            policy_def = polconn.policy_definitions.get(policy_definition_name=name)
        result = policy_def.as_dict()
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def definitions_list(hub, ctx, hide_builtin=False, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all policy definitions for a subscription.

    :param hide_builtin: Boolean which will filter out BuiltIn policy definitions from the result.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.policy.definitions_list

    """
    result = {}
    polconn = await hub.exec.azurerm.utils.get_client(ctx, "policy", **kwargs)
    try:
        policy_defs = await hub.exec.azurerm.utils.paged_object_to_list(
            polconn.policy_definitions.list()
        )

        for policy in policy_defs:
            if not (hide_builtin and policy["policy_type"] == "BuiltIn"):
                result[policy["name"]] = policy
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
