# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute SSH Public Key State Module

.. versionadded:: 4.0.0

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

TREQ = {
    "present": {"require": ["states.azurerm.resource.group.present",]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    public_key=None,
    generate_key_pair=False,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Ensures the SSH public key exists.

    :param name: The name of the SSH public key.

    :param resource_group: The name of the resource group name assigned to the SSH public key.

    :param public_key: SSH public key used to authenticate to a virtual machine through ssh. If this property is not
        initially provided when the resource is created, the ``public_key`` parameter will be populated when the
        generate_key_pair module is called. If the public key is provided upon resource creation, the provided public
        key needs to be at least 2048-bit and in ssh-rsa format.

    :param generate_key_pair: A boolean flag specifying whether or not to generate a public/private key pair to
        populates the SSH public key resource with the public key. The length of the key will be 3072 bits. This
        may only be done if the SSH public key resource does not already have a public key associated with it.
        Defaults to False. This parameter can not be specified at the same time as the ``public_key`` parameter.

    :param tags: A dictionary of strings can be passed as tag metadata to the SSH public key resource object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure SSH Public Key exists:
            azurerm.compute.ssh_public_key.present:
                - name: test_key
                - resource_group: test_group
                - tags:
                    contact_name: Elmer Fudd Gantry

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

    if generate_key_pair and public_key:
        log.error(
            "The generate_key_pair and public_key parameters cannot both be specified. The public key "
            "specified within the public_key parameter will be used for the SSH public key resource."
        )
        generate_key_pair = False

    key = await hub.exec.azurerm.compute.ssh_public_key.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in key:
        action = "update"

        tag_changes = differ.deep_diff(key.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if public_key:
            if public_key != key.get("public_key"):
                ret["changes"]["public_key"] = {
                    "old": key.get("public_key"),
                    "new": public_key,
                }

        if generate_key_pair:
            if key.get("public_key"):
                log.error(
                    "The generate_key_pair parameter was set as True; however, the SSH public key resource "
                    "already has a public key associated with it, so Azure will not generate a new key pair."
                )
                generate_key_pair = False

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "SSH public key {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "SSH public key {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "SSH public key {0} would be created.".format(name)
        ret["result"] = None
        return ret

    key_kwargs = kwargs.copy()
    key_kwargs.update(connection_auth)

    if action == "create":
        key = await hub.exec.azurerm.compute.ssh_public_key.create(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            public_key=public_key,
            tags=tags,
            **key_kwargs,
        )
    elif action == "update":
        key = await hub.exec.azurerm.compute.ssh_public_key.update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            public_key=public_key,
            tags=tags,
            **key_kwargs,
        )

    generated_pair = {}
    if generate_key_pair:
        generated_pair = await hub.exec.azurerm.compute.ssh_public_key.generate_key_pair(
            ctx=ctx, name=name, resource_group=resource_group,
        )
        generated_pair.pop("id", None)

    if action == "create":
        if generated_pair:
            key.update(generated_pair)
        ret["changes"] = {"old": {}, "new": key}
    elif action == "update" and generated_pair:
        ret["changes"]["public_key"] = {"new": generated_pair.get("public_key")}
        ret["changes"]["private_key"] = {"new": generated_pair.get("private_key")}

    if "error" not in key:
        ret["result"] = True
        ret["comment"] = f"SSH public key {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} SSH public key {1}! ({2})".format(
        action, name, key.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Ensures the specified SSH public key resource does not exist.

    :param name: The name of the SSH public key resource.

    :param resource_group: The name of the resource group.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure ssh public key absent:
            azurerm.compute.ssh_public_key.absent:
                - name: test_key
                - resource_group: test_group

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

    key = await hub.exec.azurerm.compute.ssh_public_key.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in key:
        ret["result"] = True
        ret["comment"] = "SSH public key {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "SSH public key {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": key,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.compute.ssh_public_key.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "SSH public key {0} has been deleted.".format(name)
        ret["changes"] = {"old": key, "new": {}}
        return ret

    ret["comment"] = "Failed to delete SSH public key {0}!".format(name)
    return ret
