"""Sentry integration for error monitoring.

In dev without SENTRY_DSN, errors are logged locally instead.
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_sentry_available = False


def init_sentry():
    """Initialize Sentry if SENTRY_DSN is configured."""
    global _sentry_available

    dsn = getattr(settings, 'SENTRY_DSN', None)
    if not dsn:
        logger.info('Sentry DSN not configured — errors will be logged locally')
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.APP_ENV,
            traces_sample_rate=0.1 if settings.APP_ENV == 'prod' else 1.0,
            profiles_sample_rate=0.1 if settings.APP_ENV == 'prod' else 1.0,
            integrations=[
                FastApiIntegration(transaction_style='endpoint'),
                CeleryIntegration(),
            ],
        )
        _sentry_available = True
        logger.info('Sentry initialized for environment: %s', settings.APP_ENV)
    except ImportError:
        logger.warning('sentry-sdk not installed — errors will be logged locally')
    except Exception as e:
        logger.error('Sentry init failed: %s', e)


def capture_exception(exc: Exception | None = None):
    """Capture exception in Sentry if available, otherwise log locally."""
    if _sentry_available:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    if exc:
        logger.error('Unhandled exception: %s', exc, exc_info=True)


def capture_message(message: str, level: str = 'info'):
    """Capture a message in Sentry if available."""
    if _sentry_available:
        try:
            import sentry_sdk
            sentry_sdk.capture_message(message, level=level)
        except Exception:
            pass
    log_fn = getattr(logger, level, logger.info)
    log_fn('Sentry message: %s', message)
