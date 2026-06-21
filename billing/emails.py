from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_invoice_email(invoice):
    """Send an invoice email to the member. Returns True on success."""
    member = invoice.member
    recipient = member.email
    if not recipient:
        guardians = member.guardians.filter(email__gt='').first()
        if guardians:
            recipient = guardians.email
    if not recipient:
        return False, 'No email address on file for this member.'

    org_name = invoice.organisation.name
    subject = f'Invoice from {org_name} — {invoice.period}'

    context = {'invoice': invoice, 'org_name': org_name}
    html_body = render_to_string('emails/invoice.html', context)
    text_body = (
        f"Hi {member.name},\n\n"
        f"Invoice from {org_name} for {invoice.period}.\n\n"
        f"Amount due: £{invoice.amount:.2f}\n"
        f"Due date: {invoice.due_date.strftime('%d %b %Y')}\n"
    )
    if invoice.notes:
        text_body += f"\n{invoice.notes}\n"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
    return True, recipient
