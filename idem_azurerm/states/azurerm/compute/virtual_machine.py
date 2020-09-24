# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Virtual Machine State Module

.. versionadded:: 1.0.0

.. versionchanged:: 2.0.0

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
import operator

# Azure libs
HAS_LIBS = False
try:
    from msrestazure.tools import parse_resource_id

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.virtual_network.present",
            "states.azurerm.network.virtual_network.subnet_present",
            "states.azurerm.network.network_interface.present",
            "states.azurerm.compute.availability_set.present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    vm_size,
    admin_username="idem",
    os_disk_create_option="FromImage",
    os_disk_size_gb=30,
    ssh_public_keys=None,
    disable_password_auth=None,
    custom_data=None,
    allow_extensions=None,
    enable_automatic_updates=None,
    time_zone=None,
    allocate_public_ip=False,
    create_interfaces=True,
    network_resource_group=None,
    virtual_network=None,
    subnet=None,
    network_interfaces=None,
    os_managed_disk=None,
    os_disk_vhd_uri=None,
    os_disk_image_uri=None,
    os_type=None,
    os_disk_name=None,
    os_disk_caching=None,
    os_write_accel=None,
    os_ephemeral_disk=None,
    ultra_ssd_enabled=None,
    image=None,
    boot_diags_enabled=None,
    diag_storage_uri=None,
    admin_password=None,
    force_admin_password=False,
    max_price=None,
    provision_vm_agent=True,
    userdata_file=None,
    userdata=None,
    enable_disk_enc=False,
    disk_enc_keyvault=None,
    disk_enc_volume_type=None,
    disk_enc_kek_url=None,
    data_disks=None,
    availability_set=None,
    virtual_machine_scale_set=None,
    proximity_placement_group=None,
    host=None,
    host_group=None,
    extensions_time_budget=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.0.0, 4.0.0

    Ensure a virtual machine exists.

    :param name: The virtual machine to ensure is present.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param vm_size: The size of the virtual machine.

    :param admin_username: Specifies the name of the administrator account.

    :param os_disk_create_option: (attach, from_image, or empty) Specifies how the virtual machine should be created.
        The "attach" value is used when you are using a specialized disk to create the virtual machine. The "from_image"
        value is used when you are using an image to create the virtual machine. If you are using a platform image, you
        also use the image_reference element. If you are using a marketplace image, you also use the plan element.

    :param os_disk_size_gb: Specifies the size of an empty OS disk in gigabytes. This element can be used to overwrite
        the size of the disk in a virtual machine image.

    :param ssh_public_keys: The list of SSH public keys used to authenticate with Linux based VMs.

    :param disable_password_auth: (only on Linux) Specifies whether password authentication should be disabled when SSH
        public keys are provided.

    :param custom_data: (only on Linux) Specifies a base-64 encoded string of custom data for cloud-init (not user-data
        scripts). The base-64 encoded string is decoded to a binary array that is saved as a file on the Virtual
        Machine. The maximum length of the binary array is 65535 bytes. For using cloud-init for your VM, see `Using
        cloud-init to customize a Linux VM during creation
        <https://docs.microsoft.com/en-us/azure/virtual-machines/linux/using-cloud-init>`_

    :param allow_extensions: Specifies whether extension operations should be allowed on the virtual machine. This may
        only be set to False when no extensions are present on the virtual machine.

    :param enable_automatic_updates: (only on Windows) Indicates whether automatic updates are enabled for the Windows
        virtual machine. Default value is true. For virtual machine scale sets, this property can be updated and updates
        will take effect on OS reprovisioning.

    :param time_zone: (only on Windows) Specifies the time zone of the virtual machine. e.g. "Pacific Standard Time"

    :param allocate_public_ip: Create and attach a public IP object to the VM.

    :param create_interfaces: Create network interfaces to attach to the VM if none are provided.

    :param network_resource_group: Specify the resource group of the network components referenced in this module.

    :param virtual_network: Virtual network for the subnet which will contain the network interfaces.

    :param subnet: Subnet to which the network interfaces will be attached.

    :param network_interfaces: A list of network interface references ({"id": "/full/path/to/object"}) to attach.

    :param os_managed_disk: A managed disk resource ID or dictionary containing the managed disk parameters. If a
        dictionary is provided, "storage_account_type" can be passed in additional to the "id". Storage account type for
        the managed disk can include: 'Standard_LRS', 'Premium_LRS', 'StandardSSD_LRS', 'UltraSSD_LRS'. NOTE:
        UltraSSD_LRS can only be used with data disks.

    :param os_disk_vhd_uri: The virtual hard disk for the OS ({"uri": "/full/path/to/object"}).

    :param os_disk_image_uri: The source user image virtual hard disk ({"uri": "/full/path/to/object"}). The virtual
        hard disk will be copied before being attached to the virtual machine. If SourceImage is provided, the
        destination virtual hard drive must not exist.

    :param os_type: (linux or windows) This property allows you to specify the type of the OS that is included in the
        disk if creating a VM from user-image or a specialized VHD.

    :param os_disk_name: The OS disk name.

    :param os_disk_caching: (read_only, read_write, or none) Specifies the caching requirements. Defaults
        to "None" for Standard storage and "ReadOnly" for Premium storage.

    :param os_write_accel: Boolean value specifies whether write accelerator should be enabled or disabled on the disk.

    :param os_ephemeral_disk: Boolean value to enable ephemeral "diff" OS disk. `Ephemeral OS disks
        <https://docs.microsoft.com/en-us/azure/virtual-machines/linux/ephemeral-os-disks>`_ are created on the local
        virtual machine (VM) storage and not saved to the remote Azure Storage.

    :param ultra_ssd_enabled: The flag that enables or disables a capability to have one or more managed data disks with
        UltraSSD_LRS storage account type on the VM or VMSS. Managed disks with storage account type UltraSSD_LRS can be
        added to a virtual machine or virtual machine scale set only if this property is enabled.

    :param image: A pipe-delimited representation of an image to use, in the format of "publisher|offer|sku|version".
        Examples - "OpenLogic|CentOS|7.7|latest" or "Canonical|UbuntuServer|18.04-LTS|latest"

    :param boot_diags_enabled: Enables boots diagnostics on the Virtual Machine. Required for use of the
        diag_storage_uri parameter.

    :param diag_storage_uri: Enables boots diagnostics on the Virtual Machine by passing the URI of the storage account
        to use for placing the console output and screenshot.

    :param admin_password: Specifies the password of the administrator account. Note that there are minimum length,
        maximum length, and complexity requirements imposed on this password. See the Azure documentation for details.

    :param force_admin_password: A Boolean flag that represents whether or not the admin password should be updated.
        If it is set to True, then the admin password will be updated if the virtual machine already exists. If it is
        set to False, then the password will not be updated unless other parameters also need to be updated.
        Defaults to False.

    :param provision_vm_agent: Indicates whether virtual machine agent should be provisioned on the virtual machine.
        When this property is not specified in the request body, default behavior is to set it to true. This will ensure
        that VM Agent is installed on the VM so that extensions can be added to the VM later. If attempting to set this
        value, os_type should also be set in order to ensure the proper OS configuration is used.

    :param userdata_file: This parameter can contain a local or web path for a userdata script. If a local file is used,
        then the contents of that file will override the contents of the userdata parameter. If a web source is used,
        then the userdata parameter should contain the command to execute the script file. For instance, if a file
        location of https://raw.githubusercontent.com/saltstack/salt-bootstrap/stable/bootstrap-salt.sh is used then the
        userdata parameter would contain "./bootstrap-salt.sh" along with any desired arguments. Note that PowerShell
        execution policy may cause issues here. For PowerShell files, considered signed scripts or the more insecure
        "powershell -ExecutionPolicy Unrestricted -File ./bootstrap-salt.ps1" addition to the command.

    :param userdata: This parameter is used to pass text to be executed on a system. The native shell will be used on a
        given host operating system.

    :param max_price: Specifies the maximum price you are willing to pay for a Azure Spot VM/VMSS. This price is in US
        Dollars. This price will be compared with the current Azure Spot price for the VM size. Also, the prices are
        compared at the time of create/update of Azure Spot VM/VMSS and the operation will only succeed if max_price is
        greater than the current Azure Spot price. The max_price will also be used for evicting a Azure Spot VM/VMSS if
        the current Azure Spot price goes beyond the maxPrice after creation of VM/VMSS. Possible values are any decimal
        value greater than zero (example: 0.01538) or -1 indicates default price to be up-to on-demand. You can set the
        max_price to -1 to indicate that the Azure Spot VM/VMSS should not be evicted for price reasons. Also, the
        default max price is -1 if it is not provided by you.

    :param priority: (low or regular) Specifies the priority for the virtual machine.

    :param eviction_policy: (deallocate or delete) Specifies the eviction policy for the Azure Spot virtual machine.

    :param license_type: (Windows_Client or Windows_Server) Specifies that the image or disk that is being used was
        licensed on-premises. This element is only used for images that contain the Windows Server operating system.

    :param zones: A list of the virtual machine zones.

    :param availability_set: The resource ID of the availability set that the virtual machine should be assigned to.
        Virtual machines specified in the same availability set are allocated to different nodes to maximize
        availability. For more information about availability sets, see `Manage the availability of virtual
        machines <https://docs.microsoft.com/azure/virtual-machines/virtual-machines-windows-manage-availability>`_.
        Currently, a VM can only be added to availability set at creation time. An existing VM cannot be added to an
        availability set. This parameter cannot be specified if the ``virtual_machine_scale_set`` parameter is also
        specified.

    :param virtual_machine_scale_set: The resource ID of the virtual machine scale set that the virtual machine should
        be assigned to. Virtual machines specified in the same virtual machine scale set are allocated to different
        nodes to maximize availability. Currently, a VM can only be added to virtual machine scale set at creation time.
        An existing VM cannot be added to a virtual machine scale set. This parameter cannot be specified if the
        ``availability_set`` parameter is also specified.

    :param proximity_placement_group: The resource ID of the proximity placement group that the virtual machine should
        be assigned to.

    :param host: The resource ID of the dedicated host that the virtual machine resides in. This parameter cannot be
        specified if the ``host_group`` parameter is also specified.

    :param host_group: The resource ID of the dedicated host group that the virtual machine resides in. This
        parameter cannot be specified if the ``host`` parameter is also specified.

    :param extensions_time_budget: Specifies the time alloted for all extensions to start. The time duration should be
        between 15 minutes and 120 minutes (inclusive) and should be specified in ISO 8601 format. The default value is
        90 minutes (PT1H30M).

    :param tags: A dictionary of strings can be passed as tag metadata to the virtual machine object.

    :param connection_auth: A dictionary with subscription and authentication parameters to be used in connecting to
        the Azure Resource Manager API.

    Virtual Machine Disk Encryption:
        If you would like to enable disk encryption within the virtual machine you must set the enable_disk_enc
        parameter to True. Disk encryption utilizes a VM published by Microsoft.Azure.Security of extension type
        AzureDiskEncryptionForLinux or AzureDiskEncryption, depending on your virtual machine OS. More information
        about Disk Encryption and its requirements can be found in the links below.

        Disk Encryption for Windows Virtual Machines:
        https://docs.microsoft.com/en-us/azure/virtual-machines/windows/disk-encryption-overview

        Disk Encryption for Linux Virtual Machines:
        https://docs.microsoft.com/en-us/azure/virtual-machines/linux/disk-encryption-overview

        The following parameters may be used to implement virtual machine disk encryption:

        - **param enable_disk_enc**: This boolean flag will represent whether disk encryption has been enabled for the
          virtual machine. This is a required parameter.
        - **disk_enc_keyvault**: The resource ID of the key vault containing the disk encryption key, which is a
          Key Vault Secret. This is a required parameter.
        - **disk_enc_volume_type**: The volume type(s) that will be encrypted. Possible values include: 'OS',
          'Data', and 'All'. This is a required parameter.
        - **disk_enc_kek_url**: The Key Identifier URL for a Key Encryption Key (KEK). The KEK is used as an
          additional layer of security for encryption keys. Azure Disk Encryption will use the KEK to wrap the
          encryption secrets before writing to the Key Vault. The KEK must be in the same vault as the encryption
          secrets. This is an optional parameter.

    Attaching Data Disks:
        Data disks can be attached by passing a list of dictionaries in the data_disks parameter. The dictionaries in
        the list can have the following parameters:

        - **lun**: (optional int) Specifies the logical unit number of the data disk. This value is used to identify
          data disks within the VM and therefore must be unique for each data disk attached to a VM. If not
          provided, we increment the lun designator based upon the index within the provided list of disks.
        - **name**: (optional str) The disk name. Defaults to "{vm_name}-datadisk{lun}"
        - **vhd**: (optional str or dict) Virtual hard disk to use. If a URI string is provided, it will be nested
          under a "uri" key in a dictionary as expected by the SDK.
        - **image**: (optional str or dict) The source user image virtual hard disk. The virtual hard disk will be
          copied before being attached to the virtual machine. If image is provided, the destination virtual hard
          drive must not exist. If a URI string is provided, it will be nested under a "uri" key in a dictionary as
          expected by the SDK.
        - **caching**: (optional str - read_only, read_write, or none) Specifies the caching requirements. Defaults to
          "None" for Standard storage and "ReadOnly" for Premium storage.
        - **write_accelerator_enabled**: (optional bool - True or False) Specifies whether write accelerator should be
          enabled or disabled on the disk.
        - **create_option**: (optional str - attach, from_image, or empty) Specifies how the virtual machine should be
          created. The "attach" value is used when you are using a specialized disk to create the virtual machine. The
          "from_image" value is used when you are using an image to create the virtual machine. If you are using a
          platform image, you also use the image_reference element. If you are using a marketplace image, you also use
          the plan element.
        - **disk_size_gb**: (optional int) Specifies the size of an empty data disk in gigabytes. This element can be
          used to overwrite the size of the disk in a virtual machine image.
        - **managed_disk**: (optional str or dict) The managed disk parameters. If an ID string is provided, it will
          be nested under an "id" key in a dictionary as expected by the SDK. If a dictionary is provided, the
          "storage_account_type" parameter can be passed (accepts (Standard|Premium)_LRS or (Standard|Ultra)SSD_LRS).

    Example usage:

    .. code-block:: yaml

        Ensure virtual machine exists:
            azurerm.compute.virtual_machine.present:
                - name: idem-vm01
                - resource_group: idem
                - vm_size: Standard_B1s
                - virtual_network: vnet1
                - subnet: default
                - allocate_public_ip: True
                - ssh_public_keys:
                    - /home/myuser/.ssh/id_rsa.pub
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

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in vm:
        action = "update"

        tag_changes = differ.deep_diff(vm.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if vm_size.lower() != vm["hardware_profile"]["vm_size"].lower():
            ret["changes"]["vm_size"] = {
                "old": vm["hardware_profile"]["vm_size"].lower(),
                "new": vm_size.lower(),
            }

        if boot_diags_enabled is not None:
            if boot_diags_enabled != vm.get("diagnostics_profile", {}).get(
                "boot_diagnostics", {}
            ).get("enabled", False):
                ret["changes"]["boot_diags_enabled"] = {
                    "old": vm.get("diagnostics_profile", {})
                    .get("boot_diagnostics", {})
                    .get("enabled", False),
                    "new": boot_diags_enabled,
                }

        if diag_storage_uri:
            if diag_storage_uri != vm.get("diagnostics_profile", {}).get(
                "boot_diagnostics", {}
            ).get("storage_uri"):
                ret["changes"]["diag_storage_uri"] = {
                    "old": vm.get("diagnostics_profile", {})
                    .get("boot_diagnostics", {})
                    .get("storage_uri"),
                    "new": diag_storage_uri,
                }

        if max_price:
            if max_price != vm.get("billing_profile", {}).get("max_price"):
                ret["changes"]["max_price"] = {
                    "old": vm.get("billing_profile", {}).get("max_price"),
                    "new": max_price,
                }

        if allow_extensions is not None:
            if allow_extensions != vm.get("os_profile", {}).get(
                "allow_extension_operations", True
            ):
                ret["changes"]["allow_extensions"] = {
                    "old": vm.get("os_profile", {}).get(
                        "allow_extension_operations", True
                    ),
                    "new": allow_extensions,
                }

        if os_write_accel is not None:
            if os_write_accel != vm.get("storage_profile", {}).get("os_disk", {}).get(
                "write_accelerator_enabled"
            ):
                ret["changes"]["os_write_accel"] = {
                    "old": vm.get("storage_profile", {})
                    .get("os_disk", {})
                    .get("write_accelerator_enabled"),
                    "new": os_write_accel,
                }

        if os_disk_caching is not None:
            if os_disk_caching != vm.get("storage_profile", {}).get("os_disk", {}).get(
                "caching"
            ):
                ret["changes"]["os_disk_caching"] = {
                    "old": vm.get("storage_profile", {})
                    .get("os_disk", {})
                    .get("caching"),
                    "new": os_disk_caching,
                }

        if ultra_ssd_enabled is not None:
            if ultra_ssd_enabled != vm.get("additional_capabilities", {}).get(
                "ultra_ssd_enabled"
            ):
                ret["changes"]["ultra_ssd_enabled"] = {
                    "old": vm.get("additional_capabilities", {}).get(
                        "ultra_ssd_enabled"
                    ),
                    "new": ultra_ssd_enabled,
                }

        if provision_vm_agent is not None:
            if vm.get("os_profile", {}).get("linux_configuration", {}):
                if provision_vm_agent != vm["os_profile"]["linux_configuration"].get(
                    "provision_vm_agent", True
                ):
                    ret["changes"]["provision_vm_agent"] = {
                        "old": vm["os_profile"]["linux_configuration"].get(
                            "provision_vm_agent", True
                        ),
                        "new": provision_vm_agent,
                    }
            if vm.get("os_profile", {}).get("windows_configuration", {}):
                if provision_vm_agent != vm["os_profile"]["windows_configuration"].get(
                    "provision_vm_agent", True
                ):
                    ret["changes"]["provision_vm_agent"] = {
                        "old": vm["os_profile"]["windows_configuration"].get(
                            "provision_vm_agent", True
                        ),
                        "new": provision_vm_agent,
                    }

        if time_zone:
            if time_zone != vm.get("os_profile", {}).get(
                "windows_configuration", {}
            ).get("time_zone", True):
                ret["changes"]["time_zone"] = {
                    "old": vm.get("os_profile", {})
                    .get("windows_configuration", {})
                    .get("time_zone", True),
                    "new": time_zone,
                }

        if enable_automatic_updates is not None:
            if enable_automatic_updates != vm.get("os_profile", {}).get(
                "windows_configuration", {}
            ).get("enable_automatic_updates", True):
                ret["changes"]["enable_automatic_updates"] = {
                    "old": vm.get("os_profile", {})
                    .get("windows_configuration", {})
                    .get("enable_automatic_updates", True),
                    "new": enable_automatic_updates,
                }

        if data_disks is not None:
            existing_disks = vm.get("storage_profile", {}).get("data_disks", [])

            if len(existing_disks) != len(data_disks):
                ret["changes"]["data_disks"] = {
                    "old": existing_disks,
                    "new": data_disks,
                }
            else:
                for idx, disk in enumerate(data_disks):
                    for key in disk:
                        if isinstance(disk[key], dict) and isinstance(
                            existing_disks[idx].get(key), dict
                        ):
                            for k in disk[key]:
                                if disk[key][k] != existing_disks[idx][key].get(k):
                                    ret["changes"]["data_disks"] = {
                                        "old": existing_disks,
                                        "new": data_disks,
                                    }
                        else:
                            if disk[key] != existing_disks[idx].get(key):
                                ret["changes"]["data_disks"] = {
                                    "old": existing_disks,
                                    "new": data_disks,
                                }

        if enable_disk_enc:
            extensions = vm.get("resources", [])
            disk_enc_exists = False
            for extension in extensions:
                if (
                    extension.get("virtual_machine_extension_type")
                    == "AzureDiskEncryptionForLinux"
                    or extension.get("virtual_machine_extension_type")
                    == "AzureDiskEncryption"
                ):
                    disk_enc_exists = True
                    break

            if not disk_enc_exists:
                ret["changes"]["enable_disk_enc"] = {"old": False, "new": True}
                if disk_enc_keyvault:
                    ret["changes"]["disk_enc_keyvault"] = {"new": disk_enc_keyvault}
                if disk_enc_volume_type:
                    ret["changes"]["disk_enc_volume_type"] = {
                        "new": disk_enc_volume_type
                    }
                if disk_enc_kek_url:
                    ret["changes"]["disk_enc_kek_url"] = {"new": disk_enc_kek_url}

        if admin_password and force_admin_password:
            ret["changes"]["admin_password"] = {"new": "REDACTED"}
        elif ret["changes"]:
            ret["changes"]["admin_password"] = {"new": "REDACTED"}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Virtual machine {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Virtual machine {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["result"] = None
        ret["comment"] = "Virtual machine {0} would be created.".format(name)
        return ret

    vm_kwargs = kwargs.copy()
    vm_kwargs.update(connection_auth)

    vm = await hub.exec.azurerm.compute.virtual_machine.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        vm_size=vm_size,
        admin_username=admin_username,
        os_disk_create_option=os_disk_create_option,
        os_disk_size_gb=os_disk_size_gb,
        ssh_public_keys=ssh_public_keys,
        disable_password_auth=disable_password_auth,
        custom_data=custom_data,
        allow_extensions=allow_extensions,
        enable_automatic_updates=enable_automatic_updates,
        time_zone=time_zone,
        allocate_public_ip=allocate_public_ip,
        create_interfaces=create_interfaces,
        network_resource_group=network_resource_group,
        virtual_network=virtual_network,
        subnet=subnet,
        network_interfaces=network_interfaces,
        os_managed_disk=os_managed_disk,
        os_disk_vhd_uri=os_disk_vhd_uri,
        os_disk_image_uri=os_disk_image_uri,
        os_type=os_type,
        os_disk_name=os_disk_name,
        os_disk_caching=os_disk_caching,
        os_write_accel=os_write_accel,
        os_ephemeral_disk=os_ephemeral_disk,
        ultra_ssd_enabled=ultra_ssd_enabled,
        image=image,
        boot_diags_enabled=boot_diags_enabled,
        diag_storage_uri=diag_storage_uri,
        admin_password=admin_password,
        max_price=max_price,
        provision_vm_agent=provision_vm_agent,
        userdata_file=userdata_file,
        userdata=userdata,
        enable_disk_enc=enable_disk_enc,
        disk_enc_keyvault=disk_enc_keyvault,
        disk_enc_volume_type=disk_enc_volume_type,
        disk_enc_kek_url=disk_enc_kek_url,
        data_disks=data_disks,
        availability_set=availability_set,
        virtual_machine_scale_set=virtual_machine_scale_set,
        proximity_placement_group=proximity_placement_group,
        host=host,
        host_group=host_group,
        extensions_time_budget=extensions_time_budget,
        tags=tags,
        **vm_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": vm}

    if "error" not in vm:
        ret["result"] = True
        ret["comment"] = f"Virtual machine {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} virtual machine {1}! ({2})".format(
        action, name, vm.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub,
    ctx,
    name,
    resource_group,
    cleanup_osdisks=False,
    cleanup_datadisks=False,
    cleanup_interfaces=False,
    cleanup_public_ips=False,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.0.0

    Ensure a virtual machine does not exist in a resource group.

    :param name:
        Name of the virtual machine.

    :param resource_group:
        Name of the resource group containing the virtual machine.

    :param cleanup_osdisks:
        Enable deletion of the operating system disk attached to the virtual machine.

    :param cleanup_datadisks:
        Enable deletion of ALL of the data disks attached to the virtual machine.

    :param cleanup_interfaces:
        Enable deletion of ALL of the network interfaces attached to the virtual machine.

    :param cleanup_public_ips:
        Enable deletion of ALL of the public IP addresses directly attached to the virtual machine.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual machine absent:
            azurerm.compute.virtual_machine.absent:
                - name: test_machine
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

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in vm:
        ret["result"] = True
        ret["comment"] = "Virtual machine {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Virtual machine {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": vm,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.compute.virtual_machine.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        if cleanup_osdisks:
            vm["cleanup_osdisks"] = True
            os_disk = vm["storage_profile"]["os_disk"]
            if os_disk.get("managed_disk", {}).get("id"):
                disk_link = os_disk["managed_disk"]["id"]
                try:
                    disk_dict = parse_resource_id(disk_link)
                    disk_name = disk_dict["name"]
                    disk_group = disk_dict["resource_group"]
                except KeyError as exc:
                    log.error("This isn't a valid disk resource: %s", os_disk)

                deleted_disk = await hub.exec.azurerm.compute.disk.delete(
                    ctx,
                    disk_name,
                    disk_group,
                    azurerm_log_level="info",
                    **connection_auth,
                )

                if not deleted_disk:
                    log.error("Unable to delete disk: %s", disk_link)

        if cleanup_datadisks:
            vm["cleanup_datadisks"] = True
            for disk in vm["storage_profile"].get("data_disks", []):
                if disk.get("managed_disk", {}).get("id"):
                    disk_link = disk["managed_disk"]["id"]
                    try:
                        disk_dict = parse_resource_id(disk_link)
                        disk_name = disk_dict["name"]
                        disk_group = disk_dict["resource_group"]
                    except KeyError as exc:
                        log.error("This isn't a valid disk resource: %s", os_disk)
                        continue

                    deleted_disk = await hub.exec.azurerm.compute.disk.delete(
                        ctx,
                        disk_name,
                        disk_group,
                        azurerm_log_level="info",
                        **connection_auth,
                    )

                    if not deleted_disk:
                        log.error("Unable to delete disk: %s", disk_link)

        if cleanup_interfaces:
            vm["cleanup_interfaces"] = True
            for nic_link in vm.get("network_profile", {}).get("network_interfaces", []):
                try:
                    nic_dict = parse_resource_id(nic_link["id"])
                    nic_name = nic_dict["name"]
                    nic_group = nic_dict["resource_group"]
                except KeyError as exc:
                    log.error(
                        "This isn't a valid network interface subresource: %s", nic_link
                    )
                    continue

                nic = await hub.exec.azurerm.network.network_interface.get(
                    ctx,
                    nic_name,
                    nic_group,
                    azurerm_log_level="info",
                    **connection_auth,
                )

                deleted_nic = await hub.exec.azurerm.network.network_interface.delete(
                    ctx,
                    nic_name,
                    nic_group,
                    azurerm_log_level="info",
                    **connection_auth,
                )

                if cleanup_public_ips:
                    vm["cleanup_public_ips"] = True
                    for ipc in nic.get("ip_configurations", []):
                        if "public_ip_address" not in ipc:
                            continue

                        try:
                            pip_dict = parse_resource_id(ipc["public_ip_address"]["id"])
                            pip_name = pip_dict["name"]
                            pip_group = pip_dict["resource_group"]
                        except KeyError as exc:
                            log.error(
                                "This isn't a valid public IP subresource: %s",
                                ipc.get("public_ip_address"),
                            )
                            continue

                        deleted_pip = await hub.exec.azurerm.network.public_ip_address.delete(
                            ctx,
                            pip_name,
                            pip_group,
                            azurerm_log_level="info",
                            **connection_auth,
                        )

        ret["result"] = True
        ret["comment"] = "Virtual machine {0} has been deleted.".format(name)
        ret["changes"] = {"old": vm, "new": {}}
        return ret

    ret["comment"] = "Failed to delete virtual machine {0}!".format(name)
    return ret
