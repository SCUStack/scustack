from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from openpyxl import Workbook

from app.services.course_import_service import import_courses, parse_course_workbook


HEADERS = ['学院', '课程名称', 'Slug', '别名', '分类', '学分', '描述', '川大课程号', '原开课单位']


def workbook_bytes(rows, headers=HEADERS):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def make_db(colleges=None, courses=None):
    db = MagicMock()
    db.flush = AsyncMock()
    db.scalars = AsyncMock(side_effect=[
        MagicMock(all=MagicMock(return_value=colleges or [])),
        MagicMock(all=MagicMock(return_value=courses or [])),
    ])
    return db


def make_college(name='数学学院'):
    college = MagicMock()
    college.id = uuid.uuid4()
    college.name = name
    return college


def test_parse_course_workbook():
    rows = parse_course_workbook(workbook_bytes([
        ['数学学院', '线性代数', 'linear-algebra', '矩阵代数；线代', '专业必修', 4, '基础课程', '201', '数学学院'],
    ]))

    assert len(rows) == 1
    assert rows[0].aliases == ['矩阵代数', '线代']
    assert rows[0].credit == 4


def test_parse_course_workbook_rejects_wrong_header():
    with pytest.raises(ValueError, match='表头必须为'):
        parse_course_workbook(workbook_bytes([], headers=['课程']))


@pytest.mark.asyncio
async def test_import_courses_dry_run_does_not_write():
    college = make_college()
    db = make_db([college])
    rows = parse_course_workbook(workbook_bytes([
        ['数学学院', '线性代数', 'linear-algebra', '', '专业必修', 4, '', '201', '数学学院'],
    ]))

    result = await import_courses(db, rows, dry_run=True)

    assert result['ready'] == 1
    assert result['imported'] == 0
    db.add_all.assert_not_called()
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_courses_writes_valid_rows():
    college = make_college()
    db = make_db([college])
    rows = parse_course_workbook(workbook_bytes([
        ['数学学院', '线性代数', 'linear-algebra', '', '专业必修', 4, '', '201', '数学学院'],
    ]))

    result = await import_courses(db, rows, dry_run=False)

    assert result['imported'] == 1
    db.add_all.assert_called_once()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_courses_reports_row_errors_together():
    college = make_college()
    existing = MagicMock()
    existing.college_id = college.id
    existing.name = '已存在课程'
    existing.slug = 'existing'
    db = make_db([college], [existing])
    rows = parse_course_workbook(workbook_bytes([
        ['不存在学院', '未知课程', 'bad_slug', '', '其它', 31, '', '201', '未知单位'],
        ['数学学院', '已存在课程', 'another-slug', '', '专业必修', 4, '', '202', '数学学院'],
    ]))

    result = await import_courses(db, rows, dry_run=True)

    assert result['error_count'] == 1
    assert result['skipped'] == 1
    assert result['errors'][0]['messages'] == [
        '学院不存在',
        'Slug 必须是英文小写、数字和连字符，并以字母开头',
        '学分必须在 0 到 30 之间',
        '分类必须是通识、专业必修、专业选修或实践',
    ]


@pytest.mark.asyncio
async def test_import_courses_rejects_duplicate_slug_and_name():
    college = make_college()
    db = make_db([college])
    rows = parse_course_workbook(workbook_bytes([
        ['数学学院', '课程一', 'shared-slug', '', '专业选修', 2, '', '201', '数学学院'],
        ['数学学院', '课程一', 'shared-slug', '', '专业选修', 2, '', '202', '数学学院'],
    ]))

    result = await import_courses(db, rows, dry_run=True)

    assert result['ready'] == 1
    assert result['error_count'] == 1
    assert 'Slug 已存在或在文件中重复' in result['errors'][0]['messages']
    assert '同学院课程在文件中重复' in result['errors'][0]['messages']
