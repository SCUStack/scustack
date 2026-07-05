from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


OBSERVED_PUBLIC_PATHS = {
    'homepage': ('/api/v1/homepage',),
    'search': ('/api/v1/search',),
    'material_detail': ('/api/v1/materials/',),
    'download': ('/api/v1/materials/', '/download'),
    'preview': ('/api/v1/materials/', '/download'),
}


@dataclass
class PathCostSample:
    count: int = 0
    total_latency_ms: float = 0
    total_cost_units: int = 0
    recent_latency_ms: deque[float] = field(default_factory=lambda: deque(maxlen=100))

    def record(self, latency_ms: float, cost_units: int) -> None:
        self.count += 1
        self.total_latency_ms += latency_ms
        self.total_cost_units += cost_units
        self.recent_latency_ms.append(latency_ms)

    def snapshot(self) -> dict:
        recent = sorted(self.recent_latency_ms)
        p95 = recent[int((len(recent) - 1) * 0.95)] if recent else 0
        return {
            'count': self.count,
            'avg_latency_ms': round(self.total_latency_ms / self.count, 2) if self.count else 0,
            'p95_latency_ms': round(p95, 2),
            'avg_cost_units': round(self.total_cost_units / self.count, 2) if self.count else 0,
        }


_samples: dict[str, PathCostSample] = defaultdict(PathCostSample)


def classify_public_path(path: str) -> str | None:
    if path == '/api/v1/homepage':
        return 'homepage'
    if path.startswith('/api/v1/search'):
        return 'search'
    if path.startswith('/api/v1/materials/') and path.endswith('/download'):
        return 'download'
    if path.startswith('/api/v1/materials/') and path.endswith('/detail'):
        return 'material_detail'
    return None


def estimate_cost_units(route_id: str | None, request: Request) -> int:
    if route_id == 'download':
        return 8
    if route_id == 'search':
        return 5
    if route_id == 'homepage':
        return 4
    if route_id == 'material_detail':
        return 3
    if request.url.path.startswith('/api/v1/'):
        return 1
    return 0


def get_observability_snapshot() -> dict:
    return {route_id: sample.snapshot() for route_id, sample in _samples.items()}


class CostObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        route_id = classify_public_path(request.url.path)
        started = perf_counter()
        response = await call_next(request)
        latency_ms = (perf_counter() - started) * 1000
        cost_units = estimate_cost_units(route_id, request)

        if route_id:
            _samples[route_id].record(latency_ms, cost_units)
            response.headers['X-SCU-Route'] = route_id
            response.headers['X-SCU-Cost-Units'] = str(cost_units)
            response.headers['X-SCU-Latency-Ms'] = f'{latency_ms:.2f}'

        return response
