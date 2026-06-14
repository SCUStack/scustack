import pytest


@pytest.mark.asyncio
async def test_404_returns_unified_format(client):
    response = await client.get('/api/v1/nonexistent')
    assert response.status_code == 404
    data = response.json()
    assert 'code' in data
    assert 'message' in data


@pytest.mark.asyncio
async def test_validation_error_format(client):
    response = await client.post(
        '/api/v1/health',
        json={'invalid': 'body'},
    )
    assert response.status_code in (405, 422)
