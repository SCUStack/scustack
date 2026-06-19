import hashlib
from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RequestIdentity:
    identity_type: str
    key: str

    def scoped_key(self, prefix: str) -> str:
        return f'{prefix}:{self.identity_type}:{self.key}'


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]


def build_request_identity(request: Request, current_user=None) -> RequestIdentity:
    user_id = getattr(current_user, 'id', None)
    if user_id is not None:
        return RequestIdentity(
            identity_type='authenticated',
            key=_hash(f'user:{user_id}'),
        )

    ip = request.client.host if request.client else 'unknown'
    user_agent = request.headers.get('user-agent', '').strip()
    accept_language = request.headers.get('accept-language', '').strip()
    forwarded_for = request.headers.get('x-forwarded-for', '').strip()
    fingerprint = '|'.join([ip, forwarded_for, user_agent, accept_language])
    return RequestIdentity(
        identity_type='anonymous',
        key=_hash(f'anon:{fingerprint}'),
    )
