"""Tests for review queue query shape and course lookup behavior."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.review_service import get_review_queue


@pytest.mark.asyncio
async def test_review_queue_batches_course_lookup_and_keeps_missing_course_empty():
    first = MagicMock(
        id=uuid4(),
        course_id=uuid4(),
        title='First',
        category='lecture',
        semester='2025-2026-1',
        contributor_id=None,
        format='pdf',
        file_size=10,
        trust_status='unverified',
        review_status='pending',
        created_at=datetime.now(UTC),
    )
    second = MagicMock(
        id=uuid4(),
        course_id=uuid4(),
        title='Second',
        category='exam',
        semester='2025-2026-1',
        contributor_id=None,
        format='pdf',
        file_size=20,
        trust_status='unverified',
        review_status='returned',
        created_at=datetime.now(UTC),
    )
    total_result = MagicMock()
    total_result.scalar.return_value = 2
    items_result = MagicMock()
    items_result.all.return_value = [(first, 'Course A'), (second, None)]
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[total_result, items_result])

    items, total = await get_review_queue(db, limit=50)

    assert total == 2
    assert [item['course_name'] for item in items] == ['Course A', '']
    assert db.execute.await_count == 2
    queue_statement = db.execute.await_args_list[1].args[0]
    assert 'LEFT OUTER JOIN courses' in str(queue_statement)
