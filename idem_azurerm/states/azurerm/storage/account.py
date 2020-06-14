# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Storage Account State Module

.. versionadded:: 2.0.0

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

    Example acct setup for Azure Resource Manager authentication:

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
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging

log = logging.getLogger(__name__)

TREQ = {"present": {"require": ["states.azurerm.resource.group.present",]}}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    sku,
    kind,
    location,
    custom_domain=None,
    encryption=None,
    network_rule_set=None,
    access_tier=None,
    https_traffic_only=None,
    is_hns_enabled=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a storage account exists in the resource group.

    :param name: The name of the storage account being created. Storage account names must be between 3 and 24
        characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param sku: The name of the storage account SKU. Possible values include: 'Standard_LRS', 'Standard_GRS',
        'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS', 'Premium_ZRS', 'Standard_GZRS', and 'Standard_RAGZRS'.

    :param kind: Indicates the type of storage account. Possible values include: 'Storage', 'StorageV2', 'BlobStorage'.

    :param location: Gets or sets the location of the resource. This will be one of the supported and registered Azure
        Geo Regions (e.g. West US, East US, Southeast Asia, etc.). The geo region of a resource cannot be changed once
        it is created, but if an identical geo region is specified on update, the request will succeed.

    :param custom_domain: User domain assigned to the storage account. Valid parameters are:
        - ``name``: Required. Gets or sets the custom domain name assigned to the storage account. Name is the CNAME
                    source. To clear the existing custom domain, use an empty string for this property.
        - ``use_sub_domain_name``: Indicates whether indirect CName validation is enabled. Default value is false.
                                   This should only be set on updates.

    :param encryption: Provides the encryption settings on the account. If left unspecified the account encryption
        settings will remain the same. The default setting is unencrypted.

    :param network_rule_set: A dictionary representing a NetworkRuleSet object.

    :param access_tier: The access tier is used for billing. Required for when the kind is set to 'BlobStorage'.
        Possible values include: 'Hot' and 'Cool'.

    :param https_traffic_only: Allows https traffic only to storage service if set to True. The default value
        is False.

    :param is_hns_enabled: Account HierarchicalNamespace enabled if set to True. The default value is False.

    :param tags: A dictionary of strings can be passed as tag metadata to the storage account object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure storage account exists:
            azurerm.storage.account.present:
                - name: my_account
                - resource_group: my_rg
                - sku: 'Standard_LRS'
                - kind: 'Storage'
                - location: 'eastus'
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    account = await hub.exec.azurerm.storage.account.get_properties(
        ctx, name, resource_group, **connection_auth
    )

    if "error" not in account:
        action = "update"
        tag_changes = differ.deep_diff(account.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if sku != account.get("sku").get("name"):
            ret["changes"]["sku"] = {"old": account.get("sku").get("name"), "new": sku}

        if kind != account.get("kind"):
            ret["changes"]["kind"] = {"old": account.get("kind"), "new": kind}

        if https_traffic_only is not None:
            if https_traffic_only != account.get("enable_https_traffic_only"):
                ret["changes"]["enable_https_traffic_only"] = {
                    "old": account.get("enable_https_traffic_only"),
                    "new": https_traffic_only,
                }

        if is_hns_enabled is not None:
            if is_hns_enabled != account.get("is_hns_enabled"):
                ret["changes"]["is_hns_enabled"] = {
                    "old": account.get("is_hns_enabled"),
                    "new": is_hns_enabled,
                }

        if network_rule_set:
            rule_set_changes = differ.deep_diff(
                account.get("network_rule_set", {}), network_rule_set or {}
            )
            if rule_set_changes:
                ret["changes"]["network_rule_set"] = rule_set_changes

        if encryption:
            encryption_changes = differ.deep_diff(
                account.get("encryption", {}), encryption or {}
            )
            if encryption_changes:
                ret["changes"]["encryption"] = encryption_changes

        # The Custom Domain can only be added on once, so if it already exists then this cannot be changed
        if custom_domain:
            domain_changes = differ.deep_diff(
                account.get("custom_domain", {}), custom_domain or {}
            )
            if domain_changes:
                ret["changes"]["custom_domain"] = domain_changes

        if access_tier:
            if access_tier != account.get("access_tier"):
                ret["changes"]["access_tier"] = {
                    "old": account.get("access_tier"),
                    "new": access_tier,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Storage account {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Storage account {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "sku": sku,
                "kind": kind,
                "location": location,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if access_tier:
            ret["changes"]["new"]["access_tier"] = access_tier
        if custom_domain:
            ret["changes"]["new"]["custom_domain"] = custom_domain
        if encryption:
            ret["changes"]["new"]["encryption"] = encryption
        if network_rule_set:
            ret["changes"]["new"]["network_rule_set"] = network_rule_set
        if https_traffic_only is not None:
            ret["changes"]["new"]["enable_https_traffic_only"] = https_traffic_only
        if is_hns_enabled is not None:
            ret["changes"]["new"]["is_hns_enabled"] = is_hns_enabled

    if ctx["test"]:
        ret["comment"] = "Storage account {0} would be created.".format(name)
        ret["result"] = None
        return ret

    account_kwargs = kwargs.copy()
    account_kwargs.update(connection_auth)

    account = await hub.exec.azurerm.storage.account.create(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        tags=tags,
        sku=sku,
        kind=kind,
        location=location,
        custom_domain=custom_domain,
        encryption=encryption,
        network_rule_set=network_rule_set,
        access_tier=access_tier,
        https_traffic_only=https_traffic_only,
        is_hns_enabled=is_hns_enabled,
        **account_kwargs,
    )

    if "error" not in account:
        ret["result"] = True
        ret["comment"] = f"Storage account {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} storage acccount {1}! ({2})".format(
        action, name, account.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a storage account does not exist in the resource group.

    :param name: The name of the storage account being deleted.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml
        Ensure storage account does not exist:
            azurerm.storage.account.absent:
                - name: my_account
                - resource_group: my_rg
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

    account = await hub.exec.azurerm.storage.account.get_properties(
        ctx, name, resource_group, **connection_auth
    )

    if "error" in account:
        ret["result"] = True
        ret["comment"] = "Storage account {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Storage account {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": account,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.storage.account.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Storage account {0} has been deleted.".format(name)
        ret["changes"] = {"old": account, "new": {}}
        return ret

    ret["comment"] = "Failed to delete storage account {0}!".format(name)
    return ret
