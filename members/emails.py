from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_welcome_email(member):
    """Send a welcome email to the member (or their guardian if no member email). Returns (success, recipient_or_error)."""
    recipient = member.email
    if not recipient:
        guardian = member.guardians.filter(email__gt='').first()
        if guardian:
            recipient = guardian.email
    if not recipient:
        return False, 'No email address on file.'

    org_name = member.organisation.name
    subject = f'Welcome to {org_name}'

    context = {'member': member, 'org_name': org_name}
    html_body = render_to_string('emails/welcome.html', context)
    text_body = (
        f"Hi {member.name},\n\n"
        f"Welcome to {org_name}! We're glad to have you with us.\n\n"
        f"If you have any questions, please get in touch.\n\n"
        f"See you on the mat,\n{org_name}\n"
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
    return True, recipient
