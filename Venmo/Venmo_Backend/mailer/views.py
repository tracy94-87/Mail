import json
import os

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .email_builder import build_html_email, build_plain_text_email
from .email_sender import email_provider, mail_config_ok, send_outbound_email
from .forms import SendEmailPayloadForm, split_email_addresses


def sender_display_name(brand_name: str, from_email: str) -> str:
    """Human-readable inbox name (not the email address)."""
    name = (brand_name or '').strip()
    if name and '@' not in name:
        return name
    local = (from_email or '').split('@')[0]
    return local.replace('.', ' ').replace('_', ' ').title() or 'Support'


@require_GET
def api_mail_config(request):
    """Non-secret sanity check for production env wiring (Railway Variables)."""
    provider = email_provider()
    return JsonResponse(
        {
            'provider': provider,
            'resend_api_key_configured': bool(
                (os.environ.get('RESEND_API_KEY') or getattr(settings, 'RESEND_API_KEY', '') or '').strip()
            ),
            'resend_from_email': (
                os.environ.get('RESEND_FROM_EMAIL') or getattr(settings, 'RESEND_FROM_EMAIL', '')
            ),
            'smtp_password_configured': bool((settings.EMAIL_HOST_PASSWORD or '').strip()),
            'secret_key_configured': bool((settings.SECRET_KEY or '').strip()),
            'platform': 'railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'other',
            'config_ok': mail_config_ok() is None,
        }
    )


# Built-in templates for API clients (no database).
EMAIL_TEMPLATES = [
    {
        'id': 1,
        'name': 'Welcome Email',
        'template_type': 'transactional',
        'default_subject': 'Welcome to [Brand]! 👋',
        'default_body': (
            "We're thrilled to have you on board.\n\nHere's what you can do next:\n\n"
            '1. Set up your profile and preferences\n2. Explore all features in your dashboard\n'
            "3. Reach out to our support team anytime\n\nWe're committed to helping you succeed. "
            'If you ever have questions, just reply to this email.'
        ),
        'default_cta': 'Get Started →',
        'icon': '👋',
    },
    {
        'id': 2,
        'name': 'Promotional Offer',
        'template_type': 'promotional',
        'default_subject': '🎁 Exclusive 30% OFF — Limited Time!',
        'default_body': (
            'We have a special offer just for you! For a limited time, enjoy an exclusive discount '
            'on all our premium plans.\n\nHere\'s how to claim it:\n\n1. Click the button below to '
            'visit our store\n2. Add your favourite items to the cart\n3. Use code SAVE30 at checkout\n\n'
            'Offer valid until December 31, 2024. Don\'t miss out!'
        ),
        'default_cta': 'Claim Your Discount →',
        'icon': '🎁',
    },
    {
        'id': 3,
        'name': 'Monthly Newsletter',
        'template_type': 'newsletter',
        'default_subject': '📰 Your November Update from [Brand]',
        'default_body': (
            "Here are this month's highlights and updates.\n\nWe've been busy building things you'll "
            'love — from new features to community milestones. Here\'s everything you need to know:\n\n'
            '• New template builder launched\n• Open rate improvements across all clients\n'
            '• Tips: How to write irresistible subject lines\n\nWe hope you\'ve had a wonderful month. '
            'Feel free to reply directly to this email.'
        ),
        'default_cta': 'Read Full Update →',
        'icon': '📰',
    },
    {
        'id': 4,
        'name': 'Follow-Up',
        'template_type': 'reengage',
        'default_subject': 'Quick follow-up from [Brand]',
        'default_body': (
            'I wanted to follow up on my previous message — I hope it didn\'t get buried in your inbox!\n\n'
            "I'd love to show you how [Brand] can help streamline your workflow and save you time every week.\n\n"
            'Would you be available for a quick 15-minute call this week?'
        ),
        'default_cta': 'Book a Quick Call →',
        'icon': '🔄',
    },
    {
        'id': 5,
        'name': 'Invoice / Receipt',
        'template_type': 'transactional',
        'default_subject': 'Your [Brand] Invoice #MF-2024-0042',
        'default_body': (
            'Thank you for your payment. Your invoice details are below.\n\nInvoice #MF-2024-0042\n'
            'Date: November 22, 2024\nPlan: Pro Monthly — $49.00\nStatus: Paid\n\n'
            'Your next billing date is December 22, 2024. You can manage your billing in your account settings.'
        ),
        'default_cta': 'Download Invoice →',
        'icon': '🧾',
    },
]


