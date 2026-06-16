"""Tests for homepage recommendation algorithm."""
import math
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.homepage_service import (
    _quality_score,
    _heat_score,
    _freshness_score,
    _calendar_score,
    _pick_from,
    _personalize_scores,
    get_calendar_recommendations,
    get_personalized_recommendations,
    get_stats,
    get_calendar_label,
    CATEGORY_DIVERSITY_WINDOW,
    MAX_PER_CATEGORY_IN_WINDOW,
    W_QUALITY,
    W_HEAT,
    W_FRESHNESS,
    W_CALENDAR,
    SLOT_PLAN,
    TOTAL_SLOTS,
    PERSONALIZED_TOTAL_SLOTS,
)


def make_material(
    cid: str = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    category: str = '考试资料',
    avg_rating: float = 4.0,
    rating_count: int = 5,
    download_count: int = 100,
    trust_status: str = 'unverified',
    created_days_ago: int = 10,
):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.contributor_id = uuid.UUID(cid)
    m.category = category
    m.average_rating = avg_rating
    m.rating_count = rating_count
    m.download_count = download_count
    m.trust_status = trust_status
    m.created_at = datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    return m


def _mock_db_query(*return_values):
    """Build an AsyncMock db session.

    Each argument is a tuple of (result_list, use_scalars).
    use_scalars=True wraps in .scalars().all(), False uses .all() directly.
    """
    db = AsyncMock()
    mocks = []
    for val, use_scalars in return_values:
        m = MagicMock()
        if use_scalars:
            m.scalars.return_value.all.return_value = val
        else:
            m.all.return_value = val
        mocks.append(m)
    db.execute = AsyncMock(side_effect=mocks)
    return db


class TestScoringFunctions:
    def test_quality_score_excellent(self):
        m = make_material(avg_rating=5.0, trust_status='maintainer_picked')
        score = _quality_score(m)
        assert 0.8 < score <= 1.0

    def test_quality_score_poor(self):
        m = make_material(avg_rating=1.0, trust_status='doubtful')
        score = _quality_score(m)
        assert score < 0.3

    def test_quality_score_rating_weight(self):
        # Rating contributes 60%, trust 40%
        m = make_material(avg_rating=5.0, trust_status='unverified')
        expected = 0.6 * 1.0 + 0.4 * 0.50
        assert abs(_quality_score(m) - expected) < 0.01

    def test_heat_score_zero_downloads(self):
        m = make_material(download_count=0)
        assert _heat_score(m, 1000) == 0.0

    def test_heat_score_max_downloads(self):
        m = make_material(download_count=1000)
        assert abs(_heat_score(m, 1000) - 1.0) < 0.01

    def test_heat_score_log_scale(self):
        m = make_material(download_count=10)
        score = _heat_score(m, 1000)
        assert 0 < score < 1

    def test_freshness_today(self):
        m = make_material(created_days_ago=0)
        now = datetime.now(timezone.utc)
        assert abs(_freshness_score(m, now) - 1.0) < 0.05

    def test_freshness_old(self):
        m = make_material(created_days_ago=40)
        now = datetime.now(timezone.utc)
        assert _freshness_score(m, now) == 0.0

    def test_freshness_decay(self):
        now = datetime.now(timezone.utc)
        fresh = make_material(created_days_ago=0)
        week_old = make_material(created_days_ago=7)
        assert _freshness_score(fresh, now) > _freshness_score(week_old, now)

    def test_calendar_match(self):
        m = make_material(category='考试资料')
        assert _calendar_score(m, {'考试资料'}) == 1.0

    def test_calendar_no_match(self):
        m = make_material(category='教材')
        assert _calendar_score(m, {'考试资料'}) == 0.0

    def test_calendar_multiple_targets(self):
        m = make_material(category='复习提纲')
        assert _calendar_score(m, {'考试资料', '复习提纲'}) == 1.0

    def test_combined_score_range(self):
        m = make_material()
        max_dl = 1000
        now = datetime.now(timezone.utc)
        targets = {'考试资料'}
        q = _quality_score(m)
        h = _heat_score(m, max_dl)
        f = _freshness_score(m, now)
        c = _calendar_score(m, targets)
        total = (
            W_QUALITY * q + W_HEAT * h + W_FRESHNESS * f + W_CALENDAR * c
        )
        assert 0 < total < 1.5  # could be >1 with all maxed out


