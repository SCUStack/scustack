from unittest.mock import MagicMock

from app.core.observability import classify_public_path, estimate_cost_units


def test_classifies_cost_sensitive_public_paths():
    assert classify_public_path('/api/v1/homepage') == 'homepage'
    assert classify_public_path('/api/v1/search?q=math') == 'search'
    assert classify_public_path('/api/v1/materials/00000000-0000-0000-0000-000000000001/detail') == 'material_detail'
    assert classify_public_path('/api/v1/materials/00000000-0000-0000-0000-000000000001/download') == 'download'


def test_cost_units_include_nonzero_query_cost():
    request = MagicMock()
    request.url.path = '/api/v1/homepage'
    assert estimate_cost_units('homepage', request) > estimate_cost_units(None, request)
