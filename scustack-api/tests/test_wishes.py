"""Tests for wish service and API."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


COURSE_ID = uuid4()
USER_ID = uuid4()
WISH_ID = uuid4()


def _make_mock_db():
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar = AsyncMock(return_value=value)
    return result


def _mock_execute_result(rows):
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


class TestWishService:
    @pytest.mark.asyncio
    async def test_create_wish_ok(self):
        from app.services.wish_service import create_wish

        db = _make_mock_db()
        db.scalar = AsyncMock(return_value=0)

        wish = await create_wish(db, USER_ID, COURSE_ID, '求期末真题', '需要2024年的', '考试资料')

        assert wish.title == '求期末真题'
        assert wish.course_id == COURSE_ID
        assert wish.user_id == USER_ID
        db.add.assert_called()

    @pytest.mark.asyncio
    async def test_create_wish_limit_exceeded(self):
        from app.services.wish_service import create_wish, MAX_OPEN_WISHES_PER_COURSE

        db = _make_mock_db()
        db.scalar = AsyncMock(return_value=MAX_OPEN_WISHES_PER_COURSE)

        with pytest.raises(ValueError, match='最多'):
            await create_wish(db, USER_ID, COURSE_ID, '再来一条')

    @pytest.mark.asyncio
    async def test_list_wishes_by_course(self):
        from app.services.wish_service import list_wishes
        from app.models.wish import Wish

        w = Wish(
            id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
            title='求笔记', status='open', vote_count=3,
        )
        db = _make_mock_db()
        db.execute = AsyncMock(return_value=_mock_execute_result([w]))

        items = await list_wishes(db, course_id=COURSE_ID)
        assert len(items) == 1
        assert items[0]['title'] == '求笔记'
        assert items[0]['vote_count'] == 3

    @pytest.mark.asyncio
    async def test_list_wishes_shows_has_voted(self):
        from app.services.wish_service import list_wishes
        from app.models.wish import Wish, WishVote

        w = Wish(
            id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
            title='求笔记', status='open', vote_count=1,
        )
        db = _make_mock_db()
        # First call: wishes query
        mock_wishes = _mock_execute_result([w])
        # Second call: vote check
        mock_vote = MagicMock()
        mock_vote.scalar_one_or_none.return_value = WishVote(wish_id=WISH_ID, user_id=USER_ID)
        db.execute = AsyncMock(side_effect=[mock_wishes, mock_vote])

        items = await list_wishes(db, course_id=COURSE_ID, current_user_id=USER_ID)
        assert items[0]['has_voted'] is True

    @pytest.mark.asyncio
    async def test_vote_wish_toggle_on(self):
        from app.services.wish_service import vote_wish
        from app.models.wish import Wish

        w = Wish(id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
                 title='t', status='open', vote_count=3)
        db = _make_mock_db()
        db.get = AsyncMock(return_value=w)
        # Vote check: no existing vote
        mock_no_vote = MagicMock()
        mock_no_vote.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_no_vote)

        result = await vote_wish(db, WISH_ID, USER_ID)
        assert result['action'] == 'voted'
        assert result['vote_count'] == 4

    @pytest.mark.asyncio
    async def test_vote_wish_toggle_off(self):
        from app.services.wish_service import vote_wish
        from app.models.wish import Wish, WishVote

        w = Wish(id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
                 title='t', status='open', vote_count=3)
        db = _make_mock_db()
        db.get = AsyncMock(return_value=w)
        db.delete = AsyncMock()
        # Vote check: existing vote
        mock_has_vote = MagicMock()
        mock_has_vote.scalar_one_or_none.return_value = WishVote(wish_id=WISH_ID, user_id=USER_ID)
        db.execute = AsyncMock(return_value=mock_has_vote)

        result = await vote_wish(db, WISH_ID, USER_ID)
        assert result['action'] == 'unvoted'
        assert result['vote_count'] == 2

    @pytest.mark.asyncio
    async def test_vote_wish_not_found(self):
        from app.services.wish_service import vote_wish

        db = _make_mock_db()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match='not found'):
            await vote_wish(db, WISH_ID, USER_ID)

    @pytest.mark.asyncio
    async def test_fulfill_wish_ok(self):
        from app.services.wish_service import fulfill_wish
        from app.models.wish import Wish

        material_id = uuid4()
        w = Wish(id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
                 title='t', status='open', vote_count=1)
        db = _make_mock_db()
        db.get = AsyncMock(return_value=w)

        result = await fulfill_wish(db, WISH_ID, material_id, USER_ID)
        assert result.status == 'fulfilled'
        assert result.fulfill_material_id == material_id

    @pytest.mark.asyncio
    async def test_fulfill_wish_not_owner(self):
        from app.services.wish_service import fulfill_wish
        from app.models.wish import Wish

        material_id = uuid4()
        other_user = uuid4()
        w = Wish(id=WISH_ID, user_id=USER_ID, course_id=COURSE_ID,
                 title='t', status='open', vote_count=1)
        db = _make_mock_db()
        db.get = AsyncMock(return_value=w)

        with pytest.raises(ValueError, match='only the wish creator'):
            await fulfill_wish(db, WISH_ID, material_id, other_user)


class TestWishAPI:
    @pytest.fixture
    async def client(self):
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as c:
            yield c

    async def test_list_wishes_no_auth(self, client):
        with patch('app.api.v1.wishes.wish_service.list_wishes', new_callable=AsyncMock, return_value=[]):
            with patch('app.api.v1.wishes.wish_service.count_wishes', new_callable=AsyncMock, return_value=0):
                resp = await client.get('/api/v1/wishes?course_id=00000000-0000-0000-0000-000000000001')
                assert resp.status_code == 200
                data = resp.json()
                assert data['code'] == 0

    async def test_create_wish_requires_auth(self, client):
        resp = await client.post('/api/v1/wishes', json={
            'course_id': str(COURSE_ID), 'title': 'test',
        })
        assert resp.status_code == 401

    async def test_vote_wish_requires_auth(self, client):
        resp = await client.post(f'/api/v1/wishes/{WISH_ID}/vote')
        assert resp.status_code == 401

    async def test_fulfill_wish_requires_auth(self, client):
        resp = await client.post(f'/api/v1/wishes/{WISH_ID}/fulfill', json={
            'material_id': str(uuid4()),
        })
        assert resp.status_code == 401
