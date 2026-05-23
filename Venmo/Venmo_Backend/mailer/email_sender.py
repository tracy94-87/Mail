"""Send outbound mail via Resend (HTTPS) or Hostinger SMTP (local dev)."""

from __future__ import annotations

import os
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from email.headerregistry import Address
from smtplib import SMTPException

import resend
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _resend_api_key() -> str:
    """Read at runtime so Railway Variables are picked up reliably."""
    return (
        (os.environ.get('RESEND_API_KEY') or '').strip()
        or (getattr(settings, 'RESEND_API_KEY', '') or '').strip()
    )


def _resend_from_email() -> str:
    return (
        (os.environ.get('RESEND_FROM_EMAIL') or '').strip()
        or (getattr(settings, 'RESEND_FROM_EMAIL', '') or '').strip()
    )


def _on_railway() -> bool:
    return bool(os.environ.get('RAILWAY_ENVIRONMENT'))


def email_provider() -> str:
    """resend when API key is set; on Railway never use SMTP (ports blocked)."""
    forced = (getattr(settings, 'EMAIL_PROVIDER', '') or '').strip().lower()
    if forced in ('resend', 'smtp'):
        return forced
    if _resend_api_key():
        return 'resend'
    if _on_railway():
        return 'resend'
    return 'smtp'


def mail_config_ok() -> str | None:
    provider = email_provider()
    if provider == 'resend':
        if not _resend_api_key():
            return (
                'RESEND_API_KEY is missing. Create a key at https://resend.com/api-keys, '
                'add it in Railway → Variables, verify your sending domain in Resend, redeploy.'
            )
        if not _resend_from_email():
            return 'RESEND_FROM_EMAIL is not configured in settings / environment.'
        return None

    if not (settings.EMAIL_HOST_USER or '').strip():
        return 'EMAIL_HOST_USER is not configured in settings.py.'
    if not (settings.EMAIL_HOST_PASSWORD or '').strip():
        return (
            'EMAIL_HOST_PASSWORD is missing. For local SMTP, add your Hostinger app password '
            'to .env. On Railway Hobby, set RESEND_API_KEY instead (SMTP is blocked).'
        )
    return None


def format_from_header(display_name: str, address: str) -> str:
    name = (display_name or '').strip()
    addr = (address or '').strip()
    if not addr:
        return ''
    if not name or name.lower() == addr.lower():
        return addr
    return str(Address(display_name=name, addr_spec=addr))


def _friendly_mail_error(exc: Exception) -> str:
    msg = str(exc)
    lower = msg.lower()
    on_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT'))

    if email_provider() == 'resend':
        if 'domain' in lower and ('verify' in lower or 'verified' in lower):
            return (
                f'{msg} — Add and verify your domain at https://resend.com/domains, '
                'then set RESEND_FROM_EMAIL to an address on that domain.'
            )
        if 'from' in lower and ('invalid' in lower or 'not allowed' in lower):
            return (
                f'{msg} — From address must use your verified Resend domain '
                f'(configured: {settings.RESEND_FROM_EMAIL}).'
            )
        if 'api key' in lower or 'unauthorized' in lower or '401' in msg:
            return f'{msg} — Check RESEND_API_KEY in Railway → Variables.'
        return msg

    platform_hint = ''
    if on_railway:
        platform_hint = (
            ' Railway blocks outbound SMTP on Hobby plans. Set RESEND_API_KEY in '
            'Railway Variables (or upgrade to Pro for SMTP).'
        )
    elif os.environ.get('RENDER'):
        platform_hint = ' Render blocks outbound SMTP on free plans — use RESEND_API_KEY or upgrade.'

    if (
        '101' in msg
        or 'unreachable' in lower
        or 'timed out' in lower
        or 'timeout' in lower
        or '10060' in msg
        or isinstance(exc, (TimeoutError, FuturesTimeout))
    ):
        return (
            f'Cannot reach {settings.EMAIL_HOST}:{settings.EMAIL_PORT} ({msg}).'
            f'{platform_hint}'
        )
    if '535' in msg or 'authentication' in lower:
        return f'{msg} — Check EMAIL_HOST_PASSWORD matches your Hostinger app password.'
    return msg


def _smtp_reachable() -> str | None:
    host = settings.EMAIL_HOST
    port = int(settings.EMAIL_PORT)
    timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 10))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except OSError as exc:
        return _friendly_mail_error(exc)
    finally:
        sock.close()
    return None


def _send_smtp(msg: EmailMultiAlternatives) -> None:
    timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 10)) + 5
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(msg.send, fail_silently=False)
        try:
            future.result(timeout=timeout)
        except FuturesTimeout as exc:
            raise TimeoutError(
                f'SMTP send exceeded {timeout}s (Hostinger may be unreachable from this host).'
            ) from exc


def _send_resend(
    *,
    subject: str,
    plain: str,
    html: str,
    from_header: str,
    to: list[str],
    cc: list[str],
    bcc: list[str],
) -> None:
    resend.api_key = _resend_api_key()
    params: resend.Emails.SendParams = {
        'from': from_header,
        'to': to,
        'subject': subject,
        'html': html,
        'text': plain,
    }
    if cc:
        params['cc'] = cc
    if bcc:
        params['bcc'] = bcc
    resend.Emails.send(params)


def send_outbound_email(
    *,
    subject: str,
    plain: str,
    html: str,
    brand_name: str,
    from_email: str,
    to: list[str],
    cc: list[str] | None,
    bcc: list[str] | None,
    display_name_fn,
) -> str | None:
    """
    Send email. Returns None on success, or an error message string.
    """
    config_err = mail_config_ok()
    if config_err:
        return config_err

    cc_list = cc or []
    bcc_list = bcc or []
    display_name = display_name_fn(brand_name, from_email)

    if email_provider() == 'resend':
        from_addr = (_resend_from_email() or from_email).strip()
        from_header = format_from_header(display_name, from_addr)
        try:
            _send_resend(
                subject=subject,
                plain=plain,
                html=html,
                from_header=from_header,
                to=to,
                cc=cc_list,
                bcc=bcc_list,
            )
        except Exception as exc:
            return _friendly_mail_error(exc)
        return None

    reach_err = _smtp_reachable()
    if reach_err:
        return reach_err

    addr = (from_email or '').strip()
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=format_from_header(display_name, addr),
        to=to,
        cc=cc_list or None,
        bcc=bcc_list or None,
    )
    msg.attach_alternative(html, 'text/html')
    try:
        _send_smtp(msg)
    except SMTPException as exc:
        return _friendly_mail_error(exc)
    except (OSError, TimeoutError) as exc:
        return _friendly_mail_error(exc)
    except Exception as exc:
        return _friendly_mail_error(exc)
    return None
