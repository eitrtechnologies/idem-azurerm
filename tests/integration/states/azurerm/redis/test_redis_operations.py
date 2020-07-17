import pytest
import random
import string


@pytest.fixture(scope="module")
def redis_cache():
    yield "idem-redis-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="module")
def sku():
    yield {"name": "Basic", "family": "C", "capacity": 2}


@pytest.mark.skip(
    reason="Need to figure out what to do about Redis creation taking a long time"
)
@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, sku, redis_cache):
    expected = {
        "changes": {
            "new": {
                "name": redis_cache,
                "location": location,
                "resource_group": resource_group,
                "sku": sku,
            },
            "old": {},
        },
        "comment": f"Redis cache {redis_cache} has been created.",
        "name": redis_cache,
        "result": True,
    }
    ret = await hub.states.azurerm.redis.operations.present(
        ctx,
        name=redis_cache,
        resource_group=resource_group,
        location=location,
        sku=sku,
    )
    assert ret == expected


@pytest.mark.skip(
    reason="Need to figure out what to do about Redis creation taking a long time"
)
@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, sku, redis_cache):
    enable_non_ssl_port = True
    expected = {
        "changes": {"enable_non_ssl_port": {"new": True, "old": False},},
        "comment": f"Redis cache {redis_cache} has been updated.",
        "name": redis_cache,
        "result": True,
    }
    ret = await hub.states.azurerm.redis.operations.present(
        ctx,
        name=redis_cache,
        resource_group=resource_group,
        location=location,
        sku=sku,
        enable_non_ssl_port=enable_non_ssl_port,
    )
    assert ret == expected


@pytest.mark.skip(
    reason="Need to figure out what to do about Redis creation taking a long time"
)
@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, redis_cache):
    expected = {
        "changes": {"new": {}, "old": {"name": redis_cache,},},
        "comment": f"Redis cache {redis_cache} has been deleted.",
        "name": redis_cache,
        "result": True,
    }
    ret = await hub.states.azurerm.redis.operations.absent(
        ctx, redis_cache, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
