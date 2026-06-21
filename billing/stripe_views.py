import json
import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Invoice, Payment


class StripeWebhookView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        if not settings.STRIPE_SECRET_KEY:
            return HttpResponse(status=400)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            if webhook_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            else:
                event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            try:
                invoice_pk = session.metadata['invoice_pk']
            except (AttributeError, KeyError, TypeError):
                invoice_pk = None
            if invoice_pk:
                try:
                    invoice = Invoice.objects.get(pk=invoice_pk)
                    if invoice.status != 'paid':
                        Payment.objects.create(
                            invoice=invoice,
                            amount=invoice.amount,
                            method='Stripe',
                            stripe_payment_id=getattr(session, 'payment_intent', ''),
                            notes=f"Stripe Checkout session {session.id}",
                            paid_at=timezone.now(),
                        )
                        invoice.status = 'paid'
                        invoice.save(update_fields=['status'])
                except Invoice.DoesNotExist:
                    pass

        return HttpResponse(status=200)
