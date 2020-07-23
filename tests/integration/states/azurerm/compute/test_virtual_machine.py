import pytest
import random
import string


@pytest.fixture(scope="module")
def password():
    yield "#PASS" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    ) + "!"


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
