# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Registry State Module

.. versionadded:: 3.0.0

.. versionchanged:: 4.0.0

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
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
    sku="Basic",
    replica_locations=None,
    admin_user_enabled=False,
    default_action=None,
    virtual_network_rules=None,
    ip_rules=None,
    trust_policy=None,
    quarantine_policy=None,
    retention_policy=None,
    retention_days=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    .. versionchanged:: 4.0.0

    Ensure a container registry exists.

    :param name: The name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    :param sku: The SKU name of the container registry. Required for registry creation. Possible
        values include: 'Basic', 'Standard', 'Premium'

    :param replica_locations: A list of valid Azure regions can be provided in order to enable replication
        to locations other than the location in which the repository was configured.

    :param admin_user_enabled: This value that indicates whether the admin user is enabled.

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

    :param tags: A dictionary of strings can be passed as tag metadata to the object.

    Example usage:

    .. code-block:: yaml

        Ensure container registry exists:
            azurerm.containerregistry.registry.present:
                - name: testrepo
                - resource_group: testgroup
                - sku: Premium
                - location: eastus
                - replica_locations:
                    - westus
                - admin_user_enabled: True
                - default_action: Deny
                - ip_rules:
                    - action: Allow
                      ip_address_or_range: 8.8.8.8/32
                - quarantine_policy: Enabled
                - retention_policy: Enabled
                - retention_days: 7
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"
    just_repl = False

    if not replica_locations:
        replica_locations = []

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    # get existing container registry if present
    acr = await hub.exec.azurerm.containerregistry.registry.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in acr:
        action = "update"

        # sku changes
        if sku.upper() != acr["sku"]["name"].upper():
            ret["changes"]["sku"] = {"old": acr["sku"]["name"], "new": sku}

        # admin_user_enabled changes
        if (
            admin_user_enabled is not None
            and admin_user_enabled != acr["admin_user_enabled"]
        ):
            ret["changes"]["admin_user_enabled"] = {
                "old": acr["admin_user_enabled"],
                "new": admin_user_enabled,
            }

        # default_action changes
        old_da = acr.get("network_rule_set", {}).get("default_action", "")
        if default_action and default_action.upper() != old_da.upper():
            ret["changes"]["default_action"] = {"old": old_da, "new": default_action}

        # virtual_network_rules changes
        if virtual_network_rules:
            old_rules = acr.get("network_rule_set", {}).get("virtual_network_rules", [])
            comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
                old_rules, virtual_network_rules, key_name="virtual_network_resource_id"
            )

            if comp.get("changes"):
                ret["changes"]["virtual_network_rules"] = comp["changes"]

        # ip_rules changes
        if ip_rules:
            old_rules = acr.get("network_rule_set", {}).get("ip_rules", [])
            comp = await hub.exec.azurerm.utils.compare_list_of_dicts(
                old_rules, ip_rules, key_name="ip_address_or_range"
            )

            if comp.get("changes"):
                ret["changes"]["ip_rules"] = comp["changes"]

        # trust_policy changes
        old_pol = acr.get("policies", {}).get("trust_policy", {}).get("status", "")
        if trust_policy and trust_policy.upper() != old_pol.upper():
            ret["changes"]["trust_policy"] = {"old": old_pol, "new": trust_policy}

        # quarantine_policy changes
        old_pol = acr.get("policies", {}).get("quarantine_policy", {}).get("status", "")
        if quarantine_policy and quarantine_policy.upper() != old_pol.upper():
            ret["changes"]["quarantine_policy"] = {
                "old": old_pol,
                "new": quarantine_policy,
            }

        # retention_policy changes
        old_pol = acr.get("policies", {}).get("retention_policy", {}).get("status", "")
        if retention_policy and retention_policy.upper() != old_pol.upper():
            ret["changes"]["retention_policy"] = {
                "old": old_pol,
                "new": retention_policy,
            }

        # retention_days changes
        old_pol = acr.get("policies", {}).get("retention_policy", {}).get("days")
        if retention_days and int(retention_days) != old_pol:
            ret["changes"]["retention_policy"] = {"old": old_pol, "new": retention_days}

        # tag changes
        tag_diff = differ.deep_diff(acr.get("tags", {}), tags or {})
        if tag_diff:
            ret["changes"]["tags"] = tag_diff

        # replica changes
        locs = await hub.exec.azurerm.containerregistry.replication.list(
            ctx, name, resource_group, azurerm_log_level="info", **connection_auth
        )
        locs = sorted([loc.lower() for loc in locs])
        if not locs:
            locs = [acr["location"].lower()]
        replica_locations = sorted(
            [loc.lower() for loc in replica_locations + [acr["location"]]]
        )
        if locs != replica_locations:
            if not ret["changes"]:
                just_repl = True
            ret["changes"]["replica_locations"] = {
                "old": locs.copy(),
                "new": replica_locations.copy(),
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Container registry {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Container registry {0} would be updated.".format(name)
            ret["result"] = None
            return ret

    elif ctx["test"]:
        ret["comment"] = "Container registry {0} would be created.".format(name)
        ret["result"] = None
        return ret

    acr_kwargs = kwargs.copy()
    acr_kwargs.update(connection_auth)
    acr = {}

    if action == "create" or not just_repl:
        acr = await hub.exec.azurerm.containerregistry.registry.create_or_update(
            ctx,
            name,
            resource_group,
            sku=sku,
            admin_user_enabled=admin_user_enabled,
            default_action=default_action,
            virtual_network_rules=virtual_network_rules,
            ip_rules=ip_rules,
            trust_policy=trust_policy,
            quarantine_policy=quarantine_policy,
            retention_policy=retention_policy,
            retention_days=retention_days,
            tags=tags,
            **acr_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": acr}

    if "error" not in acr:
        if "location" in acr_kwargs:
            acr_kwargs.pop("location")

        if action == "create" or ret["changes"].get("replica_locations"):
            delete = []
            repl = ret["changes"].get("replica_locations")
            if repl:
                for loc in repl["new"]:
                    if loc in repl["old"]:
                        replica_locations.remove(loc)
                for loc in repl["old"]:
                    if loc not in repl["new"]:
                        delete.append(loc)

            for repl in replica_locations:
                loc = await hub.exec.azurerm.containerregistry.replication.create_or_update(
                    ctx=ctx,
                    location=repl,
                    registry_name=name,
                    resource_group=resource_group,
                    tags=tags,
                    **acr_kwargs,
                )
                if "error" in loc:
                    log.error("Unable to enable replication to %s!", repl)

            for repl in delete:
                loc = await hub.exec.azurerm.containerregistry.replication.delete(
                    ctx=ctx,
                    location=repl,
                    registry_name=name,
                    resource_group=resource_group,
                    **acr_kwargs,
                )
                if not loc:
                    log.error("Unable to disable replication to %s!", repl)

        ret["result"] = True
        ret["comment"] = f"Container registry {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} container registry {1}! ({2})".format(
        action, name, acr.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Ensure a container registry does not exist in a resource group.

    :param name: Name of the container registry.

    :param resource_group: The name of the resource group to which the container registry belongs.

    .. code-block:: yaml

        Ensure container registry is absent:
            azurerm.containerregistry.registry.absent:
                - name: other_repo
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

    acr = {}

    acr = await hub.exec.azurerm.containerregistry.registry.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in acr:
        ret["result"] = True
        ret["comment"] = "Container registry {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Container registry {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": acr,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.containerregistry.registry.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Container registry {0} has been deleted.".format(name)
        ret["changes"] = {"old": acr, "new": {}}
        return ret

    ret["comment"] = "Failed to delete container registry {0}!".format(name)
    return ret
