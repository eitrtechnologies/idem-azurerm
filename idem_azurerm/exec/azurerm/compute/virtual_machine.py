# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Virtual Machine Execution Module

.. versionadded:: 1.0.0

.. versionchanged:: 2.0.0, 4.0.0

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

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
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
    os_disk_simplename=None,
    data_disk_simplenames=None,
    os_disk_caching=None,
    os_write_accel=None,
    os_ephemeral_disk=None,
    ultra_ssd_enabled=None,
    image=None,
    boot_diags_enabled=None,
    diag_storage_uri=None,
    admin_password=None,
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
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 2.0.0, 4.0.0

    Create or update a virtual machine.

    :param name: The virtual machine to create.

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

    :param enable_automatic_updates: (only on Windows) Indicates whether Automatic Updates is enabled for the Windows
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

    :param os_disk_name: The OS disk name. Note that setting this may cause conflicts upon re-deployment of a virtual
        machine if the old OS disk isn't cleaned up. Use `os_disk_create_option="attach"` to attach a named disk.

    :param os_disk_simplename: If set to `True`, a "simple" name is used for the OS disk name instead of the randomized
        name used by default in Azure. Note that setting this may cause conflicts upon re-deployment of a virtual
        machine if the old OS disk isn't cleaned up. Use `os_disk_create_option="attach"` to attach a named disk.

    :param data_disk_simplenames: If set to `True`, a "simple" name is used for data disk names instead of the
        randomized names used by default in Azure. Note that setting this may cause conflicts upon re-deployment of a
        virtual machine if the old disk isn't cleaned up. Use `create_option="attach"` to attach a named disk.

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

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.create_or_update test_vm test_group

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
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    params = kwargs.copy()

    # This section creates dictionaries if required in order to properly create SubResource objects
    if os_managed_disk and not isinstance(os_managed_disk, dict):
        os_managed_disk = {"id": os_managed_disk}

    if os_disk_image_uri and not isinstance(os_disk_image_uri, dict):
        os_disk_image_uri = {"uri": os_disk_image_uri}

    if os_disk_vhd_uri and not isinstance(os_disk_vhd_uri, dict):
        os_disk_vhd_uri = {"uri": os_disk_vhd_uri}

    if not network_interfaces:
        network_interfaces = []

    # network interface creation
    if not network_interfaces and create_interfaces:
        ipc = {"name": f"{name}-nic0-cfg0"}

        if allocate_public_ip:
            pubip = await hub.exec.azurerm.network.public_ip_address.create_or_update(
                ctx, f"{name}-pip0", resource_group, **kwargs
            )

            try:
                ipc.update({"public_ip_address": {"id": pubip["id"]}})
            except KeyError as exc:
                result = {
                    "error": "The public IP address could not be created. ({0})".format(
                        str(exc)
                    )
                }
                return result

        iface = await hub.exec.azurerm.network.network_interface.create_or_update(
            ctx,
            f"{name}-nic0",
            [ipc],
            subnet,
            virtual_network,
            network_resource_group or resource_group,
            **kwargs,
        )

        try:
            nic = {"id": iface["id"]}
        except KeyError as exc:
            result = {
                "error": "The network interface could not be created. ({0})".format(
                    str(exc)
                )
            }
            return result

        network_interfaces.append(nic)

    # default os disk name
    if not os_disk_name and os_disk_simplename:
        os_disk_name = f"{name}-osdisk0"

    # data disks
    if not data_disks:
        data_disks = []

    for lun, data_disk in enumerate(data_disks):
        if not isinstance(data_disk, dict):
            log.warning(
                "The data disk at index %s is not a dictionary: %s", lun, data_disk
            )
            # drop from the list instead of halting. disks can always be attached after the fact.
            data_disks.pop(lun)
            continue
        # restrict allowable keys
        allowable = (
            "lun",
            "name",
            "vhd",
            "image",
            "caching",
            "write_accerator_enabled",
            "create_option",
            "disk_size_gb",
            "managed_disk",
            "to_be_detached",
        )
        data_disk = dict(
            [[key, val] for key, val in data_disk.items() if key in allowable]
        )

        # set defaults
        data_disk.setdefault("lun", lun)
        if data_disk_simplenames:
            data_disk.setdefault("name", f"{name}-datadisk{lun}")

        # attach a vhd
        if data_disk.get("vhd"):
            if not isinstance(data_disk["vhd"], dict):
                data_disk["vhd"] = {"uri": data_disk["vhd"]}
            data_disk.setdefault("create_option", "attach")

        # attach a managed disk
        if data_disk.get("managed_disk"):
            if not isinstance(data_disk["managed_disk"], dict):
                data_disk["managed_disk"] = {"id": data_disk["managed_disk"]}

        # from an image
        if data_disk.get("image"):
            if not isinstance(data_disk["image"], dict):
                data_disk["image"] = {"uri": data_disk["image"]}
            data_disk.setdefault("create_option", "from_image")

        # empty data disk if not otherwise set above
        data_disk.setdefault("create_option", "empty")
        if data_disk["create_option"] == "empty":
            data_disk.setdefault("disk_size_gb", 10)

        log.debug("Data disk with lun %s = %s", lun, data_disk)
        data_disks[lun] = data_disk

    # main configuration parameters
    params.update(
        {
            # "plan": {
            #    "name" None,
            #    "publisher": None,
            #    "product": None,
            #    "promotion_code": None
            # },
            "hardware_profile": {"vm_size": vm_size.lower(),},
            "storage_profile": {
                "os_disk": {
                    "os_type": os_type,
                    "name": os_disk_name,
                    "vhd": os_disk_vhd_uri,
                    "image": os_disk_image_uri,
                    "caching": os_disk_caching,
                    "write_accelerator_enabled": os_write_accel,
                    "create_option": os_disk_create_option,
                    "disk_size_gb": os_disk_size_gb,
                    "managed_disk": os_managed_disk,
                },
                "data_disks": data_disks,
            },
            "os_profile": {
                "computer_name": name,
                "admin_username": admin_username,
                "admin_password": admin_password,
                "custom_data": custom_data,
                #    "secrets": None,
                "allow_extension_operations": allow_extensions,
            },
            "network_profile": {"network_interfaces": network_interfaces,},
            "diagnostics_profile": {
                "boot_diagnostics": {
                    "enabled": boot_diags_enabled,
                    "storage_uri": diag_storage_uri,
                }
            },
            "extensions_time_budget": extensions_time_budget,
            # "identity": {
            #    "type": None, # SystemAssigned or UserAssigned
            #    "user_assigned_identities": None # VirtualMachineIdentityUserAssignedIdentitiesValue
            # },
        }
    )

    if isinstance(ssh_public_keys, list):
        pubkeys = []
        for pubkey in ssh_public_keys:
            if os.path.isfile(pubkey):
                try:
                    with open(pubkey, "r") as pubkey_file:
                        pubkeys.append(
                            {
                                "key_data": pubkey_file.read(),
                                "path": f"/home/{admin_username}/.ssh/authorized_keys",
                            }
                        )
                except FileNotFoundError as exc:
                    log.error(
                        "Unable to open ssh public key file: %s (%s)", pubkey, exc
                    )
            else:
                pubkeys.append(
                    {
                        "key_data": pubkey,
                        "path": f"/home/{admin_username}/.ssh/authorized_keys",
                    }
                )

        params["os_profile"].update(
            {
                "linux_configuration": {
                    "disable_password_authentication": disable_password_auth,
                    "ssh": {"public_keys": pubkeys},
                }
            }
        )

    if availability_set and virtual_machine_scale_set:
        log.error(
            "The availability_set and virtual_machine_scale_set parameters have both been specified. "
            "Only one of those two parameters may be specified during creation. "
            "Both parameters will now be ignored during execution."
        )
        availability_set = None
        virtual_machine_scale_set = None

    if availability_set:
        if is_valid_resource_id(availability_set):
            params["availability_set"] = {"id": availability_set}
        else:
            log.error(
                "The resource ID passed within the availability_set parameter is invalid and will be ignored."
            )
    elif virtual_machine_scale_set:
        if is_valid_resource_id(virtual_machine_scale_set):
            params["virtual_machine_scale_set"] = {"id": virtual_machine_scale_set}
        else:
            log.error(
                "The resource ID passed within the virtual_machine_scale_set parameter is invalid and will be ignored."
            )

    if host and host_group:
        log.error(
            "The host and host_group parameters have both been specified. "
            "Only one of those two parameters may be specified. "
            "Both parameters will now be ignored during execution."
        )
        host = None
        host_group = None

    if host:
        if is_valid_resource_id(host):
            params["host"] = {"id": host}
        else:
            log.error(
                "The resource ID passed within the host parameter is invalid and will be ignored."
            )
    elif host_group:
        if is_valid_resource_id(host_group):
            params["host_group"] = {"id": host_group}
        else:
            log.error(
                "The resource ID passed within the host_group parameter is invalid and will be ignored."
            )

    if proximity_placement_group:
        if is_valid_resource_id(proximity_placement_group):
            params["proximity_placement_group"] = {"id": proximity_placement_group}
        else:
            log.error(
                "The resource ID passed within the proximity_placement_group parameter is invalid and will be ignored."
            )

    if image:
        if is_valid_resource_id(image):
            params["storage_profile"].update({"image_reference": {"id": image}})
        elif "|" in image:
            image_keys = ["publisher", "offer", "sku", "version"]
            params["storage_profile"].update(
                {"image_reference": dict(zip(image_keys, image.split("|")))}
            )

    if time_zone or enable_automatic_updates is not None:
        if "windows_configuration" not in params["os_profile"]:
            params["os_profile"]["windows_configuration"] = {}
        if enable_automatic_updates:
            params["os_profile"]["windows_configuration"][
                "enable_automatic_updates"
            ] = enable_automatic_updates
        if time_zone:
            params["os_profile"]["windows_configuration"]["time_zone"] = time_zone

    if not provision_vm_agent:
        if "linux_configuration" in params["os_profile"]:
            params["os_profile"]["linux_configuration"][
                "provision_vm_agent"
            ] = provision_vm_agent
        elif "windows_configuration" in params["os_profile"]:
            params["os_profile"]["windows_configuration"][
                "provision_vm_agent"
            ] = provision_vm_agent
        elif os_type:
            if "linux" in os_type.lower():
                params["os_profile"]["linux_configuration"] = {
                    "provision_vm_agent": provision_vm_agent
                }
            elif "windows" in os_type.lower():
                params["os_profile"]["windows_configuration"] = {
                    "provision_vm_agent": provision_vm_agent
                }

    if os_ephemeral_disk:
        params["storage_profile"]["diff_disk_settings"] = {"option": "local"}

    if max_price:
        params["billing_profile"] = {"max_price": max_price}

    if ultra_ssd_enabled is not None:
        params["additional_capabilities"] = {"ultra_ssd_enabled": ultra_ssd_enabled}

    try:
        vmmodel = await hub.exec.azurerm.utils.create_object_model(
            "compute", "VirtualMachine", **params
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        vm = compconn.virtual_machines.create_or_update(
            resource_group_name=resource_group, vm_name=name, parameters=vmmodel
        )

        vm.wait()
        result = vm.result().as_dict()

        # Extract connection auth values for virtual machine extensions
        auth_kwargs = (
            "tenant",
            "client_id",
            "secret",
            "subscription_id",
            "username",
            "password",
        )
        connection_profile = dict([[x, kwargs[x]] for x in auth_kwargs if x in kwargs])
        is_linux = (
            True
            if result["storage_profile"]["os_disk"]["os_type"] == "Linux"
            else False
        )
        extension_info = {}

        # attach custom script extension for userdata
        if (userdata or userdata_file) and provision_vm_agent:
            if is_linux:
                extension_info["publisher"] = "Microsoft.Azure.Extensions"
                extension_info["version"] = "2.0"
                extension_info["type"] = "CustomScript"
            else:
                extension_info["publisher"] = "Microsoft.Compute"
                extension_info["version"] = "1.8"
                extension_info["type"] = "CustomScriptExtension"

            extension_info["settings"] = {}
            if userdata_file:
                if userdata_file.startswith("http"):
                    extension_info["settings"]["fileUris"] = [userdata_file]
                elif os.path.isfile(userdata_file):
                    try:
                        with open(userdata_file, "r") as udf_:
                            userdata = udf_.read()
                    except FileNotFoundError as exc:
                        log.error(
                            "Unable to open userdata file: %s (%s)", userdata, exc
                        )
            extension_info["settings"]["commandToExecute"] = userdata

            if userdata:
                userdata_ret = await hub.exec.azurerm.compute.virtual_machine_extension.create_or_update(
                    ctx=ctx,
                    name=f"{name}_custom_userdata_script",
                    vm_name=name,
                    resource_group=resource_group,
                    location=result["location"],
                    publisher=extension_info["publisher"],
                    extension_type=extension_info["type"],
                    version=extension_info["version"],
                    settings=extension_info["settings"],
                    **connection_profile,
                )
                log.debug("Return from userdata extension: %s", userdata_ret)

        # attach disk encryption extension
        if (
            enable_disk_enc
            and provision_vm_agent
            and disk_enc_keyvault
            and disk_enc_volume_type
        ):
            try:
                disk_enc_keyvault_name = (parse_resource_id(disk_enc_keyvault))["name"]
                disk_enc_keyvault_url = "https://{0}.vault.azure.net/".format(
                    disk_enc_keyvault_name
                )

                extension_info = {
                    "publisher": "Microsoft.Azure.Security",
                    "settings": {
                        "VolumeType": disk_enc_volume_type,
                        "EncryptionOperation": "EnableEncryption",
                        "KeyVaultResourceId": disk_enc_keyvault,
                        "KeyVaultURL": disk_enc_keyvault_url,
                    },
                }

                if is_linux:
                    extension_info["type"] = "AzureDiskEncryptionForLinux"
                    extension_info["version"] = "1.1"
                else:
                    extension_info["type"] = "AzureDiskEncryption"
                    extension_info["version"] = "2.2"

                if disk_enc_kek_url:
                    extension_info["settings"]["KeyEncryptionKeyURL"] = disk_enc_kek_url
                    extension_info["settings"]["KekVaultResourceId"] = disk_enc_keyvault

                encryption_info = await hub.exec.azurerm.compute.virtual_machine_extension.create_or_update(
                    ctx=ctx,
                    name="DiskEncryption",
                    vm_name=name,
                    resource_group=resource_group,
                    location=result["location"],
                    publisher=extension_info["publisher"],
                    extension_type=extension_info["type"],
                    version=extension_info["version"],
                    settings=extension_info["settings"],
                    **connection_profile,
                )

                result["storage_profile"]["disk_encryption"] = True
            except KeyError as exc:
                log.error(
                    "An error occured while trying to enable disk encryption: {0}".format(
                        str(exc)
                    )
                )
                result["storage_profile"]["disk_encryption"] = False

        # Give some more details about the sub-objects
        network_interfaces = []

        for iface in result["network_profile"]["network_interfaces"]:
            iface_dict = parse_resource_id(iface["id"])

            iface_details = await hub.exec.azurerm.network.network_interface.get(
                ctx=ctx,
                resource_group=iface_dict["resource_group"],
                name=iface_dict["name"],
                **kwargs,
            )

            network_interfaces.append(iface_details)

        result["network_profile"]["network_interfaces"] = network_interfaces
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(
    hub,
    ctx,
    name,
    resource_group,
    cleanup_disks=False,
    cleanup_data_disks=False,
    cleanup_interfaces=False,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Delete a virtual machine.

    :param name: The virtual machine to delete.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.delete testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        ctx=ctx, resource_group=resource_group, name=name, **kwargs
    )

    try:
        poller = compconn.virtual_machines.delete(
            resource_group_name=resource_group, vm_name=name
        )

        poller.wait()

        if cleanup_disks:
            os_disk = parse_resource_id(
                vm["storage_profile"]["os_disk"].get("managed_disk", {}).get("id")
            )

            os_disk_ret = await hub.exec.azurerm.compute.disk.delete(
                ctx=ctx,
                resource_group=os_disk["resource_group"],
                name=os_disk["name"],
                **kwargs,
            )

        if cleanup_data_disks:
            for disk in vm["storage_profile"]["data_disks"]:
                disk_dict = parse_resource_id(disk.get("managed_disk", {}).get("id"))

                data_disk_ret = await hub.exec.azurerm.compute.disk.delete(
                    ctx=ctx,
                    resource_group=disk_dict["resource_group"],
                    name=disk_dict["name"],
                    **kwargs,
                )

        if cleanup_interfaces:
            for iface in vm["network_profile"]["network_interfaces"]:
                iface_dict = parse_resource_id(iface["id"])

                iface_details = await hub.exec.azurerm.network.network_interface.get(
                    ctx=ctx,
                    resource_group=iface_dict["resource_group"],
                    name=iface_dict["name"],
                    **kwargs,
                )

                iface_ret = await hub.exec.azurerm.network.network_interface.delete(
                    ctx=ctx,
                    resource_group=iface_dict["resource_group"],
                    name=iface_dict["name"],
                    **kwargs,
                )

                for ipc in iface_details["ip_configurations"]:
                    if ipc.get("public_ip_address"):
                        ip_dict = parse_resource_id(ipc["public_ip_address"]["id"])

                        ip_ret = await hub.exec.azurerm.network.public_ip_address.delete(
                            ctx=ctx,
                            resource_group=ip_dict["resource_group"],
                            name=ip_dict["name"],
                            **kwargs,
                        )

        result = True

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)

    return result


