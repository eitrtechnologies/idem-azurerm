import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, acr):
    task = "idemtask"
    expected = {
        "changes": {
            "new": {
                "name": task,
                "location": "eastus",
                "platform": {"architecture": "amd64", "os": "Linux"},
                "provisioning_state": "Succeeded",
                "step": {
                    "context_path": "https://github.com/Azure-Samples/acr-build-helloworld-node",
                    "docker_file_path": "Dockerfile",
                    "image_names": [f"{acr}:helloworldnode"],
                    "is_push_enabled": True,
                    "no_cache": False,
                    "type": "Docker",
                },
                "timeout": 3600,
                "type": "Microsoft.ContainerRegistry/registries/tasks",
            },
            "old": {},
        },
        "comment": f"Container registry task {task} has been created.",
        "name": task,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.task.present(
        ctx,
        task,
        acr,
        resource_group,
        task_type="DockerBuildStep",
        platform_os="Linux",
        platform_arch="amd64",
        context_path="https://github.com/Azure-Samples/acr-build-helloworld-node",
        task_file_path="Dockerfile",
        image_names=[f"{acr}:helloworldnode"],
    )
    ret["changes"]["new"].pop("creation_date")
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, acr, tags):
    task = "idemtask"
    expected = {
        "changes": {
            "tags": {
                "new": tags,
            },
        },
        "comment": f"Container registry task {task} has been updated.",
        "name": task,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.task.present(
        ctx,
        task,
        acr,
        resource_group,
        task_type="DockerBuildStep",
        platform_os="Linux",
        platform_arch="amd64",
        context_path="https://github.com/Azure-Samples/acr-build-helloworld-node",
        task_file_path="Dockerfile",
        image_names=[f"{acr}:helloworldnode"],
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, acr, tags):
    task = "idemtask"
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": task,
                "platform": {"architecture": "amd64", "os": "Linux"},
                "location": location,
                "provisioning_state": "Succeeded",
                "step": {
                    "context_path": "https://github.com/Azure-Samples/acr-build-helloworld-node",
                    "docker_file_path": "Dockerfile",
                    "image_names": [f"{acr}:helloworldnode"],
                    "is_push_enabled": True,
                    "no_cache": False,
                    "type": "Docker",
                },
                "tags": tags,
                "timeout": 3600,
                "type": "Microsoft.ContainerRegistry/registries/tasks",
            },
        },
        "comment": f"Container registry task {task} has been deleted.",
        "name": task,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.task.absent(
        ctx, task, acr, resource_group
    )
    ret["changes"]["old"].pop("id")
    ret["changes"]["old"].pop("creation_date")
    assert ret == expected
