from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import CreateView, ListView
from dojo.mixins import OrgAdminMixin
from .forms import GuardianFormSet, MemberForm
from .models import Member


class MemberListView(OrgAdminMixin, ListView):
    template_name = 'members/list.html'
    context_object_name = 'members'
    paginate_by = 50

    def get_queryset(self):
        qs = Member.objects.filter(organisation=self.org).prefetch_related('guardians').order_by('name')
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


class MemberCreateView(OrgAdminMixin, CreateView):
    template_name = 'members/form.html'
    form_class = MemberForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add member'
        if self.request.POST:
            context['guardian_formset'] = GuardianFormSet(self.request.POST)
        else:
            context['guardian_formset'] = GuardianFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        guardian_formset = context['guardian_formset']
        if not guardian_formset.is_valid():
            return self.form_invalid(form)
        member = form.save(commit=False)
        member.organisation = self.org
        member.save()
        guardian_formset.instance = member
        guardian_formset.save()
        messages.success(self.request, f'{member.name} added successfully.')
        return redirect('member_list', org_slug=self.org.slug)