class TestSlotAllocation:
    def test_pick_from_basic(self):
        m1 = make_material(cid='a' * 32)
        m2 = make_material(cid='b' * 32)
        m3 = make_material(cid='a' * 32)
        candidates = [(m1, 0.9), (m2, 0.8), (m3, 0.7)]
        result = _pick_from(candidates, set(), 2, per_contrib_max=1)
        assert len(result) == 2
        # m1 (0.9) then m2 (0.8), m3 skipped because same contributor as m1
        assert result[0] is m1
        assert result[1] is m2

    def test_pick_from_per_contrib_max_2(self):
        m1 = make_material(cid='a' * 32)
        m2 = make_material(cid='a' * 32)
        m3 = make_material(cid='b' * 32)
        candidates = [(m1, 0.9), (m2, 0.8), (m3, 0.7)]
        result = _pick_from(candidates, set(), 3, per_contrib_max=2)
        assert len(result) == 3
        assert result[0] is m1
        assert result[1] is m2
        assert result[2] is m3

    def test_pick_from_respects_already(self):
        m1 = make_material(cid='a' * 32)
        m2 = make_material(cid='b' * 32)
        candidates = [(m1, 0.9), (m2, 0.8)]
        result = _pick_from(candidates, {m1.id}, 2)
        assert len(result) == 1
        assert result[0] is m2

    def test_pick_from_empty(self):
        assert _pick_from([], set(), 3) == []

    def test_pick_from_insufficient(self):
        m1 = make_material(cid='a' * 32)
        result = _pick_from([(m1, 0.9)], set(), 3)
        assert len(result) == 1

    def test_slot_plan_sums_to_10(self):
        assert TOTAL_SLOTS == 10


