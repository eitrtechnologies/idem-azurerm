import pytest
import random
import string
import os
import tempfile
import pathlib
import zipfile


@pytest.fixture(scope="session")
def function_app():
    yield "func-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="session")
def app_service_plan():
    yield "plan-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="session")
def zip_file():
    """
    Create a temp zip file and returns the path of it.
    """
    filename = (
        "idem"
        + "".join(random.choice(string.ascii_lowercase) for _ in range(8))
        + ".zip"
    )

    with tempfile.TemporaryDirectory() as tempdir:
        path = pathlib.Path(tempdir)
        file_path = path.joinpath(filename)

        with zipfile.ZipFile(file_path, "w") as myzip:
            myzip.writestr("code.py", "def main():\n\treturn 0")
        yield file_path


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, function_app, app_service_plan, resource_group, storage_account, zip_file
):
    os_type = "linux"
    runtime_stack = "python"
    expected = {
        "changes": {
            "new": {
                "name": function_app,
                "resource_group": resource_group,
                "storage_account": storage_account,
                "app_service_plan": app_service_plan,
                "os_type": os_type,
                "runtime_stack": runtime_stack,
                "tags": None,
                "site_config": {},
            },
            "old": {},
        },
        "comment": f"Function App {function_app} has been created.",
        "name": function_app,
        "result": True,
    }

    ret = await hub.states.azurerm.web.function_app.present(
        ctx,
        name=function_app,
        resource_group=resource_group,
        storage_account=storage_account,
        app_service_plan=app_service_plan,
        runtime_stack=runtime_stack,
        os_type=os_type,
        functions_file_path=zip_file,
    )

    expected["changes"]["new"]["site_config"]["app_settings"] = ret["changes"]["new"][
        "site_config"
    ]["app_settings"]
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub,
    ctx,
    function_app,
    app_service_plan,
    resource_group,
    storage_account,
    zip_file,
    tags,
):
    os_type = "linux"
    runtime_stack = "python"

    expected = {
        "changes": {"tags": {"new": tags},},
        "comment": f"Function App {function_app} has been updated.",
        "name": function_app,
        "result": True,
    }

    ret = await hub.states.azurerm.web.function_app.present(
        ctx,
        name=function_app,
        resource_group=resource_group,
        storage_account=storage_account,
        app_service_plan=app_service_plan,
        runtime_stack=runtime_stack,
        os_type=os_type,
        functions_file_path=zip_file,
        tags=tags,
    )

    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, function_app, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": function_app},},
        "comment": f"Function App {function_app} has been deleted.",
        "name": function_app,
        "result": True,
    }

    ret = await hub.states.azurerm.web.function_app.absent(
        ctx, name=function_app, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
