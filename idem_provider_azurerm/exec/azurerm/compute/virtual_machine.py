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
import os

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(hub, name, resource_group, vm_size, admin_username='idem', os_disk_create_option='FromImage',
                           os_disk_size_gb=30, ssh_public_keys=None, allocate_public_ip=False,
                           create_interfaces=True, network_resource_group=None, virtual_network=None,
                           subnet=None, network_interfaces=None, os_disk_vhd_uri=None, os_disk_image_uri=None,
                           os_type=None, os_disk_name=None, os_disk_caching=None, image=None, admin_password=None,
                           **kwargs):
    '''
    .. versionadded:: 1.0.0

    Create or update a virtual machine.

    :param name: The virtual machine to create.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param vm_size: The size of the virtual machine.

    # These can be passed as kwargs:
    #   priority = low or regular
    #   eviction_policy = deallocate or delete
    #   license_type = Windows_Client or Windows_Server
    #   zones = [ list of zone numbers ]

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.create_or_update testvm testgroup

    '''
    if 'location' not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            resource_group, **kwargs
        )

        if 'error' in rg_props:
            log.error(
                'Unable to determine location from resource group specified.'
            )
            return False
        kwargs['location'] = rg_props['location']

    if not network_interfaces:
        network_interfaces = []

    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)

    params = kwargs.copy()

    # This section creates dictionaries if required in order to properly create SubResource objects
    if 'availability_set' in params and not isinstance(params['availability_set'], dict):
        params.update({'availability_set': {'id': params['availability_set']}})

    if 'virtual_machine_scale_set' in params and not isinstance(params['virtual_machine_scale_set'], dict):
        params.update({'virtual_machine_scale_set': {'id': params['virtual_machine_scale_set']}})

    if 'proximity_placement_group' in params and not isinstance(params['proximity_placement_group'], dict):
        params.update({'proximity_placement_group': {'id': params['proximity_placement_group']}})

    if 'host' in params and not isinstance(params['host'], dict):
        params.update({'host': {'id': params['host']}})

    if os_disk_image_uri and not isinstance(os_disk_image_uri, dict):
        os_disk_image_uri = {'id': os_disk_image_uri}

    if os_disk_vhd_uri and not isinstance(os_disk_vhd_uri, dict):
        os_disk_vhd_uri = {'id': os_disk_vhd_uri}

    if not network_interfaces and create_interfaces:
        ipc = {'name': f'{name}-iface0-ip'}

        if allocate_public_ip:
            pubip = await hub.exec.azurerm.network.public_ip_address.create_or_update(
                f'{name}-ip',
                resource_group,
                **kwargs
            )

            try:
                ipc.update({'public_ip_address': {'id': pubip['id']}})
            except KeyError as exc:
                result = {'error': 'The public IP address could not be created. ({0})'.format(str(exc))}
                return result

        iface = await hub.exec.azurerm.network.network_interface.create_or_update(
            f'{name}-iface0',
            [ipc],
            subnet,
            virtual_network,
            network_resource_group or resource_group,
            **kwargs
        )

        try:
            nic = {'id': iface['id']}
        except KeyError as exc:
            result = {'error': 'The network interface could not be created. ({0})'.format(str(exc))}
            return result

        network_interfaces.append(nic)

    params.update(
        {
            #'plan': {
            #    'name' None,
            #    'publisher': None,
            #    'product': None,
            #    'promotion_code': None
            #},
            'hardware_profile': {
                'vm_size': vm_size.lower()
            },
            'storage_profile': {
                'os_disk': {
                    'os_type': os_type,
                    #'encryption_settings': {
                    #    'disk_encryption_key': {
                    #        'secret_url': '',
                    #        'source_vault': { id: '' }
                    #    },
                    #    'key_encryption_key': {
                    #        'key_url': '',
                    #        'source_vault': { id: '' }
                    #    },
                    #    'enabled': None # True or False
                    #},
                    'name': os_disk_name,
                    'vhd': os_disk_vhd_uri,
                    'image': os_disk_image_uri,
                    'caching': os_disk_caching, # ReadOnly or ReadWrite
                    #'write_accelerator_enabled': None, # True or False
                    #'diff_disk_settings': { 'option': None }, # Local or None
                    'create_option': os_disk_create_option, # Attach or FromImage
                    'disk_size_gb': os_disk_size_gb,
                    #'managed_disk': { 'id': None, 'storage_account_type': None } # (Standard|Premium)_LRS or (Standard|Ultra)SSD_LRS
                },
                'data_disks': [
                    #{
                    #    'lun': None,
                    #    'name': None,
                    #    'vhd': { 'uri': '' },
                    #    'image': { 'uri': '' },
                    #    'caching': None, # ReadOnly or ReadWrite
                    #    'write_accelerator_enabled': None, # True or False
                    #    'create_option': None, # Attach or FromImage
                    #    'disk_size_gb': None,
                    #    'managed_disk': { 'id': None, 'storage_account_type': None }, # (Standard|Premium)_LRS or (Standard|Ultra)SSD_LRS
                    #    'to_be_detached': None # True or False
                    #}
                ]
            },
            #'additional_capabilities': {
            #    'ultra_ssd_enabled': None
            #},
            'os_profile': {
                'computer_name': name,
                'admin_username': admin_username,
                'admin_password': admin_password,
            #    'custom_data': None,
            #    'windows_configuration': None,
            #    'secrets': None,
            #    'allow_extension_operations': None,
            #    'require_guest_provision_signal': None
            },
            'network_profile': {
                'network_interfaces': network_interfaces
            },
            #'diagnostics_profiles': {
            #    'boot_diagnostics': {
            #        'enabled': None, # True or False
            #        'storage_uri': # storage account URI
            #    }
            #},
            #'identity': {
            #    'type': None, # SystemAssigned or UserAssigned
            #    'user_assigned_identities': None # VirtualMachineIdentityUserAssignedIdentitiesValue
            #},
            #'billing_profile': { max_price: None }
        }
    )

    if isinstance(ssh_public_keys, list):
        pubkeys = []
        for pubkey in ssh_public_keys:
            if os.path.isfile(pubkey):
                try:
                    with open(pubkey, 'r') as pubkey_file:
                        pubkeys.append(
                            {
                                'key_data': pubkey_file.read(),
                                'path': f'/home/{admin_username}/.ssh/authorized_keys'
                            }
                        )
                except FileNotFoundError as exc:
                    log.error(
                        'Unable to open ssh public key file: %s (%s)', pubkey, exc
                    )
            else:
                pubkeys.append(
                    {
                        'key_data': pubkey,
                        'path': f'/home/{admin_username}/.ssh/authorized_keys'
                    }
                )

        params['os_profile'].update(
            {
                'linux_configuration': {
                    'disable_password_authentication': True,
                    'ssh': {
                        'public_keys': pubkeys
                    }
                }
            }
        )

    if image:
        if is_valid_resource_id(image):
            params['storage_profile'].update(
                { 'image_reference': { 'id': image }}
            )
        elif '|' in image:
            image_keys = ['publisher', 'offer', 'sku', 'version']
            params['storage_profile'].update(
                { 'image_reference': dict(zip(image_keys, image.split('|'))) }
            )

    try:
        vmmodel = await hub.exec.utils.azurerm.create_object_model(
            'compute',
            'VirtualMachine',
            **params
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        vm = compconn.virtual_machines.create_or_update(
            resource_group_name=resource_group,
            vm_name=name,
            parameters=vmmodel
        )

        vm.wait()
        vm_result = vm.result()
        result = vm_result.as_dict()

        network_interfaces = []

        # Give some more details about the sub-objects
        for iface in result['network_profile']['network_interfaces']:
            iface_dict = parse_resource_id(
                iface['id']
            )

            iface_details = await hub.exec.azurerm.network.network_interface.get(
                resource_group=iface_dict['resource_group'],
                name=iface_dict['name'],
                **kwargs
            )

            network_interfaces.append(iface_details)

        result['network_profile']['network_interfaces'] = network_interfaces

    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def delete(hub, name, resource_group, cleanup_disks=False, cleanup_data_disks=False, cleanup_interfaces=False,
                 **kwargs):
    '''
    .. versionadded:: 1.0.0

    Delete a virtual machine.

    :param name: The virtual machine to delete.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.delete testvm testgroup

    '''
    result = False
    compconn = await hub.exec.utils.azurerm.get_client('compute', **kwargs)

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        resource_group=resource_group,
        name=name,
        **kwargs
    )

    try:
        poller = compconn.virtual_machines.delete(
            resource_group_name=resource_group,
            vm_name=name
        )

        poller.wait()

        if cleanup_disks:
            os_disk = parse_resource_id(
                vm['storage_profile']['os_disk'].get('managed_disk', {}).get('id')
            )

            os_disk_ret = await hub.exec.azurerm.compute.disk.delete(
                resource_group=os_disk['resource_group'],
                name=os_disk['name'],
                **kwargs
            )

        if cleanup_data_disks:
            for disk in vm['storage_profile']['data_disks']:
                disk_dict = parse_resource_id(
                    disk.get('managed_disk', {}).get('id')
                )

                data_disk_ret = await hub.exec.azurerm.compute.disk.delete(
                    resource_group=disk_dict['resource_group'],
                    name=disk_dict['name'],
                    **kwargs
                )

        if cleanup_interfaces:
            for iface in vm['network_profile']['network_interfaces']:
                iface_dict = parse_resource_id(
                    iface['id']
                )

                iface_details = await hub.exec.azurerm.network.network_interface.get(
                    resource_group=iface_dict['resource_group'],
                    name=iface_dict['name'],
                    **kwargs
                )

                iface_ret = await hub.exec.azurerm.network.network_interface.delete(
                    resource_group=iface_dict['resource_group'],
                    name=iface_dict['name'],
                    **kwargs
                )

                for ipc in iface_details['ip_configurations']:
                    if ipc.get('public_ip_address'):
                        ip_dict = parse_resource_id(
                            ipc['public_ip_address']['id']
                        )

                        ip_ret = await hub.exec.azurerm.network.public_ip_address.delete(
                            resource_group=ip_dict['resource_group'],
                            name=ip_dict['name'],
                            **kwargs
                        )

        result = True

    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('compute', str(exc), **kwargs)

    return result


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
