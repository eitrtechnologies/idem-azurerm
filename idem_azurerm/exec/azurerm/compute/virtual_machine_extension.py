# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Virtual Machine Extension Operations Execution Module

.. versionadded:: 2.0.0

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

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

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
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub,
    name,
    vm_name,
    resource_group,
    location,
    publisher,
    extension_type,
    version,
    settings,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    The operation to create or update the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine where the extension should be created or updated.

    :param resource_group: The name of the resource group.

    :param location: Resource location.

    :param publisher: The publisher of the extension.

    :param extension_type: Specifies the type of the extension; an example is "CustomScriptExtension".

    :param version: Specifies the version of the script handler.

    :param settings: A dictionary representing the public settings for the extension. This dictionary will be
        utilized as JSON by the SDK operation..

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension.create_or_update test_name test_vm test_group test_loc \
                test_publisher test_type test_version test_settings

    """
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client("compute", **kwargs)

    try:
        paramsmodel = await hub.exec.utils.azurerm.create_object_model(
            "compute",
            "VirtualMachineExtension",
            location=location,
            settings=settings,
            publisher=publisher,
            virtual_machine_extension_type=extension_type,
            type_handler_version=version,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        extension = compconn.virtual_machine_extensions.create_or_update(
            vm_extension_name=name,
            vm_name=vm_name,
            resource_group_name=resource_group,
            extension_parameters=paramsmodel,
        )

        extension.wait()
        result = extension.result().as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, name, vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    The operation to delete the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine where the extension should be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension.delete test_name test_vm test_group

    """
    result = False
    compconn = await hub.exec.utils.azurerm.get_client("compute", **kwargs)

    try:
        extension = compconn.virtual_machine_extensions.delete(
            vm_extension_name=name, vm_name=vm_name, resource_group_name=resource_group
        )

        extension.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, name, vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    The operation to get the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine containing the extension.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension.get test_name test_vm test_group

    """
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client("compute", **kwargs)

    try:
        extension = compconn.virtual_machine_extensions.get(
            vm_extension_name=name, vm_name=vm_name, resource_group_name=resource_group
        )

        result = extension.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    The operation to get all extensions of a Virtual Machine.

    :param vm_name: The name of the virtual machine containing the extension.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine_extension.list test_vm test_group

    """
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client("compute", **kwargs)

    try:
        extensions = compconn.virtual_machine_extensions.list(
            vm_name=vm_name, resource_group_name=resource_group
        )

        extensions_as_list = extensions.as_dict().get("value", {})
        for extension in extensions_as_list:
            result[extension["name"]] = extension
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