async def capture(
    hub,
    ctx,
    name,
    destination_name,
    resource_group,
    prefix="capture-",
    overwrite=False,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Captures the VM by copying virtual hard disks of the VM and outputs a template that can be used to create
    similar VMs.

    :param name: The name of the virtual machine.

    :param destination_name: The destination container name.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param prefix: (Default: 'capture-') The captured virtual hard disk's name prefix.

    :param overwrite: (Default: False) Overwrite the destination disk in case of conflict.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.capture testvm testcontainer testgroup

    """
    # pylint: disable=invalid-name
    VirtualMachineCaptureParameters = getattr(
        azure.mgmt.compute.models, "VirtualMachineCaptureParameters"
    )

    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.capture(
            resource_group_name=resource_group,
            vm_name=name,
            parameters=VirtualMachineCaptureParameters(
                vhd_prefix=prefix,
                destination_container_name=destination_name,
                overwrite_vhds=overwrite,
            ),
        )
        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Retrieves information about the model view or the instance view of a virtual machine.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.get testvm testgroup

    """
    expand = kwargs.get("expand")

    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.get(
            resource_group_name=resource_group, vm_name=name, expand=expand
        )
        result = vm.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def assess_patches(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Assess patches on the VM.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.assess_patches testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.assess_patches(
            resource_group_name=resource_group, vm_name=name
        )

        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def convert_to_managed_disks(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Converts virtual machine disks from blob-based to managed disks. Virtual machine must be stop-deallocated before
    invoking this operation.

    :param name: The name of the virtual machine to convert.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.convert_to_managed_disks testvm testgroup

    """
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.convert_to_managed_disks(
            resource_group_name=resource_group, vm_name=name
        )
        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def deallocate(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Power off a virtual machine and deallocate compute resources.

    :param name: The name of the virtual machine to deallocate.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.deallocate testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.deallocate(
            resource_group_name=resource_group, vm_name=name
        )
        vm.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def generalize(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Set the state of a virtual machine to 'generalized'.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.generalize testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        compconn.virtual_machines.generalize(
            resource_group_name=resource_group, vm_name=name
        )
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    List all virtual machines within a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            vms = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.virtual_machines.list(resource_group_name=resource_group)
            )
        else:
            vms = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.virtual_machines.list_all(**kwargs)
            )

        for vm in vms:  # pylint: disable=invalid-name
            result[vm["name"]] = vm
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_location(hub, ctx, location, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets all the virtual machines under the specified subscription for the specified location.

    :param location: The location for which virtual machines under the subscription are queried.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list "eastus"

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        vms = await hub.exec.azurerm.utils.paged_object_to_list(
            compconn.virtual_machines.list_by_location(location=location)
        )

        for vm in vms:  # pylint: disable=invalid-name
            result[vm["name"]] = vm
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_available_sizes(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all available virtual machine sizes to which the specified virtual machine can be resized.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.list_available_sizes testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        sizes = await hub.exec.azurerm.utils.paged_object_to_list(
            compconn.virtual_machines.list_available_sizes(
                resource_group_name=resource_group, vm_name=name
            )
        )
        for size in sizes:
            result[size["name"]] = size
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def instance_view(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Retrieves information about the run-time state of a virtual machine.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.instance_view testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.instance_view(
            resource_group_name=resource_group, vm_name=name
        )

        result = vm.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def perform_maintenance(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    The operation to perform maintenance on a virtual machine.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.perform_maintenance testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.perform_maintenance(
            resource_group_name=resource_group, vm_name=name
        )

        result = vm.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def power_off(hub, ctx, name, resource_group, skip_shutdown=False, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    The operation to power off (stop) a virtual machine. The virtual machine can be restarted with the same provisioned
    resources. You are still charged for this virtual machine.

    :param name: The name of the virtual machine to stop.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param skip_shutdown: A boolean value representing wheter to request non-graceful VM shutdown. True value for this
        flag indicates non-graceful shutdown whereas False indicates otherwise. Defaults to False.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.power_off testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.power_off(
            resource_group_name=resource_group,
            vm_name=name,
            skip_shutdown=skip_shutdown,
        )

        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def reapply(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    The operation to reapply a virtual machine's state.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.reapply testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.reapply(
            resource_group_name=resource_group, vm_name=name
        )
        vm.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def reimage(hub, ctx, name, resource_group, temp_disk=False, **kwargs):
    """
    .. versionadded:: 4.0.0

    Reimages the virtual machine which has an ephemeral OS disk back to its initial state.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param temp_disk: A boolean value specifying whether to reimage temp disk. This parameter is only supported for
        VM/VMSS with Ephemral OS disk. Defaults to False.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.reimage testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.reimage(
            resource_group_name=resource_group, vm_name=name, temp_disk=temp_disk
        )
        vm.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def restart(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Restart a virtual machine.

    :param name: The name of the virtual machine to restart.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.restart testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.restart(
            resource_group_name=resource_group, vm_name=name
        )

        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def start(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Power on (start) a virtual machine.

    :param name: The name of the virtual machine to start.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.start testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.start(
            resource_group_name=resource_group, vm_name=name
        )

        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def redeploy(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Redeploy a virtual machine.

    :param name: The name of the virtual machine to redeploy.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.redeploy testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)
    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.redeploy(
            resource_group_name=resource_group, vm_name=name
        )
        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def retrieve_boot_diagnostics_data(
    hub, ctx, name, resource_group, sas_uri_expiration_time=None, **kwargs
):
    """
    .. versionadded:: 4.0.0

    The operation to retrieve SAS URIs for a virtual machine's boot diagnostic logs.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    :param sas_uri_expiration_time: Expiration duration in minutes for the SAS URIs with a value between 1 to 1440
        minutes. NOTE: If not specified, SAS URIs will be generated with a default expiration duration of 120 minutes.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.retrieve_boot_diagnostics_data testvm testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.retrieve_boot_diagnostics_data(
            resource_group_name=resource_group,
            vm_name=name,
            sas_uri_expiration_time_in_minutes=sas_uri_expiration_time,
        )
        vm.wait()
        result = vm.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def simulate_eviction(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    The operation to simulate the eviction of spot virtual machine. The eviction will occur within 30 minutes of
    calling the API.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the virtual machine.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.virtual_machine.simulate_eviction testvm testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        # pylint: disable=invalid-name
        vm = compconn.virtual_machines.simulate_eviction(
            resource_group_name=resource_group, vm_name=name,
        )
        vm.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
