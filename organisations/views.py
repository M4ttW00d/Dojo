from datetime import date, timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.views.generic import ListView, TemplateView
from auditlog.models import LogEntry
from dojo.mixins import OrgAdminMixin, OrgMixin


class DashboardView(OrgMixin, TemplateView):
    template_name = 'org/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from classes.models import Attendance, ClassMember, Session
        from members.models import Member

        today = date.today()
        week_end = today + timedelta(days=7)

        active_members = self.org.club_members.filter(is_active=True)
        member_count = active_members.count()

        enrolled_ids = ClassMember.objects.filter(
            assigned_class__organisation=self.org
        ).values_list('member_id', flat=True)
        unenrolled_count = active_members.exclude(pk__in=enrolled_ids).count()

        upcoming_sessions = (
            Session.objects
            .filter(assigned_class__organisation=self.org, date__gte=today, date__lte=week_end)
            .select_related('assigned_class')
            .order_by('date')
        )

        sessions_with_status = []
        for session in upcoming_sessions:
            taken = Attendance.objects.filter(session=session).exists()
            enrolled = ClassMember.objects.filter(assigned_class=session.assigned_class).count()
            present = Attendance.objects.filter(session=session, present=True).count() if taken else None
            sessions_with_status.append({
                'session': session,
                'taken': taken,
                'enrolled': enrolled,
                'present': present,
            })

        context.update({
            'member_count': member_count,
            'class_count': self.org.classes.count(),
            'unenrolled_count': unenrolled_count,
            'sessions_this_week': len(upcoming_sessions),
            'upcoming': sessions_with_status,
            'today': today,
        })
        return context


class AuditLogView(OrgAdminMixin, ListView):
    template_name = 'org/audit_log.html'
    context_object_name = 'entries'
    paginate_by = 50

    def get_queryset(self):
        from members.models import Guardian, Member
        from classes.models import Attendance, Class, ClassCoach, ClassMember, Session

        member_pks = list(
            Member.objects.filter(organisation=self.org).values_list('pk', flat=True)
        )
        class_pks = list(
            Class.objects.filter(organisation=self.org).values_list('pk', flat=True)
        )
        guardian_pks = list(
            Guardian.objects.filter(member__organisation=self.org).values_list('pk', flat=True)
        )
        session_pks = list(
            Session.objects.filter(assigned_class__organisation=self.org).values_list('pk', flat=True)
        )
        attendance_pks = list(
            Attendance.objects.filter(session__assigned_class__organisation=self.org).values_list('pk', flat=True)
        )
        classmember_pks = list(
            ClassMember.objects.filter(assigned_class__organisation=self.org).values_list('pk', flat=True)
        )
        classcoach_pks = list(
            ClassCoach.objects.filter(assigned_class__organisation=self.org).values_list('pk', flat=True)
        )

        def ct(model):
            return ContentType.objects.get_for_model(model)

        q = (
            Q(content_type=ct(Member), object_id__in=member_pks)
            | Q(content_type=ct(Guardian), object_id__in=guardian_pks)
            | Q(content_type=ct(Class), object_id__in=class_pks)
            | Q(content_type=ct(Session), object_id__in=session_pks)
            | Q(content_type=ct(Attendance), object_id__in=attendance_pks)
            | Q(content_type=ct(ClassMember), object_id__in=classmember_pks)
            | Q(content_type=ct(ClassCoach), object_id__in=classcoach_pks)
        )

        return (
            LogEntry.objects.filter(q)
            .select_related('actor', 'content_type')
            .order_by('-timestamp')
        )
