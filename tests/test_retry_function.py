# tests/test_retry_function.py
import pytest
from retry_function import retry


def test_sync_retry_success_after_failure():
    counter = {"calls": 0}

    @retry(tries=3, delay=0.1)
    def flaky():
        counter["calls"] += 1
        if counter["calls"] < 2:
            raise ValueError("Fail once")
        return "success"

    result = flaky()
    assert result == "success"
    assert counter["calls"] == 2


def test_sync_retry_all_failures():
    @retry(tries=2, delay=0.1)
    def always_fail():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_fail()


@pytest.mark.asyncio
async def test_async_retry_success_after_failure():
    counter = {"calls": 0}

    @retry(tries=3, delay=0.1)
    async def async_flaky():
        counter["calls"] += 1
        if counter["calls"] < 2:
            raise RuntimeError("Fail once")
        return "ok"

    result = await async_flaky()
    assert result == "ok"
    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_async_retry_all_failures():
    @retry(tries=2, delay=0.1)
    async def always_fail():
        raise RuntimeError("Boom")

    with pytest.raises(RuntimeError, match="Boom"):
        await always_fail()
