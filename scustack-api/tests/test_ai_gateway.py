from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.ai import MaterialDraft, MaterialDraftRequest
from app.services.ai_gateway import create_material_draft, list_providers, probe_providers


def _db_with_config(config):
    db = MagicMock()
    db.scalar = AsyncMock(return_value=config)
    db.flush = AsyncMock()
    return db


def test_numeric_confidence_is_normalized():
    draft = MaterialDraft.model_validate({'title': '资料', 'confidence': 0.7})
    assert draft.confidence == {'overall': 0.7}


@pytest.mark.asyncio
async def test_no_provider_returns_rule_based_draft():
    result = await create_material_draft(
        _db_with_config(None),
        MaterialDraftRequest(file_name='计算机网络_复习提纲.pdf'),
    )

    assert result.provider == 'fallback'
    assert result.draft.title == '计算机网络 复习提纲'


@pytest.mark.asyncio
async def test_provider_pool_fails_over_by_priority():
    config = MagicMock(config_value={'providers': [
        {'id': '1', 'name': 'primary', 'base_url': 'https://one.example/v1', 'model': 'one', 'priority': 1, 'enabled': True, 'api_key_encrypted': 'a'},
        {'id': '2', 'name': 'backup', 'base_url': 'https://two.example/v1', 'model': 'two', 'priority': 2, 'enabled': True, 'api_key_encrypted': 'b'},
    ]})
    draft = MaterialDraft(title='复习提纲', category='复习提纲')
    with patch('app.services.ai_gateway._complete', new_callable=AsyncMock, side_effect=[RuntimeError(), draft]) as complete:
        result = await create_material_draft(_db_with_config(config), MaterialDraftRequest(file_name='notes.pdf'))

    assert result.provider == 'backup'
    assert complete.await_count == 2


@pytest.mark.asyncio
async def test_provider_list_never_returns_api_key():
    config = MagicMock(config_value={'providers': [{
        'id': '1', 'name': 'provider', 'base_url': 'https://example.com/v1', 'model': 'model',
        'priority': 1, 'enabled': True, 'api_key_encrypted': 'ciphertext',
    }]})
    result = await list_providers(_db_with_config(config))

    assert result[0].has_api_key is True
    assert 'api_key' not in result[0].model_dump()


@pytest.mark.asyncio
async def test_probe_marks_provider_healthy():
    config = MagicMock(config_value={'providers': [{
        'id': '1', 'name': 'provider', 'base_url': 'https://example.com/v1', 'model': 'model',
        'priority': 1, 'enabled': True, 'api_key_encrypted': 'ciphertext',
    }]})
    response = MagicMock()
    response.raise_for_status = MagicMock()
    client = MagicMock(get=AsyncMock(return_value=response))
    context = MagicMock(__aenter__=AsyncMock(return_value=client), __aexit__=AsyncMock(return_value=False))
    with patch('app.services.ai_gateway.decrypt_pii', return_value='secret'), \
         patch('app.services.ai_gateway.httpx.AsyncClient', return_value=context):
        result = await probe_providers(_db_with_config(config))

    assert result[0].health == 'healthy'
