"""
email_builder.py
Builds the branded HTML email that is sent to recipients,
mirroring exactly what the live preview shows in the frontend.
"""
import html as _html
import re


def _x(value: str) -> str:
    """HTML-escape a string (matches the frontend x() helper)."""
    return _html.escape(str(value), quote=True)


def _parse_body(raw_body: str, brand_color: str) -> tuple[str, str]:
    """
    Split numbered-list lines (1. …) from regular paragraph lines.
    Returns (paragraphs_html, steps_html).
    """
    lines = raw_body.split('\n')
    steps = []
    body_lines = []

    for line in lines:
        m = re.match(r'^(\d+)\.\s+(.+)', line)
        if m:
            steps.append(m.group(2))
        else:
            body_lines.append(line)

    # Build paragraph HTML
    raw_paras = '\n'.join(body_lines)
    para_blocks = [p.strip() for p in re.split(r'\n\s*\n', raw_paras) if p.strip()]

    para_html_parts = []
    for block in para_blocks:
        blines = block.split('\n')
        if any(l.strip().startswith('•') for l in blines):
            # Bullet list
            parts = []
            for l in blines:
                if l.strip().startswith('•'):
                    parts.append(
                        f'<div style="font-size:13.5px;color:#444;margin:4px 0;padding-left:4px">'
                        f'• {_x(l.strip().lstrip("• ").strip())}</div>'
                    )
                else:
                    parts.append(
                        f'<p style="font-size:13.5px;color:#444;line-height:1.65;margin:0 0 10px">'
                        f'{_x(l)}</p>'
                    )
            para_html_parts.append(''.join(parts))
        else:
            inline = _x(block).replace('\n', '<br>')
            para_html_parts.append(
                f'<p style="font-size:13.5px;color:#444;line-height:1.65;margin:0 0 12px">'
                f'{inline}</p>'
            )

    paragraphs_html = ''.join(para_html_parts)

    # Build steps HTML
    if steps:
        step_items = ''.join(
            f'''<div style="display:flex;gap:10px;align-items:flex-start;font-size:13.5px;
                color:#444;line-height:1.55;margin-bottom:10px">
              <span style="min-width:22px;height:22px;border-radius:50%;
                background:{_x(brand_color)};color:#fff;font-size:11px;font-weight:700;
                display:inline-flex;align-items:center;justify-content:center;
                flex-shrink:0;margin-top:1px">{i + 1}</span>
              <span>{_x(s)}</span>
            </div>'''
            for i, s in enumerate(steps)
        )
        steps_html = f'<div style="margin:14px 0 16px">{step_items}</div>'
    else:
        steps_html = ''

    return paragraphs_html, steps_html


def build_html_email(
    brand_name: str,
    from_email: str,
    subject: str,
    recipient_name: str,
    body: str,
    cta_label: str,
    support_contact: str,
    brand_color: str = '#008CFF',
) -> str:
    """
    Returns a complete HTML string for the branded email.
    This mirrors the live preview rendered by updatePreview() in the JS.
    """
    paragraphs_html, steps_html = _parse_body(body, brand_color)

    # CTA button
    cta_html = ''
    if cta_label:
        cta_html = f'''
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="margin:16px 0">
          <tr><td align="center">
            <a href="#"
               style="display:inline-block;background:{_x(brand_color)};color:#fff;
                      text-align:center;padding:14px 36px;border-radius:6px;
                      font-size:14px;font-weight:700;text-decoration:none;
                      font-family:Arial,Helvetica,sans-serif">
              {_x(cta_label)}
            </a>
          </td></tr>
        </table>'''

    # Support block
    support_html = ''
    if support_contact:
        support_html = f'''
        <div style="display:flex;align-items:center;gap:12px;padding:16px 24px;
                    background:#fafafa;border-top:1px solid #eee">
          <div style="width:34px;height:34px;border-radius:50%;background:#111;
                      display:flex;align-items:center;justify-content:center;
                      flex-shrink:0;font-size:16px">📞</div>
          <div>
            <div style="font-weight:700;color:#111;font-size:13px;margin-bottom:2px">
              Get in touch with {_x(brand_name)} Support. Available 24/7.
            </div>
            <a href="tel:{_x(support_contact)}"
               style="color:{_x(brand_color)};font-size:13px;font-weight:700;
                      text-decoration:none">
              {_x(support_contact)}
            </a>
          </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_x(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#f4f4f4;padding:32px 0">
    <tr><td align="center">
      <div style="max-width:580px;width:100%;margin:0 auto;
                  font-family:Arial,Helvetica,sans-serif;border-radius:8px;
                  overflow:hidden;box-shadow:0 4px 28px rgba(0,0,0,.14);
                  background:#fff">

        <!-- Brand header -->
        <div style="background:{_x(brand_color)};padding:24px 20px;text-align:center">
          <span style="font-family:Arial,Helvetica,sans-serif;font-size:28px;
                       font-weight:900;color:#ffffff;letter-spacing:-1px">
            {_x(brand_name)}
          </span>
        </div>

        <!-- Subject headline -->
        <div style="padding:22px 24px 4px">
          <h1 style="margin:0;font-size:21px;font-weight:900;color:#111;
                     line-height:1.2;font-family:Arial,Helvetica,sans-serif">
            {_x(subject)}
          </h1>
        </div>

        <!-- Body -->
        <div style="padding:16px 24px 20px">
          <p style="font-size:14px;color:#333;margin:0 0 14px;font-weight:400">
            Hi {_x(recipient_name)},
          </p>
          {paragraphs_html}
          {steps_html}
          {cta_html}
          <hr style="border:none;border-top:1px solid #eee;margin:18px 0">
          <p style="font-size:11.5px;color:#999;line-height:1.6;margin:0">
            This email was sent by
            <strong style="color:#666">{_x(brand_name)}</strong>.
            If you believe you received this in error, please contact our support team.
          </p>
        </div>

        {support_html}

        <!-- Footer -->
        <div style="padding:12px 24px;font-size:10px;color:#ccc;text-align:center;
                    line-height:1.7;border-top:1px solid #f0f0f0;background:#fafafa">
          &copy; 2024 {_x(brand_name)} &nbsp;&middot;&nbsp;
          <a href="#" style="color:#ccc;text-decoration:underline">Unsubscribe</a>
          &nbsp;&middot;&nbsp;
          <a href="#" style="color:#ccc;text-decoration:underline">Privacy Policy</a>
        </div>

      </div>
    </td></tr>
  </table>
</body>
</html>'''


def build_plain_text_email(
    brand_name: str,
    subject: str,
    recipient_name: str,
    body: str,
    cta_label: str,
    support_contact: str,
) -> str:
    """
    Plain-text fallback for email clients that don't support HTML.
    """
    lines = [
        f'{brand_name}',
        '=' * len(brand_name),
        '',
        f'Subject: {subject}',
        '',
        f'Hi {recipient_name},',
        '',
        body,
    ]
    if cta_label:
        lines += ['', f'→ {cta_label}']
    if support_contact:
        lines += ['', f'Support: {support_contact}']
    lines += ['', '—', f'{brand_name}']
    return '\n'.join(lines)