from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Member


class PortalView(View):
    def get(self, request, token):
        member = get_object_or_404(Member, token=token, is_active=True)
        org = member.organisation

        guardian = member.guardians.filter(email__gt='').first()
        has_guardians = member.guardians.exists()

        invoices = member.invoices.order_by('-created_at')
        outstanding = [inv for inv in invoices if inv.status != 'paid']
        paid = [inv for inv in invoices if inv.status == 'paid']

        from progression.models import MemberProgression
        progressions = (
            MemberProgression.objects
            .filter(member=member)
            .select_related('stage__system')
            .order_by('-achieved_date')
        )
        current_grade = progressions.first()

        outstanding_total = sum(inv.amount for inv in outstanding)

        return render(request, 'portal/index.html', {
            'member': member,
            'org': org,
            'guardian': guardian,
            'has_guardians': has_guardians,
            'outstanding': outstanding,
            'paid': paid,
            'current_grade': current_grade,
            'progressions': progressions,
            'outstanding_total': outstanding_total,
        })