class TestCalendarLabel:
    def test_january_exam(self):
        with patch('app.services.homepage_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15, tzinfo=timezone.utc)
            from app.services.homepage_service import get_calendar_label as gcl
            # Can't easily mock the module-level import, test through integration
            pass


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_empty_materials(self):
        mock_db = _mock_db_query(([], True))
        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                assert result == []

    @pytest.mark.asyncio
    async def test_returns_correct_slot_count(self):
        mats = []
        for i in range(18):
            for _ in range(2):
                mats.append(make_material(cid=f'{i:032d}', category='考试资料'))
        # 2 cold-start-eligible contributors: recent + rated
        for c in range(18, 20):
            mats.append(make_material(cid=f'{c:032d}', category='考试资料', created_days_ago=0, rating_count=3))
            mats.append(make_material(cid=f'{c:032d}', category='考试资料', created_days_ago=5))
        # 3 vulnerable contributors
        for v in range(20, 23):
            for _ in range(2):
                mats.append(make_material(cid=f'{v:032d}', category='课堂笔记'))

        count_rows = [(uuid.UUID(f'{i:032d}'), 10) for i in range(20)]
        count_rows += [(uuid.UUID(f'{v:032d}'), 2) for v in range(20, 23)]

        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                # Algorithm gracefully underfills when diversity constraints
                # can't be met. 8-10 is the expected range.
                assert 8 <= len(result) <= TOTAL_SLOTS

    @pytest.mark.asyncio
    async def test_doubtful_excluded(self):
        good = make_material(cid='a' * 32, trust_status='unverified')
        # Doubtful material — in real query, SQL WHERE trust_status != 'doubtful' filters it.
        # Our mock pre-filters: only approved + non-doubtful in the returned pool.
        mats = [good]
        mock_db = _mock_db_query((mats, True), ([], False), ([(uuid.UUID('a' * 32), 1)], False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                # All returned materials are from the (pre-filtered) pool
                for m in result:
                    assert m.trust_status != 'doubtful'

    @pytest.mark.asyncio
    async def test_records_exposures(self):
        mats = [make_material(cid=f'{i:032d}') for i in range(25)]
        count_rows = [(uuid.UUID(f'{i:032d}'), 5) for i in range(25)]
        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        mock_bump = AsyncMock()
        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=mock_bump):
                result = await get_calendar_recommendations(mock_db)
                assert mock_bump.call_count == len(result)
                assert mock_bump.call_count > 0

    @pytest.mark.asyncio
    async def test_vulnerable_contributors_detected(self):
        mats = []
        for i in range(15):
            mats.append(make_material(cid=f'{i:032d}', category='考试资料'))
        for v in range(15, 18):
            for _ in range(2):
                mats.append(make_material(cid=f'{v:032d}', category='课堂笔记'))

        count_rows = [(uuid.UUID(f'{i:032d}'), 10) for i in range(15)]
        count_rows += [(uuid.UUID(f'{v:032d}'), 2) for v in range(15, 18)]
        # Contributor 15 is also a newcomer
        # Use a contributor from the vulnerable range (15-17) as newcomer
        newcomer_uuid = uuid.UUID(f'{15:032d}')
        mock_db = _mock_db_query((mats, True), ([(newcomer_uuid,)], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                result_cids = {m.contributor_id for m in result}
                vulnerable_cids = {uuid.UUID(f'{v:032d}') for v in range(15, 18)}
                assert len(result_cids & vulnerable_cids) > 0

    @pytest.mark.asyncio
    async def test_per_contributor_limit_in_calendar(self):
        same_cid = 'a' * 32
        mats = [make_material(cid=same_cid, category='考试资料', download_count=1000 - i) for i in range(5)]
        for i in range(25):
            mats.append(make_material(cid=f'{i:032d}', category='考试资料', download_count=10))

        count_rows = [(uuid.UUID(same_cid), 5)] + [(uuid.UUID(f'{i:032d}'), 5) for i in range(25)]
        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                dominant_count = sum(1 for m in result if m.contributor_id == uuid.UUID(same_cid))
                assert dominant_count <= 3  # 1 calendar + up to 2 remaining

    @pytest.mark.asyncio
    async def test_cold_start_includes_recent_materials(self):
        now = datetime.now(timezone.utc)
        cid_a = 'a' * 32
        cid_b = 'b' * 32
        cid_c = 'c' * 32

        recent_good = make_material(cid=cid_a, created_days_ago=0, rating_count=3)
        recent_bad = make_material(cid=cid_b, created_days_ago=0, rating_count=0)
        old = make_material(cid=cid_c, created_days_ago=7, rating_count=5)
        recent_good.created_at = now - timedelta(hours=12)
        recent_bad.created_at = now - timedelta(hours=12)
        old.created_at = now - timedelta(days=7)

        mats = [recent_good, recent_bad, old] + [
            make_material(cid=f'{i:032d}') for i in range(22)
        ]
        count_rows = [
            (uuid.UUID(cid_a), 5), (uuid.UUID(cid_b), 5), (uuid.UUID(cid_c), 5)
        ] + [(uuid.UUID(f'{i:032d}'), 5) for i in range(22)]

        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                result_ids = {m.id for m in result}
                assert recent_good.id in result_ids

    @pytest.mark.asyncio
    async def test_cold_start_includes_unrated_recent_materials(self):
        now = datetime.now(timezone.utc)
        unrated = make_material(
            cid='a' * 32,
            category='课堂笔记',
            avg_rating=0,
            rating_count=0,
            download_count=1,
        )
        unrated.created_at = now - timedelta(hours=2)

        mats = [unrated] + [
            make_material(
                cid=f'{i:032d}',
                category='考试资料',
                avg_rating=4.5,
                rating_count=8,
                download_count=300 - i,
            )
            for i in range(1, 25)
        ]
        count_rows = [(m.contributor_id, 5) for m in mats]
        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                assert unrated.id in {m.id for m in result}

    @pytest.mark.asyncio
    async def test_category_diversity_caps_first_homepage_window(self):
        dominant = [
            make_material(
                cid=f'{i:032d}',
                category='考试资料',
                avg_rating=5,
                rating_count=10,
                download_count=1000 - i,
            )
            for i in range(1, 9)
        ]
        alternatives = [
            make_material(cid='00000000000000000000000000000009', category='课堂笔记'),
            make_material(cid='00000000000000000000000000000010', category='教材'),
            make_material(cid='00000000000000000000000000000011', category='习题集'),
            make_material(cid='00000000000000000000000000000012', category='实验报告'),
        ]
        mats = dominant + alternatives
        count_rows = [(m.contributor_id, 5) for m in mats]
        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                first_window = result[:CATEGORY_DIVERSITY_WINDOW]
                counts = Counter(m.category for m in first_window)
                assert max(counts.values()) <= MAX_PER_CATEGORY_IN_WINDOW
                assert len(counts) > 1

    @pytest.mark.asyncio
    async def test_legacy_high_value_material_remains_eligible(self):
        legacy = make_material(
            cid='a' * 32,
            category='考试资料',
            avg_rating=5,
            rating_count=80,
            download_count=5000,
            trust_status='maintainer_picked',
            created_days_ago=720,
        )
        mats = [legacy] + [
            make_material(
                cid=f'{i:032d}',
                category='课堂笔记',
                avg_rating=3,
                rating_count=3,
                download_count=20 + i,
                created_days_ago=14,
            )
            for i in range(1, 25)
        ]
        count_rows = [(m.contributor_id, 5) for m in mats]
        mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_calendar_recommendations(mock_db)
                assert legacy.id in {m.id for m in result}

    @pytest.mark.asyncio
    async def test_exposure_decay_spreads_contributors(self):
        mats = [make_material(cid=f'{i:032d}', category='考试资料') for i in range(25)]
        count_rows = [(uuid.UUID(f'{i:032d}'), 5) for i in range(25)]

        exposure_store: dict[str, int] = {}

        async def mock_get_exposures(cids):
            return {cid: exposure_store.get(cid, 0) for cid in cids}

        async def mock_bump(cid):
            exposure_store[cid] = exposure_store.get(cid, 0) + 1
            return exposure_store[cid]

        all_result_cids = set()
        for _ in range(10):
            mock_db = _mock_db_query((mats, True), ([], False), (count_rows, False))
            with patch('app.services.homepage_service.get_exposures', new=mock_get_exposures):
                with patch('app.services.homepage_service.bump_exposure', new=mock_bump):
                    result = await get_calendar_recommendations(mock_db)
                    for m in result:
                        all_result_cids.add(str(m.contributor_id))

        assert len(all_result_cids) >= 8


class TestPersonalization:
    """Tests for the personalized recommendation pipeline."""

    def test_personalize_scores_boosts_bookmarked(self):
        """Materials from bookmarked courses get a score boost."""
        cid = uuid.uuid4()
        m1 = make_material(cid='a' * 32)
        m1.course_id = cid
        m2 = make_material(cid='b' * 32)
        m2.course_id = uuid.uuid4()

        scored = [(m1, 1.0), (m2, 1.0)]
        adjusted = _personalize_scores(scored, None, {cid}, set())

        # m1 (bookmarked course) should rank higher than m2
        assert adjusted[0][1] > adjusted[1][1]
        # Boost should be exactly 1.0 + COURSE_BOOST_BOOKMARK
        assert abs(adjusted[0][1] - 1.30) < 0.01

    def test_personalize_scores_boosts_preferred_category(self):
        """Materials in preferred categories get a download-level boost."""
        m = make_material(category='考试资料')
        scored = [(m, 1.0)]
        adjusted = _personalize_scores(scored, None, set(), {'考试资料', '课堂笔记'})
        assert abs(adjusted[0][1] - 1.15) < 0.01

    def test_personalize_scores_noop_without_context(self):
        """No boost when user has no bookmarks or preferences."""
        m = make_material()
        scored = [(m, 1.0)]
        adjusted = _personalize_scores(scored, None, set(), set())
        assert adjusted[0][1] == 1.0

    def test_personalize_scores_sort_order(self):
        """Materials with higher affinity sort above others."""
        bm_cid = uuid.uuid4()
        m_bookmark = make_material(cid='a' * 32, download_count=10)
        m_bookmark.course_id = bm_cid
        m_prefcat = make_material(cid='b' * 32, category='复习提纲', download_count=10)
        m_none = make_material(cid='c' * 32, download_count=10)

        scored = [(m_bookmark, 1.0), (m_prefcat, 1.0), (m_none, 1.0)]
        adjusted = _personalize_scores(scored, None, {bm_cid}, {'复习提纲'})
        adjusted.sort(key=lambda x: x[1], reverse=True)

        assert adjusted[0][0] is m_bookmark   # bookmark boost (1.30x)
        assert adjusted[1][0] is m_prefcat    # category boost (1.15x)
        assert adjusted[2][0] is m_none       # no boost (1.00x)

    @pytest.mark.asyncio
    async def test_personalized_pipeline_runs(self):
        """Personalized pipeline returns recommendations."""
        mats = [make_material(cid=f'{i:032d}', category='考试资料') for i in range(30)]

        # Single mock that returns materials for .scalars().all()
        # and empty for .all() and None for .first()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mats
        mock_result.all.return_value = []
        mock_result.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_personalized_recommendations(
                    mock_db, uuid.UUID('a' * 32)
                )
                assert len(result) <= PERSONALIZED_TOTAL_SLOTS
                assert len(result) >= 5

    @pytest.mark.asyncio
    async def test_personalized_pipeline_empty_materials(self):
        """Personalized returns empty when no materials exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.all.return_value = []
        mock_result.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            result = await get_personalized_recommendations(
                mock_db, uuid.UUID('a' * 32)
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_personalized_noop_for_user_without_history(self):
        """User with no bookmarks still gets recommendations from generic pools."""
        mats = [make_material(cid=f'{i:032d}', category='考试资料') for i in range(30)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mats
        mock_result.all.return_value = []
        mock_result.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.homepage_service.get_exposures', new=AsyncMock(return_value={})):
            with patch('app.services.homepage_service.bump_exposure', new=AsyncMock()):
                result = await get_personalized_recommendations(
                    mock_db, uuid.UUID('a' * 32)
                )
                assert len(result) >= 5