def index(request):
    return render(request, 'mailer/index.html')


@require_GET
def api_templates(request):
    out = []
    for t in EMAIL_TEMPLATES:
        out.append(
            {
                'id': t['id'],
                'name': t['name'],
                'template_type': t['template_type'],
                'default_subject': t['default_subject'],
                'default_body': t['default_body'],
                'default_cta': t['default_cta'],
                'icon': t['icon'],
            }
        )
    return JsonResponse({'count': len(out), 'results': out})


@require_GET
def api_template_detail(request, pk):
    for t in EMAIL_TEMPLATES:
        if t['id'] == pk:
            return JsonResponse(t)
    return JsonResponse({'error': 'Template not found.'}, status=404)


@require_GET
def api_logs(request):
    return JsonResponse(
        {
            'count': 0,
            'results': [],
            'detail': 'Send history is not stored on this server.',
        }
    )


def _load_json(request):
    try:
        return json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _normalize_payload(payload: dict) -> dict:
    out = dict(payload)
    for key in (
        'recipients',
        'cc',
        'bcc',
        'body',
        'recipient_name',
        'cta_label',
        'support_contact',
        'brand_color',
        'scheduled_at',
    ):
        if out.get(key) is None:
            out[key] = ''
    if out.get('action') is None:
        out['action'] = 'send'
    return out


def _form_from_payload(payload):
    if not isinstance(payload, dict):
        return None, JsonResponse({'success': False, 'error': 'JSON object body required.'}, status=400)
    form = SendEmailPayloadForm(_normalize_payload(payload))
    if form.is_valid():
        return form, None
    return None, JsonResponse({'success': False, 'errors': form.errors}, status=400)


@csrf_exempt
@require_POST
def api_preview(request):
    payload = _load_json(request)
    if payload is None:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    form, err = _form_from_payload(payload)
    if err:
        return err
    d = form.cleaned_data
    html = build_html_email(
        brand_name=d['brand_name'],
        from_email=d['from_email'],
        subject=d['subject'],
        recipient_name=d['recipient_name'] or 'there',
        body=d['body'] or '',
        cta_label=d['cta_label'] or '',
        support_contact=d['support_contact'] or '',
        brand_color=d['brand_color'],
    )
    plain = build_plain_text_email(
        brand_name=d['brand_name'],
        subject=d['subject'],
        recipient_name=d['recipient_name'] or 'there',
        body=d['body'] or '',
        cta_label=d['cta_label'] or '',
        support_contact=d['support_contact'] or '',
    )
    return JsonResponse({'success': True, 'html': html, 'plain': plain})


@csrf_exempt
@require_POST
def api_send(request):
    payload = _load_json(request)
    if payload is None:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    form, err = _form_from_payload(payload)
    if err:
        return err
    d = form.cleaned_data

    if (d.get('scheduled_at') or '').strip():
        return JsonResponse(
            {
                'success': False,
                'error': 'Scheduled sending is not available without a job store.',
            },
            status=400,
        )

    if d['action'] == 'draft':
        return JsonResponse(
            {
                'success': True,
                'message': 'Draft accepted (not stored on server).',
            }
        )

    to_list = split_email_addresses(d['recipients'])
    cc_list = split_email_addresses(d['cc'])
    bcc_list = split_email_addresses(d['bcc'])

    html = build_html_email(
        brand_name=d['brand_name'],
        from_email=d['from_email'],
        subject=d['subject'],
        recipient_name=d['recipient_name'] or 'there',
        body=d['body'] or '',
        cta_label=d['cta_label'] or '',
        support_contact=d['support_contact'] or '',
        brand_color=d['brand_color'],
    )
    plain = build_plain_text_email(
        brand_name=d['brand_name'],
        subject=d['subject'],
        recipient_name=d['recipient_name'] or 'there',
        body=d['body'] or '',
        cta_label=d['cta_label'] or '',
        support_contact=d['support_contact'] or '',
    )

    send_err = send_outbound_email(
        subject=d['subject'],
        plain=plain,
        html=html,
        brand_name=d['brand_name'],
        from_email=d['from_email'],
        to=to_list,
        cc=cc_list,
        bcc=bcc_list,
        display_name_fn=sender_display_name,
    )
    if send_err:
        status = 500 if 'missing' in send_err.lower() else 502
        return JsonResponse({'success': False, 'error': send_err}, status=status)

    return JsonResponse(
        {
            'success': True,
            'message': f"Message sent to {len(to_list)} recipient(s).",
        }
    )
