import html as _html
import re


def _x(value: str) -> str:
    return _html.escape(str(value), quote=True)


def _parse_body(raw_body: str, brand_color: str):
    lines = raw_body.split('\n')
    steps = []
    body_lines = []

    for line in lines:
        m = re.match(r'^(\d+)\.\s+(.+)', line)
        if m:
            steps.append(m.group(2))
        else:
            body_lines.append(line)

    raw_paras = '\n'.join(body_lines)
    para_blocks = [p.strip() for p in re.split(r'\n\s*\n', raw_paras) if p.strip()]

    para_html_parts = []
    for block in para_blocks:
        blines = block.split('\n')
        if any(l.strip().startswith('•') for l in blines):
            parts = []
            for l in blines:
                if l.strip().startswith('•'):
                    parts.append(
                        f'<p style="font-size:13.5px;color:#444;margin:4px 0;padding-left:4px">'
                        f'• {_x(l.strip().lstrip("• ").strip())}</p>'
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
                f'<p style="font-size:13.5px;color:#444;line-height:1.65;margin:0 0 12px;'
                f'font-family:Arial,Helvetica,sans-serif">'
                f'{inline}</p>'
            )

    paragraphs_html = ''.join(para_html_parts)

    if steps:
        step_rows = ''
        for i, s in enumerate(steps):
            step_rows += f'''
            <tr>
              <td width="30" valign="top" style="padding-bottom:10px">
                <table cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td align="center" valign="middle"
                        style="width:22px;height:22px;border-radius:11px;
                               background:{_x(brand_color)};color:#fff;
                               font-size:11px;font-weight:700;
                               font-family:Arial,Helvetica,sans-serif">
                      {i + 1}
                    </td>
                  </tr>
                </table>
              </td>
              <td style="padding-left:10px;padding-bottom:10px;font-size:13.5px;
                         color:#444;line-height:1.55;font-family:Arial,Helvetica,sans-serif">
                {_x(s)}
              </td>
            </tr>'''
        steps_html = f'''
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="margin:14px 0 16px">
          {step_rows}
        </table>'''
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
    paragraphs_html, steps_html = _parse_body(body, brand_color)

    cta_html = ''
    if cta_label:
        cta_html = f'''
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="margin:16px 0">
          <tr>
            <td align="center">
              <a href="#"
                 style="display:inline-block;background:{_x(brand_color)};color:#fff;
                        text-align:center;padding:14px 36px;border-radius:6px;
                        font-size:14px;font-weight:700;text-decoration:none;
                        font-family:Arial,Helvetica,sans-serif">
                {_x(cta_label)}
              </a>
            </td>
          </tr>
        </table>'''

    support_html = ''
    if support_contact:
        support_html = f'''
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background:#fafafa;border-top:1px solid #eee">
          <tr>
            <td width="50" align="center" valign="middle"
                style="padding:16px 0 16px 24px">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" valign="middle"
                      style="width:34px;height:34px;border-radius:17px;
                             background:#111;font-size:16px;color:#fff;
                             font-family:Arial,Helvetica,sans-serif">
                    &#128222;
                  </td>
                </tr>
              </table>
            </td>
            <td valign="middle" style="padding:16px 24px 16px 12px">
              <p style="font-weight:700;color:#111;font-size:13px;margin:0 0 2px;
                        font-family:Arial,Helvetica,sans-serif">
                Get in touch with {_x(brand_name)} Support. Available 24/7.
              </p>
              <a href="tel:{_x(support_contact)}"
                 style="color:{_x(brand_color)};font-size:13px;font-weight:700;
                        text-decoration:none;font-family:Arial,Helvetica,sans-serif">
                {_x(support_contact)}
              </a>
            </td>
          </tr>
        </table>'''

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
  <tr>
    <td align="center">

      <table width="580" cellpadding="0" cellspacing="0" border="0"
             style="max-width:580px;width:100%;background:#fff;
                    border-radius:8px;overflow:hidden;
                    box-shadow:0 4px 28px rgba(0,0,0,.14)">

        <tr>
          <td align="center" bgcolor="{_x(brand_color)}"
              style="padding:24px 20px;background:{_x(brand_color)};text-align:center">
            <span style="font-size:26px;font-weight:700;color:#ffffff;
                         font-family:Helvetica,Arial,sans-serif;letter-spacing:0">
              {_x(brand_name)}
            </span>
          </td>
        </tr>

        <tr>
          <td style="padding:22px 24px 4px">
            <h1 style="margin:0;font-size:21px;font-weight:900;color:#111;
                       line-height:1.2;font-family:Arial,Helvetica,sans-serif">
              {_x(subject)}
            </h1>
          </td>
        </tr>

        <tr>
          <td style="padding:16px 24px 20px">
            <p style="font-size:14px;color:#333;margin:0 0 14px;
                      font-family:Arial,Helvetica,sans-serif">
              Hi {_x(recipient_name)},
            </p>
            {paragraphs_html}
            {steps_html}
            {cta_html}
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="margin:18px 0">
              <tr>
                <td style="border-top:1px solid #eee;font-size:1px;line-height:1px">
                  &nbsp;
                </td>
              </tr>
            </table>
            <p style="font-size:11.5px;color:#999;line-height:1.6;margin:0;
                      font-family:Arial,Helvetica,sans-serif">
              This email was sent by
              <strong style="color:#666">{_x(brand_name)}</strong>.
            </p>
          </td>
        </tr>

        {f'<tr><td>{support_html}</td></tr>' if support_contact else ''}

        <tr>
          <td align="center"
              style="padding:12px 24px;font-size:10px;color:#ccc;
                     border-top:1px solid #f0f0f0;background:#fafafa;
                     font-family:Arial,Helvetica,sans-serif">
            &copy; 2024 {_x(brand_name)} &nbsp;&middot;&nbsp;
            <a href="#" style="color:#ccc;text-decoration:underline">Unsubscribe</a>
          </td>
        </tr>

      </table>

    </td>
  </tr>
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