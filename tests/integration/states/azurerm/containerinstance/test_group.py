import pytest


@pytest.fixture(scope="module")
def containers():
    yield [
        {
            "name": "mycoolwebcontainer",
            "image": "nginx:latest",
            "resources": {"requests": {"memory_in_gb": 1.0, "cpu": 1.0,}},
        }
    ]


@pytest.mark.second
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, containers):
    aci = "aci-idemtest"
    expected = {
        "changes": {
            "new": {
                "name": aci,
                "containers": containers,
                "os_type": "Linux",
                "restart_policy": "OnFailure",
                "resource_group": resource_group,
                "tags": {"hihi": "cats"},
            },
            "old": {},
        },
        "comment": f"Container instance group {aci} has been created.",
        "name": aci,
        "result": True,
    }
    ret = await hub.states.azurerm.containerinstance.group.present(
        ctx,
        aci,
        resource_group,
        containers=containers,
        os_type="Linux",
        tags={"hihi": "cats"},
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, containers, tags):
    aci = "aci-idemtest"
    expected = {
        "changes": {"tags": {"new": tags, "old": {"hihi": "cats"}},},
        "comment": f"Container instance group {aci} has been updated.",
        "name": aci,
        "result": True,
    }
    ret = await hub.states.azurerm.containerinstance.group.present(
        ctx, aci, resource_group, containers=containers, os_type="Linux", tags=tags,
    )
    assert ret == expected


@pytest.mark.second_to_last
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, containers, tags):
    aci = "aci-idemtest"
    expected = {
        "changes": {
            "new": {},
            "old": {
                "location": location,
                "name": aci,
                "os_type": "Linux",
                "provisioning_state": "Succeeded",
                "restart_policy": "OnFailure",
                "sku": "Standard",
                "type": "Microsoft.ContainerInstance/containerGroups",
                "tags": tags,
                "containers": containers,
                "init_containers": [],
                "instance_view": {"events": [], "state": "Running"},
            },
        },
        "comment": f"Container instance group {aci} has been deleted.",
        "name": aci,
        "result": True,
    }
    ret = await hub.states.azurerm.containerinstance.group.absent(
        ctx, aci, resource_group
    )
    ret["changes"]["old"].pop("id")
    for cnt in ret["changes"]["old"].get("containers", []):
        cnt.pop("environment_variables")
        cnt.pop("instance_view")
        cnt.pop("ports")
    assert ret == expected
