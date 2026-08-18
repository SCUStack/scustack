import asyncio
import errno
import hmac
import json
import os
import select
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class UniversityCredentialsRejectedError(Exception):
    pass


class UniversityAuthUnavailableError(Exception):
    pass


class UniversityIdentityVerifier(Protocol):
    async def verify(self, university_id: str, password: str) -> None: ...


class DisabledUniversityIdentityVerifier:
    async def verify(self, university_id: str, password: str) -> None:
        raise UniversityAuthUnavailableError('university identity verification is not configured')


class MockUniversityIdentityVerifier:
    def __init__(self, expected_password: str) -> None:
        self.expected_password = expected_password

    async def verify(self, university_id: str, password: str) -> None:
        if settings.APP_ENV == 'prod' or not self.expected_password:
            raise UniversityAuthUnavailableError('mock university verification is unavailable')
        if not hmac.compare_digest(password, self.expected_password):
            raise UniversityCredentialsRejectedError('university credentials were rejected')


class ScuCliUniversityIdentityVerifier:
    def __init__(self, executable: str, timeout_seconds: float, runtime_dir: str = '') -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.runtime_dir = runtime_dir or None

    async def verify(self, university_id: str, password: str) -> None:
        await asyncio.to_thread(self._verify_sync, university_id, password)

    def _verify_sync(self, university_id: str, password: str) -> None:
        if os.name == 'nt':
            raise UniversityAuthUnavailableError('scu-cli verifier requires a POSIX runtime')

        import pty

        executable = shutil.which(self.executable) or self.executable
        if not Path(executable).is_file():
            raise UniversityAuthUnavailableError('scu-cli executable was not found')

        runtime_parent = Path(self.runtime_dir) if self.runtime_dir else None
        if runtime_parent is not None and not runtime_parent.is_dir():
            raise UniversityAuthUnavailableError('scu-cli runtime directory does not exist')

        master_fd, slave_fd = pty.openpty()
        process: subprocess.Popen[bytes] | None = None
        output = bytearray()
        sent_university_id = False
        sent_password = False
        deadline = time.monotonic() + self.timeout_seconds

        try:
            with tempfile.TemporaryDirectory(dir=runtime_parent) as config_dir:
                env = {
                    'LANG': os.environ.get('LANG', 'C.UTF-8'),
                    'PATH': os.environ.get('PATH', ''),
                    'SCU_CLI_CONFIG_DIR': config_dir,
                }
                process = subprocess.Popen(
                    [executable, 'login'],
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    env=env,
                    close_fds=True,
                )
                os.close(slave_fd)
                slave_fd = -1

                while process.poll() is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        process.kill()
                        raise UniversityAuthUnavailableError('university verification timed out')
                    readable, _, _ = select.select([master_fd], [], [], min(remaining, 0.2))
                    if not readable:
                        continue
                    try:
                        chunk = os.read(master_fd, 4096)
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            break
                        raise
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > 65536:
                        process.kill()
                        raise UniversityAuthUnavailableError('scu-cli returned too much output')
                    if not sent_university_id and '学号: ' in output.decode(errors='ignore'):
                        os.write(master_fd, university_id.encode() + b'\n')
                        sent_university_id = True
                    if (
                        sent_university_id
                        and not sent_password
                        and '密码: ' in output.decode(errors='ignore')
                    ):
                        os.write(master_fd, password.encode() + b'\n')
                        sent_password = True

                process.wait(timeout=max(deadline - time.monotonic(), 0.1))
                while True:
                    readable, _, _ = select.select([master_fd], [], [], 0)
                    if not readable:
                        break
                    try:
                        output.extend(os.read(master_fd, 4096))
                    except OSError:
                        break

                result = self._parse_result(output.decode(errors='replace'))
                if process.returncode == 0 and result.get('ok') is True:
                    principal = str(result.get('data', {}).get('principal', ''))
                    if hmac.compare_digest(principal, university_id):
                        return
                    raise UniversityAuthUnavailableError('scu-cli returned an unexpected identity')

                error = result.get('error', {})
                message = str(error.get('message', '')).lower()
                credential_markers = (
                    'invalid_credentials',
                    'invalid_grant',
                    'invalid_password',
                    '用户不存在',
                    '用户名或密码',
                    '账号或密码',
                    '密码错误',
                )
                if error.get('kind') == 'login' and any(
                    marker in message for marker in credential_markers
                ):
                    raise UniversityCredentialsRejectedError('university credentials were rejected')
                raise UniversityAuthUnavailableError('university identity service is unavailable')
        except (UniversityCredentialsRejectedError, UniversityAuthUnavailableError):
            raise
        except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
            raise UniversityAuthUnavailableError(
                'university identity service is unavailable'
            ) from exc
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            if slave_fd >= 0:
                os.close(slave_fd)
            os.close(master_fd)

    @staticmethod
    def _parse_result(raw_output: str) -> dict:
        decoder = json.JSONDecoder()
        for index, char in enumerate(raw_output):
            if char != '{':
                continue
            try:
                value, _ = decoder.raw_decode(raw_output[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and 'ok' in value:
                return value
        raise ValueError('scu-cli did not return a JSON result')


def get_university_identity_verifier() -> UniversityIdentityVerifier:
    if settings.UNIVERSITY_AUTH_PROVIDER == 'mock':
        return MockUniversityIdentityVerifier(settings.UNIVERSITY_AUTH_MOCK_PASSWORD)
    if settings.UNIVERSITY_AUTH_PROVIDER == 'scu_cli':
        return ScuCliUniversityIdentityVerifier(
            settings.SCU_CLI_PATH,
            settings.SCU_CLI_TIMEOUT_SECONDS,
            settings.SCU_CLI_RUNTIME_DIR,
        )
    return DisabledUniversityIdentityVerifier()
