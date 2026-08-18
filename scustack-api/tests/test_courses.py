"""Tests for college and course services — CRUD, alias search, course merge, college filter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


COURSE_ID = '00000000-0000-0000-0000-000000000001'
COLLEGE_ID = '00000000-0000-0000-0000-000000000001'


class TestCourseListAPI:
    async def test_list_empty(self, client):
        with patch('app.api.v1.courses.course_service.list_courses', new_callable=AsyncMock, return_value=[]):
            resp = await client.get(f'/api/v1/courses?college_id={COLLEGE_ID}')
            assert resp.json()['code'] == 0
            assert resp.json()['data'] == []

    async def test_list_with_college_filter(self, client):
        m = MagicMock()
        m.id = COURSE_ID; m.name = '数据结构'; m.slug = 'ds'
        m.college_id = COLLEGE_ID; m.aliases = []; m.description = ''
        m.credit = 3; m.category = 'core'; m.is_active = True
        m.created_at = __import__('datetime').datetime.now()
        m.updated_at = __import__('datetime').datetime.now()
        m.college = None
        with patch('app.api.v1.courses.course_service.list_courses', new_callable=AsyncMock, return_value=[m]):
            resp = await client.get(f'/api/v1/courses?college_id={COLLEGE_ID}')
            data = resp.json()['data']
            assert len(data) == 1
            assert data[0]['name'] == '数据结构'

    async def test_get_course_not_found(self, client):
        with patch('app.api.v1.courses.course_service.get_course', new_callable=AsyncMock, return_value=None):
            resp = await client.get(f'/api/v1/courses/{COURSE_ID}')
            assert resp.json()['code'] == 40400

    async def test_management_list_requires_authentication(self, client):
        resp = await client.get('/api/v1/courses/manage')
        assert resp.status_code == 401


class TestCourseService:
    @pytest.mark.asyncio
    async def test_list_courses(self):
        from app.services.course_service import list_courses
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_courses(mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_courses_filtered(self):
        from app.services.course_service import list_courses
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_courses(mock_db, college_id=COLLEGE_ID)
        assert result == []

    @pytest.mark.asyncio
    async def test_management_list_includes_inactive_courses(self):
        from app.services.course_service import list_courses
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_courses(mock_db, include_inactive=True)
        assert result == []
        statement = str(mock_db.execute.await_args.args[0])
        assert 'WHERE courses.is_active' not in statement

    @pytest.mark.asyncio
    async def test_create_course(self):
        from app.services.course_service import create_course
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()
        c = await create_course(mock_db, college_id=COLLEGE_ID, name='数据结构', slug='ds')
        assert c.name == '数据结构'
        assert c.slug == 'ds'
        mock_db.add.assert_called_once()
        mock_db.refresh.assert_awaited_once_with(c, attribute_names=['college'])

    @pytest.mark.asyncio
    async def test_update_course_refreshes_database_generated_timestamp(self):
        from app.services.course_service import update_course

        mock_db = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()
        course = MagicMock()

        with patch(
            'app.services.course_service.get_course',
            new_callable=AsyncMock,
            return_value=course,
        ):
            result = await update_course(mock_db, COURSE_ID, name='操作系统')

        assert result is course
        assert course.name == '操作系统'
        mock_db.refresh.assert_awaited_once_with(course, attribute_names=['updated_at'])

    @pytest.mark.asyncio
    async def test_find_by_alias(self):
        from app.services.course_service import find_by_alias
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await find_by_alias(mock_db, 'DS')
        assert result == []

    @pytest.mark.asyncio
    async def test_merge_courses(self):
        from app.services.course_service import merge_courses
        mock_db = MagicMock()
        mock_db.flush = AsyncMock()
        target = MagicMock()
        target.aliases = []
        source = MagicMock()
        source.aliases = ['DS']
        source.name = '旧数据结构'
        with patch('app.services.course_service.get_course', new_callable=AsyncMock, side_effect=[source, target]):
            result = await merge_courses(mock_db, 'tid', 'sid')
        assert result is True
