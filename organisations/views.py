from django.views.generic import TemplateView
from dojo.mixins import OrgMixin


class DashboardView(OrgMixin, TemplateView):
    template_name = 'org/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member_count'] = self.org.club_members.filter(is_active=True).count()
        context['class_count'] = self.org.classes.count()
        return context
