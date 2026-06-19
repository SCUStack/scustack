from dataclasses import asdict, dataclass
from enum import StrEnum


class ProtectionLevel(StrEnum):
    BASELINE = 'baseline'
    GUARDED = 'guarded'
    STRICT = 'strict'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class EndpointProtectionPolicy:
    route_id: str
    route_pattern: str
    surface: str
    exposure: str
    protection_level: ProtectionLevel
    intended_identity: str
    current_protection: str
    intended_behaviors: tuple[str, ...]
    redis_failure_strategy: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data['protection_level'] = self.protection_level.value
        return data


ANTI_SCRAPING_POLICY_MATRIX: tuple[EndpointProtectionPolicy, ...] = (
    EndpointProtectionPolicy(
        route_id='homepage_feed',
        route_pattern='GET /api/v1/homepage',
        surface='homepage',
        exposure='Recent updates, hot courses, recommendation feed suitable for bulk discovery.',
        protection_level=ProtectionLevel.GUARDED,
        intended_identity='Anonymous fingerprint by IP today, upgrade to unified request identity in #240.',
        current_protection='No dedicated route limiter; only generic middleware applies.',
        intended_behaviors=(
            'Apply discovery-path rate limiting with cursor-sensitive burst control.',
            'Log unusually deep pagination or repeated feed pulls for observability.',
            'Treat this endpoint as a list-discovery path, not as a static marketing page.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing all protection.',
    ),
    EndpointProtectionPolicy(
        route_id='homepage_recent_updates',
        route_pattern='GET /api/v1/homepage/recent-updates',
        surface='homepage',
        exposure='Cursor-based recent-updates feed used for continued homepage browsing.',
        protection_level=ProtectionLevel.GUARDED,
        intended_identity='Anonymous fingerprint by IP today, upgrade to unified request identity in #240.',
        current_protection='No dedicated route limiter before splitting it from the homepage aggregate.',
        intended_behaviors=(
            'Apply the same discovery-path family of limits as the homepage feed.',
            'Protect repeated cursor-driven feed pulls without re-running homepage aggregate work.',
            'Keep pagination observable as a discovery surface in its own right.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing all protection.',
    ),
    EndpointProtectionPolicy(
        route_id='search_query',
        route_pattern='GET /api/v1/search',
        surface='search',
        exposure='High-value keyword search over approved materials and courses.',
        protection_level=ProtectionLevel.STRICT,
        intended_identity='Per-request identity that distinguishes anonymous and authenticated actors.',
        current_protection='Per-IP minute limiter plus rapid-scroll throttling.',
        intended_behaviors=(
            'Preserve search-specific rate limiting and scrolling burst detection.',
            'Escalate suspicious repeated enumeration through identity-aware counters.',
            'Use this endpoint as the baseline for stricter protections on adjacent discovery routes.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing all protection.',
    ),
    EndpointProtectionPolicy(
        route_id='search_suggest',
        route_pattern='GET /api/v1/search/suggest',
        surface='search',
        exposure='Low-latency suggestion endpoint that leaks discoverable course/material names.',
        protection_level=ProtectionLevel.STRICT,
        intended_identity='Per-request identity that can be shared with search query controls.',
        current_protection='Per-IP minute limiter.',
        intended_behaviors=(
            'Share identity and limiter buckets with the main search flow.',
            'Cap automated suggestion harvesting more aggressively than normal search.',
            'Feed protection signals into the same escalation path as search enumeration.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently becoming unbounded.',
    ),
    EndpointProtectionPolicy(
        route_id='colleges_list',
        route_pattern='GET /api/v1/colleges',
        surface='discovery',
        exposure='Top-level catalog enumeration for the full academic directory.',
        protection_level=ProtectionLevel.GUARDED,
        intended_identity='Shared discovery identity used across anonymous and authenticated browsing.',
        current_protection='No dedicated route limiter.',
        intended_behaviors=(
            'Bring into the same discovery-path limiter family as courses and materials lists.',
            'Keep anonymous browsing possible while making bulk enumeration meaningfully slower.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing discovery protection.',
    ),
    EndpointProtectionPolicy(
        route_id='courses_list',
        route_pattern='GET /api/v1/courses',
        surface='discovery',
        exposure='Course catalog enumeration with pagination and material counts.',
        protection_level=ProtectionLevel.GUARDED,
        intended_identity='Shared discovery identity used across anonymous and authenticated browsing.',
        current_protection='No dedicated route limiter.',
        intended_behaviors=(
            'Protect both all-course pagination and college-scoped listing paths.',
            'Align limiter policy with the discovery matrix instead of leaving it search-only.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing discovery protection.',
    ),
    EndpointProtectionPolicy(
        route_id='materials_list',
        route_pattern='GET /api/v1/materials',
        surface='discovery',
        exposure='Approved material listing path that can bypass search-specific protections.',
        protection_level=ProtectionLevel.STRICT,
        intended_identity='Shared discovery identity used across anonymous and authenticated browsing.',
        current_protection='No dedicated route limiter.',
        intended_behaviors=(
            'Apply discovery-path rate limits comparable to protected search flows.',
            'Treat repeated list enumeration as high-risk even when queries are empty.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing all protection.',
    ),
    EndpointProtectionPolicy(
        route_id='material_detail',
        route_pattern='GET /api/v1/materials/{material_id}',
        surface='detail',
        exposure='Single approved material metadata detail with contributor, trust, and version context.',
        protection_level=ProtectionLevel.GUARDED,
        intended_identity='Shared request identity reused by detail and related-resource requests.',
        current_protection='No dedicated route limiter.',
        intended_behaviors=(
            'Allow ordinary human navigation while making scripted deep crawling measurable.',
            'Coordinate with adjacent related-material traversal to prevent graph harvesting.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently losing detail traversal protection.',
    ),
    EndpointProtectionPolicy(
        route_id='material_related',
        route_pattern='GET /api/v1/materials/{material_id}/related',
        surface='detail',
        exposure='Graph expansion from one material into adjacent materials.',
        protection_level=ProtectionLevel.STRICT,
        intended_identity='Shared request identity reused with material detail traversal.',
        current_protection='No dedicated route limiter.',
        intended_behaviors=(
            'Treat repeated related-material traversal as an enumeration vector.',
            'Apply tighter burst controls than ordinary detail reads.',
        ),
        redis_failure_strategy='Degrade to per-process in-memory limiting instead of silently becoming unbounded.',
    ),
    EndpointProtectionPolicy(
        route_id='download_redirect',
        route_pattern='GET /api/v1/materials/{material_id}/download',
        surface='download',
        exposure='Highest-value hosted file access path.',
        protection_level=ProtectionLevel.CRITICAL,
        intended_identity='Authenticated user identity plus shared anonymous fingerprint fallback.',
        current_protection='Per-user daily download limit plus per-IP hourly limiter.',
        intended_behaviors=(
            'Preserve strict download quotas and add identity-aware fallback behavior.',
            'Treat Redis failure as a critical protection-path incident, not a silent bypass.',
        ),
        redis_failure_strategy='Explicit deny-on-uncertain when Redis is unavailable for the highest-value extraction path.',
    ),
)

ANTI_SCRAPING_POLICY_BY_ID = {policy.route_id: policy for policy in ANTI_SCRAPING_POLICY_MATRIX}


def export_policy_matrix() -> list[dict]:
    return [policy.to_dict() for policy in ANTI_SCRAPING_POLICY_MATRIX]
