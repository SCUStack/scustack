import pytest


@pytest.mark.asyncio
async def test_api_response_format(client):
    response = await client.get('/api/v1/health')
    assert response.status_code == 200

    data = response.json()
    assert 'status' in data
    assert data['status'] == 'ok'


@pytest.mark.asyncio
async def test_openapi_docs(client):
    response = await client.get('/openapi.json')
    assert response.status_code == 200

    spec = response.json()
    assert spec['info']['title'] == '川流课栈 API'
