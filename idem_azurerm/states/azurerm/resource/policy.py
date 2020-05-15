# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Policy State Module

.. versionadded:: 1.0.0

.. versionchanged:: 2.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as a dictionary of
    keyword arguments to the ``connection_auth`` parameter in order to work properly. Since the authentication
    parameters are sensitive, it's recommended to pass them to the states via pillar.

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

    Example Pillar for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass
            mysubscription:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        Ensure resource group exists:
            azurerm.resource.group.present:
                - name: my_rg
                - location: westus
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure resource group is absent:
            azurerm.resource.group.absent:
                - name: other_rg
                - connection_auth: {{ profile }}

"""
# Import Python libs
from __future__ import absolute_import
import json
import logging

log = logging.getLogger(__name__)

TREQ = {
    "assignment_present": {
        "require": ["states.azurerm.resource.policy.definition_present",]
    },
}


async def definition_present(
    hub,
    ctx,
    name,
    policy_rule=None,
    policy_type=None,
    mode=None,
    display_name=None,
    description=None,
    metadata=None,
    parameters=None,
    policy_rule_json=None,
    policy_rule_file=None,
    template="jinja",
    source_hash=None,
    source_hash_name=None,
    skip_verify=False,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.0.0

    Ensure a security policy definition exists.

    :param name:
        Name of the policy definition.

    :param policy_rule:
        A YAML dictionary defining the policy rule. See `Azure Policy Definition documentation
        <https://docs.microsoft.com/en-us/azure/azure-policy/policy-definition#policy-rule>`_ for details on the
        structure. One of ``policy_rule``, ``policy_rule_json``, or ``policy_rule_file`` is required, in that order of
        precedence for use if multiple parameters are used.

    :param policy_rule_json:
        A text field defining the entirety of a policy definition in JSON. See `Azure Policy Definition documentation
        <https://docs.microsoft.com/en-us/azure/azure-policy/policy-definition#policy-rule>`_ for details on the
        structure. One of ``policy_rule``, ``policy_rule_json``, or ``policy_rule_file`` is required, in that order of
        precedence for use if multiple parameters are used. Note that the `name` field in the JSON will override the
        ``name`` parameter in the state.

    :param policy_rule_file:
        The local source location of a JSON file defining the entirety of a policy definition. See `Azure Policy
        Definition documentation <https://docs.microsoft.com/en-us/azure/azure-policy/policy-definition#policy-rule>`_
        for details on the structure. One of ``policy_rule``, ``policy_rule_json``, or ``policy_rule_file`` is required,
        in that order of precedence for use if multiple parameters are used. Note that the `name` field in the JSON
        will override the ``name`` parameter in the state.

    :param policy_type:
        The type of policy definition. Possible values are NotSpecified, BuiltIn, and Custom. Only used with the
        ``policy_rule`` parameter.

    :param mode:
        The policy definition mode. Possible values are NotSpecified, Indexed, and All. Only used with the
        ``policy_rule`` parameter.

    :param display_name:
        The display name of the policy definition. Only used with the ``policy_rule`` parameter.

    :param description:
        The policy definition description. Only used with the ``policy_rule`` parameter.

    :param metadata:
        The policy definition metadata defined as a dictionary. Only used with the ``policy_rule`` parameter.

    :param parameters:
        Required dictionary if a parameter is used in the policy rule. Only used with the ``policy_rule`` parameter.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure policy definition exists:
            azurerm.resource.policy.definition_present:
                - name: testpolicy
                - display_name: Test Policy
                - description: Test policy for testing policies.
                - policy_rule:
                    if:
                      allOf:
                        - equals: Microsoft.Compute/virtualMachines/write
                          source: action
                        - field: location
                          in:
                            - eastus
                            - eastus2
                            - centralus
                    then:
                      effect: deny
                - connection_auth: {{ profile }}

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

    if not policy_rule and not policy_rule_json and not policy_rule_file:
        ret[
            "comment"
        ] = 'One of "policy_rule", "policy_rule_json", or "policy_rule_file" is required!'
        return ret

    if (
        sum(x is not None for x in [policy_rule, policy_rule_json, policy_rule_file])
        > 1
    ):
        ret[
            "comment"
        ] = 'Only one of "policy_rule", "policy_rule_json", or "policy_rule_file" is allowed!'
        return ret

    if (policy_rule_json or policy_rule_file) and (
        policy_type or mode or display_name or description or metadata or parameters
    ):
        ret[
            "comment"
        ] = 'Policy definitions cannot be passed when "policy_rule_json" or "policy_rule_file" is defined!'
        return ret

    temp_rule = {}
    if policy_rule_json:
        try:
            temp_rule = json.loads(policy_rule_json)
        except Exception as exc:
            ret["comment"] = "Unable to load policy rule json! ({0})".format(exc)
            return ret
    elif policy_rule_file:
        try:
            with open(policy_rule_file, "r") as prf:
                temp_rule = json.load(prf)
        except Exception as exc:
            ret["comment"] = 'Unable to load policy rule file "{0}"! ({1})'.format(
                policy_rule_file, exc
            )
            return ret

    policy_name = name
    if policy_rule_json or policy_rule_file:
        if temp_rule.get("name"):
            policy_name = temp_rule.get("name")
        policy_rule = temp_rule.get("properties", {}).get("policyRule")
        policy_type = temp_rule.get("properties", {}).get("policyType")
        mode = temp_rule.get("properties", {}).get("mode")
        display_name = temp_rule.get("properties", {}).get("displayName")
        description = temp_rule.get("properties", {}).get("description")
        metadata = temp_rule.get("properties", {}).get("metadata")
        parameters = temp_rule.get("properties", {}).get("parameters")

    policy = await hub.exec.azurerm.resource.policy.definition_get(
        name, azurerm_log_level="info", **connection_auth
    )

    if "error" not in policy:
        if policy_type and policy_type.lower() != policy.get("policy_type", "").lower():
            ret["changes"]["policy_type"] = {
                "old": policy.get("policy_type"),
                "new": policy_type,
            }

        if (mode or "").lower() != policy.get("mode", "").lower():
            ret["changes"]["mode"] = {"old": policy.get("mode"), "new": mode}

        if (display_name or "").lower() != policy.get("display_name", "").lower():
            ret["changes"]["display_name"] = {
                "old": policy.get("display_name"),
                "new": display_name,
            }

        if (description or "").lower() != policy.get("description", "").lower():
            ret["changes"]["description"] = {
                "old": policy.get("description"),
                "new": description,
            }

        rule_changes = await hub.exec.utils.dictdiffer.deep_diff(
            policy.get("policy_rule", {}), policy_rule or {}
        )
        if rule_changes:
            ret["changes"]["policy_rule"] = rule_changes

        meta_changes = await hub.exec.utils.dictdiffer.deep_diff(
            policy.get("metadata", {}), metadata or {}
        )
        if meta_changes:
            ret["changes"]["metadata"] = meta_changes

        param_changes = await hub.exec.utils.dictdiffer.deep_diff(
            policy.get("parameters", {}), parameters or {}
        )
        if param_changes:
            ret["changes"]["parameters"] = param_changes

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Policy definition {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Policy definition {0} would be updated.".format(name)
            ret["result"] = None
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": policy_name,
                "policy_type": policy_type,
                "mode": mode,
                "display_name": display_name,
                "description": description,
                "metadata": metadata,
                "parameters": parameters,
                "policy_rule": policy_rule,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Policy definition {0} would be created.".format(name)
        ret["result"] = None
        return ret

    # Convert OrderedDict to dict
    if isinstance(metadata, dict):
        metadata = json.loads(json.dumps(metadata))
    if isinstance(parameters, dict):
        parameters = json.loads(json.dumps(parameters))

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(connection_auth)

    policy = await hub.exec.azurerm.resource.policy.definition_create_or_update(
        name=policy_name,
        policy_rule=policy_rule,
        policy_type=policy_type,
        mode=mode,
        display_name=display_name,
        description=description,
        metadata=metadata,
        parameters=parameters,
        **policy_kwargs,
    )

    if "error" not in policy:
        ret["result"] = True
        ret["comment"] = "Policy definition {0} has been created.".format(name)
        return ret

    ret["comment"] = "Failed to create policy definition {0}! ({1})".format(
        name, policy.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def definition_absent(hub, name, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a policy definition does not exist in the current subscription.

    :param name:
        Name of the policy definition.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    policy = await hub.exec.azurerm.resource.policy.definition_get(
        name, azurerm_log_level="info", **connection_auth
    )

    if "error" in policy:
        ret["result"] = True
        ret["comment"] = "Policy definition {0} is already absent.".format(name)
        return ret

    elif ctx["test"]:
        ret["comment"] = "Policy definition {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": policy,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.policy.definition_delete(
        name, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Policy definition {0} has been deleted.".format(name)
        ret["changes"] = {"old": policy, "new": {}}
        return ret

    ret["comment"] = "Failed to delete policy definition {0}!".format(name)
    return ret


async def assignment_present(
    hub,
    ctx,
    name,
    scope,
    definition_name,
    display_name=None,
    description=None,
    assignment_type=None,
    parameters=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a security policy assignment exists.

    :param name:
        Name of the policy assignment.

    :param scope:
        The scope of the policy assignment.

    :param definition_name:
        The name of the policy definition to assign.

    :param display_name:
        The display name of the policy assignment.

    :param description:
        The policy assignment description.

    :param assignment_type:
        The type of policy assignment.

    :param parameters:
        Required dictionary if a parameter is used in the policy rule.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure policy assignment exists:
            azurerm.resource.policy.assignment_present:
                - name: testassign
                - scope: /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852
                - definition_name: testpolicy
                - display_name: Test Assignment
                - description: Test assignment for testing assignments.
                - connection_auth: {{ profile }}

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

    policy = await hub.exec.azurerm.resource.policy.assignment_get(
        name, scope, azurerm_log_level="info", **connection_auth
    )

    if "error" not in policy:
        if (
            assignment_type
            and assignment_type.lower() != policy.get("type", "").lower()
        ):
            ret["changes"]["type"] = {"old": policy.get("type"), "new": assignment_type}

        if scope.lower() != policy["scope"].lower():
            ret["changes"]["scope"] = {"old": policy["scope"], "new": scope}

        pa_name = policy["policy_definition_id"].split("/")[-1]
        if definition_name.lower() != pa_name.lower():
            ret["changes"]["definition_name"] = {"old": pa_name, "new": definition_name}

        if (display_name or "").lower() != policy.get("display_name", "").lower():
            ret["changes"]["display_name"] = {
                "old": policy.get("display_name"),
                "new": display_name,
            }

        if (description or "").lower() != policy.get("description", "").lower():
            ret["changes"]["description"] = {
                "old": policy.get("description"),
                "new": description,
            }

        param_changes = await hub.exec.utils.dictdiffer.deep_diff(
            policy.get("parameters", {}), parameters or {}
        )
        if param_changes:
            ret["changes"]["parameters"] = param_changes

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Policy assignment {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Policy assignment {0} would be updated.".format(name)
            ret["result"] = None
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "scope": scope,
                "definition_name": definition_name,
                "type": assignment_type,
                "display_name": display_name,
                "description": description,
                "parameters": parameters,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Policy assignment {0} would be created.".format(name)
        ret["result"] = None
        return ret

    if isinstance(parameters, dict):
        parameters = json.loads(json.dumps(parameters))

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(connection_auth)
    policy = await hub.exec.azurerm.resource.policy.assignment_create(
        name=name,
        scope=scope,
        definition_name=definition_name,
        type=assignment_type,
        display_name=display_name,
        description=description,
        parameters=parameters,
        **policy_kwargs,
    )

    if "error" not in policy:
        ret["result"] = True
        ret["comment"] = "Policy assignment {0} has been created.".format(name)
        return ret

    ret["comment"] = "Failed to create policy assignment {0}! ({1})".format(
        name, policy.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def assignment_absent(hub, ctx, name, scope, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a policy assignment does not exist in the provided scope.

    :param name:
        Name of the policy assignment.

    :param scope:
        The scope of the policy assignment.

    connection_auth
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    policy = await hub.exec.azurerm.resource.policy.assignment_get(
        name, scope, azurerm_log_level="info", **connection_auth
    )

    if "error" in policy:
        ret["result"] = True
        ret["comment"] = "Policy assignment {0} is already absent.".format(name)
        return ret

    elif ctx["test"]:
        ret["comment"] = "Policy assignment {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": policy,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.policy.assignment_delete(
        name, scope, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Policy assignment {0} has been deleted.".format(name)
        ret["changes"] = {"old": policy, "new": {}}
        return ret

    ret["comment"] = "Failed to delete policy assignment {0}!".format(name)
    return ret
