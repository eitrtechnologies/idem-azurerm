import pytest
import random
import string


@pytest.fixture(scope="module")
def password():
    yield "#PASS" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    ) + "!"


"""
--------
      ID: Ensure virtual machine exists
Function: azurerm.compute.virtual_machine.present
  Result: True
 Comment: Virtual machine vm-test has been created.
 Changes: old:
    ----------
new:
    ----------
    id:
        /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/rg-tests/providers/Microsoft.Compute/virtualMachines/vm-test
    name:
        vm-test
    type:
        Microsoft.Compute/virtualMachines
    location:
        eastus
    hardware_profile:
        ----------
        vm_size:
            standard_b4ms
    storage_profile:
        ----------
        image_reference:
            ----------
            publisher:
                MicrosoftWindowsServer
            offer:
                WindowsServer
            sku:
                2019-Datacenter
            version:
                latest
        os_disk:
            ----------
            os_type:
                Windows
            name:
                vm-test_OsDisk_1_416ab7f0cfe44707a055aa932424d71b
            caching:
                ReadWrite
            create_option:
                FromImage
            disk_size_gb:
                128
            managed_disk:
                ----------
                id:
                    /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/RG-TESTS/providers/Microsoft.Compute/disks/vm-test_OsDisk_1_416ab7f0cfe44707a055aa932424d71b
                storage_account_type:
                    Premium_LRS
        data_disks:
    os_profile:
        ----------
        computer_name:
            vm-test
        admin_username:
            idem
        windows_configuration:
            ----------
            provision_vm_agent:
                True
            enable_automatic_updates:
                True
        secrets:
        allow_extension_operations:
            True
    network_profile:
        ----------
        network_interfaces:
            |_
              ----------
              id:
                  /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/rg-tests/providers/Microsoft.Network/networkInterfaces/vm-test-nic0
              name:
                  vm-test-nic0
              type:
                  Microsoft.Network/networkInterfaces
              location:
                  eastus
              virtual_machine:
                  ----------
                  id:
                      /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/rg-tests/providers/Microsoft.Compute/virtualMachines/vm-test
              ip_configurations:
                  |_
                    ----------
                    id:
                        /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/rg-tests/providers/Microsoft.Network/networkInterfaces/vm-test-nic0/ipConfigurations/vm-test-nic0-cfg0
                    private_ip_address:
                        172.18.0.4
                    private_ip_allocation_method:
                        Dynamic
                    private_ip_address_version:
                        IPv4
                    subnet:
                        ----------
                        id:
                            /subscriptions/4677297b-9565-4371-bf72-eafcc80b8155/resourceGroups/rg-tests/providers/Microsoft.Network/virtualNetworks/vnet-eitr/subnets/default
                    primary:
                        True
                    provisioning_state:
                        Succeeded
                    name:
                        vm-test-nic0-cfg0
                    etag:
                        W/"30faeed6-d902-4f38-9d1b-eb3942a1a082"
              tap_configurations:
              dns_settings:
                  ----------
                  dns_servers:
                  applied_dns_servers:
                  internal_domain_name_suffix:
                      3f35511kkjfeba2gybzq0r1q5b.bx.internal.cloudapp.net
              mac_address:
                  00-22-48-1D-72-7C
              primary:
                  True
              enable_accelerated_networking:
                  False
              enable_ip_forwarding:
                  False
              hosted_workloads:
              resource_guid:
                  ddd7bb73-2dbb-47c0-b3e7-fdc638b115cc
              provisioning_state:
                  Succeeded
              etag:
                  W/"30faeed6-d902-4f38-9d1b-eb3942a1a082"
    diagnostics_profile:
        ----------
        boot_diagnostics:
            ----------
            enabled:
                False
    provisioning_state:
        Succeeded
    vm_id:
        514e725e-ce6e-4d13-aea6-7e423d211f5f
"""


@pytest.fixture(scope="module")
def vm_size():
    yield "Standard_B4ms"


@pytest.fixture(scope="module")
def linux_image():
    yield "OpenLogic|CentOS|7.7|latest"


@pytest.fixture(scope="module")
def windows_image():
    yield "MicrosoftWindowsServer|WindowsServer|2019-Datacenter|latest"


@pytest.mark.run(order=5)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, vm, resource_group, vm_size, windows_image, vnet, subnet, password
):
    image_info = windows_image.split("|")
    expected = {
        "changes": {
            "new": {
                "name": vm,
                "hardware_profile": {"vm_size": vm_size.lower()},
                "storage_profile": {
                    "image_reference": {
                        "publisher": image_info[0],
                        "offer": image_info[1],
                        "sku": image_info[2],
                        "version": image_info[3],
                    },
                    "os_disk": {"disk_size_gb": 128},
                },
            },
            "old": {},
        },
        "comment": f"Virtual machine {vm} has been created.",
        "name": vm,
        "result": True,
    }

    ret = await hub.states.azurerm.compute.virtual_machine.present(
        ctx,
        name=vm,
        resource_group=resource_group,
        vm_size=vm_size,
        image=windows_image,
        os_disk_size_gb=128,
        virtual_network=vnet,
        subnet=subnet,
        admin_password=password,
    )
    assert ret["changes"]["new"]["name"] == expected["changes"]["new"]["name"]
    assert (
        ret["changes"]["new"]["hardware_profile"]
        == expected["changes"]["new"]["hardware_profile"]
    )
    assert (
        ret["changes"]["new"]["storage_profile"]["image_reference"]
        == expected["changes"]["new"]["storage_profile"]["image_reference"]
    )
    assert (
        ret["changes"]["new"]["storage_profile"]["os_disk"]["disk_size_gb"]
        == expected["changes"]["new"]["storage_profile"]["os_disk"]["disk_size_gb"]
    )


@pytest.mark.run(order=5, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, vm, resource_group, vm_size, windows_image, vnet, subnet, password, tags
):
    expected = {
        "changes": {"admin_password": {"new": "REDACTED"}, "tags": {"new": tags}},
        "comment": f"Virtual machine {vm} has been updated.",
        "name": vm,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.virtual_machine.present(
        ctx,
        name=vm,
        resource_group=resource_group,
        vm_size=vm_size,
        image=windows_image,
        os_disk_size_gb=128,
        virtual_network=vnet,
        subnet=subnet,
        admin_password=password,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-5)
@pytest.mark.asyncio
async def test_absent(hub, ctx, vm, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vm,},},
        "comment": f"Virtual machine {vm} has been deleted.",
        "name": vm,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.virtual_machine.absent(
        ctx,
        name=vm,
        resource_group=resource_group,
        cleanup_osdisks=True,
        cleanup_datadisks=True,
        cleanup_interfaces=True,
        cleanup_public_ips=True,
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
