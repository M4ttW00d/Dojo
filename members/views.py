from django.views.generic import ListView
from dojo.mixins import OrgAdminMixin
from .models import Member


class MemberListView(OrgAdminMixin, ListView):
    template_name = 'members/list.html'
    context_object_name = 'members'
    paginate_by = 50

    def get_queryset(self):
        qs = Member.objects.filter(organisation=self.org).order_by('name')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(email__icontains=q) | qs.filter(phone__icontains=q)
        show = self.request.GET.get('show', 'active')
        if show == 'inactive':
            qs = qs.filter(is_active=False)
        elif show == 'all':
            pass
        else:
            qs = qs.filter(is_active=True)
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['members/partials/member_rows.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['show'] = self.request.GET.get('show', 'active')
        return context
