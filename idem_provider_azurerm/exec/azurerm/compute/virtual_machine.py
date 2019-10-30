# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Compute Virtual Machine Execution Module

.. versionadded:: 1.0.0

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

'''

# Python libs
from __future__ import absolute_import
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import is_valid_resource_id
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def capture(hub, name, destination_name, resource_group, prefix='capture-', overwrite=False, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Captures the VM by copying virtual hard disks of the VM and outputs
    a template that can be used to create similar VMs.

    :param name: The name of the virtual machine.

    :param destination_name: The destination container name.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    :param prefix: (Default: 'capture-') The captured virtual hard disk's name prefix.

    :param overwrite: (Default: False) Overwrite the destination disk in case of conflict.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.capture testvm testcontainer testgroup

    '''
    # pylint: disable=invalid-name
    VirtualMachineCaptureParameters = getattr(
        azure.mgmt.compute.models, 'VirtualMachineCaptureParameters'
    )

    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.capture(
            resource_group_name=resource_group,
            vm_name=name,
            parameters=VirtualMachineCaptureParameters(
                vhd_prefix=prefix,
                destination_container_name=destination_name,
                overwrite_vhds=overwrite
            )
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def get(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Retrieves information about the model view or the instance view of a
    virtual machine.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.get testvm testgroup

    '''
    expand = kwargs.get('expand')

    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.get(
            resource_group_name=resource_group,
            vm_name=name,
            expand=expand
        )
        result = vm.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def convert_to_managed_disks(hub, name, resource_group, **kwargs):  # pylint: disable=invalid-name
    '''
    .. versionadded:: 1.0.0

    Converts virtual machine disks from blob-based to managed disks. Virtual
    machine must be stop-deallocated before invoking this operation.

    :param name: The name of the virtual machine to convert.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.convert_to_managed_disks testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.convert_to_managed_disks(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def deallocate(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Power off a virtual machine and deallocate compute resources.

    :param name: The name of the virtual machine to deallocate.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.deallocate testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    result = False
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.deallocate(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def generalize(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Set the state of a virtual machine to 'generalized'.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.generalize testvm testgroup

    '''
    result = False
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        compconn.virtual_machines.generalize(
            resource_group_name=resource_group,
            vm_name=name
        )
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)

    return result


async def list_(hub, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List all virtual machines within a resource group.

    :param resource_group: The resource group name to list virtual
        machines within.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list testgroup

    '''
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        vms = await hub.exec.utils.azurerm.paged_object_to_list(
            compconn.virtual_machines.list(
                resource_group_name=resource_group
            )
        )
        for vm in vms:  # pylint: disable=invalid-name
            result[vm['name']] = vm
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_all(hub, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List all virtual machines within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list_all

    '''
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        vms = await hub.exec.utils.azurerm.paged_object_to_list(
            compconn.virtual_machines.list_all()
        )
        for vm in vms:  # pylint: disable=invalid-name
            result[vm['name']] = vm
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_available_sizes(hub, name, resource_group, **kwargs):  # pylint: disable=invalid-name
    '''
    .. versionadded:: 1.0.0

    Lists all available virtual machine sizes to which the specified virtual
    machine can be resized.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list_available_sizes testvm testgroup

    '''
    result = {}
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        sizes = await hub.exec.utils.azurerm.paged_object_to_list(
            compconn.virtual_machines.list_available_sizes(
                resource_group_name=resource_group,
                vm_name=name
            )
        )
        for size in sizes:
            result[size['name']] = size
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def power_off(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Power off (stop) a virtual machine.

    :param name: The name of the virtual machine to stop.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.power_off testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.power_off(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def restart(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Restart a virtual machine.

    :param name: The name of the virtual machine to restart.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.restart testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.restart(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def start(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Power on (start) a virtual machine.

    :param name: The name of the virtual machine to start.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.start testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.start(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def redeploy(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Redeploy a virtual machine.

    :param name: The name of the virtual machine to redeploy.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.redeploy testvm testgroup

    '''
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.redeploy(
            resource_group_name=resource_group,
            vm_name=name
        )
        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
