from app.core.anti_scraping import (
    ANTI_SCRAPING_POLICY_MATRIX,
    ProtectionLevel,
    export_policy_matrix,
)


def test_policy_matrix_inventories_core_high_value_paths():
    route_ids = {policy.route_id for policy in ANTI_SCRAPING_POLICY_MATRIX}
    assert {
        'homepage_feed',
        'search_query',
        'search_suggest',
        'colleges_list',
        'courses_list',
        'materials_list',
        'material_detail',
        'material_related',
        'download_redirect',
    }.issubset(route_ids)


def test_policy_matrix_marks_highest_value_download_as_critical():
    download_policy = next(policy for policy in ANTI_SCRAPING_POLICY_MATRIX if policy.route_id == 'download_redirect')
    assert download_policy.protection_level == ProtectionLevel.CRITICAL
    assert 'Redis failure' in ' '.join(download_policy.intended_behaviors) or download_policy.redis_failure_strategy


def test_exported_matrix_is_serializable_and_keeps_levels_explicit():
    exported = export_policy_matrix()
    assert all(isinstance(policy['protection_level'], str) for policy in exported)
    assert exported[0]['route_pattern'].startswith('GET /api/v1/')
