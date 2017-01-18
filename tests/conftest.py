import locale

import pytest


@pytest.fixture(scope='session', autouse=True)
def russian_locale():
    """Set numeric locale to Russian for uniformity, because Egiks parse
    floating point values based on system locale."""
    locale.setlocale(locale.LC_NUMERIC, ('ru_RU', 'UTF-8'))
