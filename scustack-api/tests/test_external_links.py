"""Tests for external URL validation in upload_service."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestDomainExtraction:
    def test_extracts_domain_simple(self):
        from app.services.upload_service import _extract_domain
        assert _extract_domain('https://example.com/path') == 'example.com'

    def test_strips_www(self):
        from app.services.upload_service import _extract_domain
        assert _extract_domain('https://www.example.com') == 'example.com'

    def test_handles_subdomain(self):
        from app.services.upload_service import _extract_domain
        assert _extract_domain('https://docs.example.com/path') == 'docs.example.com'


class TestValidateExternalUrl:
    @pytest.mark.asyncio
    async def test_rejects_javascript_protocol(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        err = await validate_external_url(mock_db, 'javascript:alert(1)', 'user-1')
        assert err is not None
        assert '协议' in err

    @pytest.mark.asyncio
    async def test_rejects_data_protocol(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        err = await validate_external_url(mock_db, 'data:text/html,<script>alert(1)</script>', 'user-1')
        assert err is not None

    @pytest.mark.asyncio
    async def test_rejects_file_protocol(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        err = await validate_external_url(mock_db, 'file:///etc/passwd', 'user-1')
        assert err is not None

    @pytest.mark.asyncio
    async def test_rejects_blacklisted_domain(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        err = await validate_external_url(mock_db, 'https://bit.ly/abc', 'user-1')
        assert err is not None

    @pytest.mark.asyncio
    async def test_accepts_valid_https_url(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=0)
        err = await validate_external_url(mock_db, 'https://example.com/notes.pdf', 'user-1')
        assert err is None

    @pytest.mark.asyncio
    async def test_accepts_valid_http_url(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=0)
        err = await validate_external_url(mock_db, 'http://legacy-site.com/doc.html', 'user-1')
        assert err is None

    @pytest.mark.asyncio
    async def test_rejects_domain_over_limit(self):
        from app.services.upload_service import validate_external_url, DOMAIN_DAILY_LIMIT
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=DOMAIN_DAILY_LIMIT)
        err = await validate_external_url(mock_db, 'https://spam.example.com', 'user-1')
        assert err is not None
        assert '上限' in err

    @pytest.mark.asyncio
    async def test_rejects_missing_domain(self):
        from app.services.upload_service import validate_external_url
        mock_db = AsyncMock()
        err = await validate_external_url(mock_db, 'https:///', 'user-1')
        assert err is not None


class TestCheckNewUserReview:
    @pytest.mark.asyncio
    async def test_new_user_returns_true(self):
        from app.services.upload_service import check_new_user_review
        mock_db = AsyncMock()
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = yesterday
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await check_new_user_review(mock_db, str(uuid4()))
        assert result is True

    @pytest.mark.asyncio
    async def test_old_user_returns_false(self):
        from app.services.upload_service import check_new_user_review
        mock_db = AsyncMock()
        long_ago = datetime.now(timezone.utc) - timedelta(days=30)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = long_ago
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await check_new_user_review(mock_db, str(uuid4()))
        assert result is False

    @pytest.mark.asyncio
    async def test_user_not_found_returns_true(self):
        from app.services.upload_service import check_new_user_review
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await check_new_user_review(mock_db, str(uuid4()))
        assert result is True
