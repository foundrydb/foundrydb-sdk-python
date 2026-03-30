"""
pytest configuration for foundrydb SDK tests.
"""
import pytest


# Configure pytest-asyncio to use auto mode so @pytest.mark.asyncio
# works without per-test decoration requirements.
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
