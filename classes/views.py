import json
from datetime import date, timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from dojo.mixins import OrgAdminMixin
from members.models import Member

from .models import Attendance, Class, ClassMember, Session


DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DAYS_JSON = json.dumps(DAYS)


def _class_form_class():
    from django import forms

    class ClassForm(forms.ModelForm):
        class Meta:
            model = Class
            fields = ['name', 'description']
            widgets = {'description': forms.Textarea(attrs={'rows': 3})}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    return ClassForm


def _parse_schedule(post_data):
    schedule = []
    days = post_data.getlist('schedule_day')
    times = post_data.getlist('schedule_time')
    ends = post_data.getlist('schedule_end')
    for i, (day, time) in enumerate(zip(days, times)):
        try:
            d = int(day)
            if 0 <= d <= 6 and time:
                entry = {'day': d, 'time': time}
                end = ends[i] if i < len(ends) else ''
                if end:
                    entry['end'] = end
                schedule.append(entry)
        except (ValueError, TypeError):
            pass
    return schedule


class ClassListView(OrgAdminMixin, ListView):
    template_name = 'classes/list.html'
    context_object_name = 'classes'

    def get_queryset(self):
        return (
            Class.objects.filter(organisation=self.org)
            .prefetch_related('enrolments', 'coaches')
            .order_by('name')
        )


