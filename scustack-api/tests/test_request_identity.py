from types import SimpleNamespace

from starlette.requests import Request

from app.core.request_identity import build_request_identity


def make_request(headers=None, client_host='127.0.0.1'):
    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/api/v1/search',
        'headers': [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        'client': (client_host, 12345),
    }
    return Request(scope)


def test_anonymous_request_identity_uses_more_than_raw_ip():
    request_a = make_request(headers={'user-agent': 'UA-1', 'accept-language': 'zh-CN'}, client_host='1.1.1.1')
    request_b = make_request(headers={'user-agent': 'UA-2', 'accept-language': 'zh-CN'}, client_host='1.1.1.1')

    identity_a = build_request_identity(request_a)
    identity_b = build_request_identity(request_b)

    assert identity_a.identity_type == 'anonymous'
    assert identity_a.key != identity_b.key


def test_authenticated_request_identity_prefers_user_identity():
    request = make_request(headers={'user-agent': 'UA-1'}, client_host='1.1.1.1')
    user = SimpleNamespace(id='user-123')

    identity_a = build_request_identity(request, user)
    identity_b = build_request_identity(make_request(headers={'user-agent': 'UA-2'}, client_host='8.8.8.8'), user)

    assert identity_a.identity_type == 'authenticated'
    assert identity_a.key == identity_b.key
