import pytest


@pytest.fixture
def settings():
    from actas.settings import get_settings

    return get_settings()