class ClassCreateView(OrgAdminMixin, View):
    def get(self, request, org_slug):
        form = _class_form_class()()
        return render(request, 'classes/form.html', {
            'org': self.org, 'org_membership': self.org_membership,
            'form': form, 'title': 'Add class', 'days': DAYS, 'days_json': DAYS_JSON, 'schedule': [],
        })

    def post(self, request, org_slug):
        FormClass = _class_form_class()
        form = FormClass(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organisation = self.org
            obj.schedule = _parse_schedule(request.POST)
            obj.save()
            messages.success(request, f'"{obj.name}" created.')
            return redirect('class_detail', org_slug=self.org.slug, pk=obj.pk)
        return render(request, 'classes/form.html', {
            'org': self.org, 'org_membership': self.org_membership,
            'form': form, 'title': 'Add class', 'days': DAYS, 'days_json': DAYS_JSON,
            'schedule': _parse_schedule(request.POST),
        })


class ClassUpdateView(OrgAdminMixin, View):
    def get_class(self, pk):
        return get_object_or_404(Class, pk=pk, organisation=self.org)

    def get(self, request, org_slug, pk):
        cls = self.get_class(pk)
        form = _class_form_class()(instance=cls)
        return render(request, 'classes/form.html', {
            'org': self.org, 'org_membership': self.org_membership,
            'form': form, 'title': f'Edit {cls.name}',
            'days': DAYS, 'days_json': DAYS_JSON, 'schedule': cls.schedule or [], 'cls': cls,
        })

    def post(self, request, org_slug, pk):
        cls = self.get_class(pk)
        FormClass = _class_form_class()
        form = FormClass(request.POST, instance=cls)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.schedule = _parse_schedule(request.POST)
            obj.save()
            messages.success(request, f'"{obj.name}" updated.')
            return redirect('class_detail', org_slug=self.org.slug, pk=obj.pk)
        return render(request, 'classes/form.html', {
            'org': self.org, 'org_membership': self.org_membership,
            'form': form, 'title': f'Edit {cls.name}',
            'days': DAYS, 'days_json': DAYS_JSON, 'schedule': _parse_schedule(request.POST), 'cls': cls,
        })


class ClassDetailView(OrgAdminMixin, DetailView):
    template_name = 'classes/detail.html'
    context_object_name = 'cls'

    def get_object(self):
        return get_object_or_404(Class, pk=self.kwargs['pk'], organisation=self.org)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrolled_ids = list(self.object.enrolments.values_list('member_id', flat=True))
        context['enrolled'] = (
            Member.objects.filter(pk__in=enrolled_ids)
            .order_by('name')
        )
        context['available'] = (
            Member.objects.filter(organisation=self.org, is_active=True)
            .exclude(pk__in=enrolled_ids)
            .order_by('name')
        )
        context['coaches'] = self.object.coaches.select_related('user')
        context['sessions'] = self.object.sessions.order_by('-date')[:10]
        context['days'] = DAYS
        return context


class EnrolMemberView(OrgAdminMixin, View):
    def post(self, request, org_slug, pk):
        cls = get_object_or_404(Class, pk=pk, organisation=self.org)
        member = get_object_or_404(Member, pk=request.POST.get('member_id'), organisation=self.org)
        ClassMember.objects.get_or_create(assigned_class=cls, member=member)
        messages.success(request, f'{member.name} enrolled.')
        return redirect('class_detail', org_slug=self.org.slug, pk=cls.pk)


class UnenrolMemberView(OrgAdminMixin, View):
    def post(self, request, org_slug, pk, member_pk):
        cls = get_object_or_404(Class, pk=pk, organisation=self.org)
        member = get_object_or_404(Member, pk=member_pk, organisation=self.org)
        ClassMember.objects.filter(assigned_class=cls, member=member).delete()
        messages.success(request, f'{member.name} removed.')
        return redirect('class_detail', org_slug=self.org.slug, pk=cls.pk)


class GenerateSessionsView(OrgAdminMixin, View):
    def post(self, request, org_slug, pk):
        cls = get_object_or_404(Class, pk=pk, organisation=self.org)
        if not cls.schedule:
            messages.warning(request, 'This class has no schedule set.')
            return redirect('class_detail', org_slug=self.org.slug, pk=cls.pk)

        try:
            weeks = max(1, min(int(request.POST.get('weeks', 8)), 52))
        except (ValueError, TypeError):
            weeks = 8

        from_date = date.today()
        to_date = from_date + timedelta(weeks=weeks)
        created = 0
        current = from_date
        while current < to_date:
            for entry in cls.schedule:
                if current.weekday() == entry['day']:
                    _, was_new = Session.objects.get_or_create(assigned_class=cls, date=current)
                    if was_new:
                        created += 1
            current += timedelta(days=1)

        messages.success(request, f'{created} session{"s" if created != 1 else ""} generated.')
        return redirect('class_detail', org_slug=self.org.slug, pk=cls.pk)


class AttendanceRegisterView(OrgAdminMixin, View):
    def _get_objects(self, pk, session_pk):
        cls = get_object_or_404(Class, pk=pk, organisation=self.org)
        session = get_object_or_404(Session, pk=session_pk, assigned_class=cls)
        return cls, session

    def get(self, request, org_slug, pk, session_pk):
        cls, session = self._get_objects(pk, session_pk)
        enrolled = (
            ClassMember.objects.filter(assigned_class=cls)
            .select_related('member')
            .order_by('member__name')
        )
        present_ids = set(
            Attendance.objects.filter(session=session, present=True)
            .values_list('member_id', flat=True)
        )
        return render(request, 'classes/register.html', {
            'org': self.org,
            'org_membership': self.org_membership,
            'cls': cls,
            'session': session,
            'enrolled': enrolled,
            'present_ids': present_ids,
        })

    def post(self, request, org_slug, pk, session_pk):
        cls, session = self._get_objects(pk, session_pk)
        enrolled = ClassMember.objects.filter(assigned_class=cls).select_related('member')
        present_ids = {int(x) for x in request.POST.getlist('present')}

        for cm in enrolled:
            Attendance.objects.update_or_create(
                session=session,
                member=cm.member,
                defaults={'present': cm.member.pk in present_ids},
            )

        session.notes = request.POST.get('notes', session.notes)
        session.save(update_fields=['notes'])

        messages.success(request, f'Register saved for {session.date:%d %b %Y}.')
        return redirect('session_register', org_slug=self.org.slug, pk=cls.pk, session_pk=session.pk)
