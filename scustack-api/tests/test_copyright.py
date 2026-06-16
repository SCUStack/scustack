"""Tests for copyright complaint service and API."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestTitleBlocklist:
    def test_blocked_title_matches(self):
        from app.services.copyright_service import check_title_blocklist
        assert check_title_blocklist('高等数学第七版课后答案完整版') is True

    def test_blocked_title_case_insensitive(self):
        from app.services.copyright_service import check_title_blocklist
        assert check_title_blocklist('同济高数第七版答案') is True

    def test_clean_title_passes(self):
        from app.services.copyright_service import check_title_blocklist
        assert check_title_blocklist('数据结构与算法笔记') is False

    def test_empty_title_passes(self):
        from app.services.copyright_service import check_title_blocklist
        assert check_title_blocklist('') is False


class TestTicketNumber:
    def test_generates_unique_tickets(self):
        from app.services.copyright_service import generate_ticket_number
        t1 = generate_ticket_number()
        t2 = generate_ticket_number()
        assert t1 != t2
        assert t1.startswith('DMCA-')
        assert len(t1) > 10


class TestCopyrightService:
    @pytest.mark.asyncio
    async def test_create_complaint_ok(self):
        from app.services.copyright_service import create_complaint

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        complaint = await create_complaint(
            db, '版权方', 'rights@example.com',
            'https://scustack.com/material/123', '本人声明...',
            contact_phone='13800000000', ip_address='1.2.3.4',
        )
        assert complaint.complainant_name == '版权方'
        assert complaint.status == 'pending'
        assert complaint.ticket_number.startswith('DMCA-')
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_complaints(self):
        from app.services.copyright_service import list_complaints
        from app.models.copyright_complaint import CopyrightComplaint

        c = CopyrightComplaint(
            ticket_number='DMCA-20260616-ABCD',
            complainant_name='Test', contact_email='t@t.com',
            infringing_url='https://x.com', statement='declaration',
            status='pending',
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [c]
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)

        items = await list_complaints(db, status='pending')
        assert len(items) == 1
        assert items[0].ticket_number == 'DMCA-20260616-ABCD'

    @pytest.mark.asyncio
    async def test_resolve_complaint_ok(self):
        from app.services.copyright_service import resolve_complaint
        from app.models.copyright_complaint import CopyrightComplaint

        cid = uuid4()
        uid = uuid4()
        complaint = CopyrightComplaint(
            id=cid, ticket_number='DMCA-20260616-ABCD',
            complainant_name='Test', contact_email='t@t.com',
            infringing_url='https://x.com', statement='declaration',
            status='pending',
        )
        db = AsyncMock()
        db.get = AsyncMock(return_value=complaint)
        db.flush = AsyncMock()

        result = await resolve_complaint(db, cid, 'resolved', uid, 'Handled')
        assert result.status == 'resolved'
        assert result.resolution_note == 'Handled'

    @pytest.mark.asyncio
    async def test_resolve_complaint_not_found(self):
        from app.services.copyright_service import resolve_complaint

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        result = await resolve_complaint(db, uuid4(), 'resolved', uuid4())
        assert result is None


class TestCopyrightAPI:
    @pytest.fixture
    async def client(self):
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as c:
            yield c

    async def test_submit_complaint_ok(self, client):
        with patch('app.api.v1.copyright.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True):
            with patch('app.api.v1.copyright.copyright_service.create_complaint') as mock_create:
                mock_complaint = MagicMock()
                mock_complaint.ticket_number = 'DMCA-20260616-ABCD'
                mock_complaint.created_at = MagicMock()
                mock_complaint.created_at.isoformat.return_value = '2026-06-16T00:00:00+00:00'
                mock_create.return_value = mock_complaint

                resp = await client.post('/api/v1/copyright/complaint', json={
                    'complainant_name': 'Test',
                    'contact_email': 'test@example.com',
                    'infringing_url': 'https://scustack.com/material/123',
                    'statement': 'This is my copyrighted work, I declare...',
                })
                assert resp.status_code == 200
                data = resp.json()
                assert data['code'] == 0
                assert data['data']['ticket_number'] == 'DMCA-20260616-ABCD'

    async def test_submit_complaint_invalid(self, client):
        resp = await client.post('/api/v1/copyright/complaint', json={
            'complainant_name': '',
            'contact_email': '',
            'infringing_url': '',
            'statement': 'short',
        })
        assert resp.status_code == 422

    async def test_list_complaints_requires_auth(self, client):
        resp = await client.get('/api/v1/copyright/complaints')
        assert resp.status_code == 401

    async def test_resolve_complaint_requires_auth(self, client):
        resp = await client.post(f'/api/v1/copyright/complaints/{uuid4()}/resolve', json={
            'status': 'resolved',
        })
        assert resp.status_code == 401
