from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestContentExtract:
    @pytest.mark.asyncio
    async def test_extract_text_plain_file(self):
        from app.tasks.content_extract import extract_content_text

        response = MagicMock()
        response.content = '拉格朗日中值定理\n证明'.encode('utf-8')
        response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=response):
            text = await extract_content_text('https://storage.example/file.txt', 1024, 'txt')

        assert '拉格朗日中值定理' in text

    @pytest.mark.asyncio
    async def test_extract_skips_large_files(self):
        from app.tasks.content_extract import extract_content_text

        text = await extract_content_text('https://storage.example/huge.pdf', 60 * 1024 * 1024, 'pdf')
        assert text == ''

    @pytest.mark.asyncio
    async def test_extract_skips_oversized_pdf_before_download(self):
        from app.tasks.content_extract import MAX_PDF_EXTRACT_SIZE, extract_content_text

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as get:
            text = await extract_content_text('https://storage.example/huge.pdf', MAX_PDF_EXTRACT_SIZE + 1, 'pdf')

        assert text == ''
        get.assert_not_called()


class TestElasticsearchMapping:
    def test_mapping_includes_content_text(self):
        from app.core.elasticsearch import MATERIALS_MAPPING

        props = MATERIALS_MAPPING['mappings']['properties']
        assert 'content_text' in props

    @pytest.mark.asyncio
    async def test_search_uses_content_text_field(self):
        from app.core import elasticsearch as es

        captured = {}

        async def fake_search(index: str, body: dict):
            captured['body'] = body
            return {'hits': {'hits': [], 'total': {'value': 0}}}

        with patch.object(es, 'es', MagicMock(search=AsyncMock(side_effect=fake_search))):
            await es.search_materials('拉格朗日')

        fields = captured['body']['query']['function_score']['query']['bool']['must'][0]['multi_match']['fields']
        assert 'content_text^2' in fields
