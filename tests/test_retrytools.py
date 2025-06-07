import pytest
import logging
from retrytools import retry

# ------------------------
# Fixtures
# ------------------------

@pytest.fixture(scope="module")
def test_logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

# ------------------------
# Retry Succeeds After Initial Failure
# ------------------------
def test_1():
    counter = {"calls": 0}

    @retry(ValueError, tries=2, delay=0.01)
    def foo():
        counter["calls"] += 1
        if counter["calls"] < 2:
            raise ValueError("Bang")
        return "success"
    
    result = foo()

    assert result == "success"
    assert counter["calls"] == 2


async def test_2(test_logger):
    counter = {"calls": 0}

    @retry(ValueError, tries=2, delay=0.01, logger=test_logger)
    async def foo():
        counter["calls"] += 1
        if counter["calls"] < 2:
            raise ValueError("Bang")
        return "success"
    
    result = await foo()

    assert result == "success"
    assert counter["calls"] == 2

# ------------------------
# Retry Fails After Max Attempts
# ------------------------
def test_3(test_logger):
    counter = {"calls": 0}
    @retry(UnboundLocalError, tries=3, delay=0.01, logger=test_logger)
    def foo():
        counter["calls"] += 1
        raise UnboundLocalError("Boom")

    with pytest.raises(UnboundLocalError, match="Boom"):
        foo()
    assert counter["calls"] == 3

async def test_4(test_logger):
    counter = {"calls": 0}
    @retry(UnboundLocalError, tries=3, delay=0.01, logger=test_logger)
    async def foo():
        counter["calls"] += 1
        raise UnboundLocalError("Boom")

    with pytest.raises(UnboundLocalError, match="Boom"):
        await foo()


# ------------------------
# Custom Exception Raised After Retry Fails 
# ------------------------
def test_6(test_logger):
    counter = {"calls": 0}
    @retry(RuntimeError, tries=2, delay=0.01, throw_error=ValueError("Boom"), logger=test_logger, jitter=True)
    def foo():
        counter["calls"] += 1
        raise RuntimeError("Bang")

    with pytest.raises(ValueError, match="Boom"):
        foo()
    assert counter["calls"] == 2

async def test_7(test_logger):
    counter = {"calls": 0}
    @retry(RuntimeError, tries=2, delay=0.01, throw_error=ValueError("Boom"), logger=test_logger, jitter=True)
    async def foo():
        counter["calls"] += 1
        raise RuntimeError("Bang")

    with pytest.raises(ValueError, match="Boom"):
        await foo()
    assert counter["calls"] == 2


# ------------------------
# Error Not Caught by Retry Decorator
# ------------------------
def test_8(test_logger):
    counter = {"calls": 0}
    @retry(UnboundLocalError, tries=2, delay=0.01, logger=test_logger, jitter=True)
    def foo():
        counter["calls"] += 1
        raise RuntimeError("Bang")

    with pytest.raises(RuntimeError, match="Bang"):
        foo()
    assert counter["calls"] == 1

async def test_9(test_logger):
    counter = {"calls": 0}
    @retry(UnboundLocalError, tries=2, delay=0.01, logger=test_logger, jitter=True)
    async def foo():
        counter["calls"] += 1
        raise RuntimeError("Bang")

    with pytest.raises(RuntimeError, match="Bang"):
        await foo()
    assert counter["calls"] == 1


# ------------------------
# Retry with Multiple Exception Types
# ------------------------
def test_10():
    counter = {"calls": 0}

    @retry((ValueError, KeyError), tries=3, delay=0.01)
    def foo():
        counter["calls"] += 1
        if counter["calls"] == 1:
            raise ValueError("First failure")
        elif counter["calls"] == 2:
            raise KeyError("Second failure")
        return "success"

    result = foo()
    assert result == "success"
    assert counter["calls"] == 3

async def test_11():
    counter = {"calls": 0}

    @retry((ValueError, KeyError), tries=3, delay=0.01)
    async def foo():
        counter["calls"] += 1
        if counter["calls"] == 1:
            raise ValueError("First failure")
        elif counter["calls"] == 2:
            raise KeyError("Second failure")
        return "success"

    result = await foo()
    assert result == "success"
    assert counter["calls"] == 3