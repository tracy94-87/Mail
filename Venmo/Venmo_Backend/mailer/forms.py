import re

from django import forms


def split_email_addresses(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [p.strip() for p in re.split(r'[,;]+', raw) if p.strip()]


class SendEmailPayloadForm(forms.Form):
    brand_name = forms.CharField(max_length=150)
    from_email = forms.EmailField()
    recipients = forms.CharField(required=False)
    cc = forms.CharField(required=False)
    bcc = forms.CharField(required=False)
    subject = forms.CharField(max_length=255)
    body = forms.CharField(required=False)
    recipient_name = forms.CharField(max_length=100, required=False)
    cta_label = forms.CharField(max_length=100, required=False)
    support_contact = forms.CharField(max_length=150, required=False)
    brand_color = forms.CharField(max_length=20, required=False)
    scheduled_at = forms.CharField(required=False)
    track_opens = forms.BooleanField(required=False, initial=False)
    track_clicks = forms.BooleanField(required=False, initial=True)
    action = forms.ChoiceField(choices=[('send', 'send'), ('draft', 'draft')])

    def clean_brand_name(self):
        value = (self.cleaned_data.get('brand_name') or '').strip()
        if not value:
            raise forms.ValidationError('Sender / brand name is required.')
        if '@' in value:
            raise forms.ValidationError(
                'Use a display name (e.g. "MailFlow Support"), not an email address.'
            )
        return value

    def clean_brand_color(self):
        value = (self.cleaned_data.get('brand_color') or '').strip() or '#008CFF'
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise forms.ValidationError('Must be a 6-digit hex color like #008CFF.')
        return value

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        action = data.get('action')
        rec = (data.get('recipients') or '').strip()
        if action == 'send' and not split_email_addresses(rec):
            raise forms.ValidationError({'recipients': ['At least one recipient is required to send.']})
        return data


SendMailForm = SendEmailPayloadForm
