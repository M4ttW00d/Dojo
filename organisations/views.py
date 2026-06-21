from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView
from auditlog.models import LogEntry
from dojo.mixins import OrgAdminMixin, OrgMixin
from .models import Organisation, OrganisationMember
from members.models import CustomField


class DashboardView(OrgMixin, TemplateView):
    template_name = 'org/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from classes.models import Attendance, ClassMember, Session
        from members.models import Member

        today = date.today()
        week_end = today + timedelta(days=7)

        is_admin = self.request.user.is_superuser or (
            self.org_membership and self.org_membership.role == 'org_admin'
        )

        active_members = self.org.club_members.filter(is_active=True)
        member_count = active_members.count()

        enrolled_ids = ClassMember.objects.filter(
            assigned_class__organisation=self.org
        ).values_list('member_id', flat=True)
        unenrolled_count = active_members.exclude(pk__in=enrolled_ids).count()

        sessions_qs = Session.objects.filter(
            assigned_class__organisation=self.org, date__gte=today, date__lte=week_end
        ).select_related('assigned_class').order_by('date')

        if not is_admin:
            sessions_qs = sessions_qs.filter(
                assigned_class__coaches__user=self.request.user
            )

        upcoming_sessions = sessions_qs

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

        from billing.models import Invoice, Payment
        from django.db.models import Sum, Q
        from members.models import MemberApplication

        first_of_month = today.replace(day=1)
        four_weeks_ago = today - timedelta(weeks=4)
        two_weeks_ago = today - timedelta(weeks=2)

        revenue_month = Payment.objects.filter(
            invoice__organisation=self.org,
            paid_at__date__gte=first_of_month,
        ).aggregate(t=Sum('amount'))['t'] or 0

        outstanding = Invoice.objects.filter(
            organisation=self.org, status=Invoice.Status.UNPAID
        ).aggregate(t=Sum('amount'))['t'] or 0

        new_members_month = active_members.filter(joined_date__gte=first_of_month).count()

        from classes.models import Attendance
        total_records = Attendance.objects.filter(
            session__assigned_class__organisation=self.org,
            session__date__gte=four_weeks_ago,
        ).count()
        present_records = Attendance.objects.filter(
            session__assigned_class__organisation=self.org,
            session__date__gte=four_weeks_ago,
            present=True,
        ).count()
        attendance_rate = round(present_records / total_records * 100) if total_records else None

        from django.db.models import Max
        at_risk = active_members.annotate(
            last_attended=Max(
                'attendance__session__date',
                filter=Q(attendance__present=True),
            )
        ).filter(
            Q(last_attended__lt=two_weeks_ago) | Q(last_attended__isnull=True)
        ).count()

        pending_applications = MemberApplication.objects.filter(
            organisation=self.org, status=MemberApplication.Status.PENDING
        ).count() if is_admin else 0

        context.update({
            'member_count': member_count,
            'class_count': self.org.classes.count(),
            'unenrolled_count': unenrolled_count,
            'sessions_this_week': len(upcoming_sessions),
            'upcoming': sessions_with_status,
            'today': today,
            'is_admin': is_admin,
            'revenue_month': revenue_month,
            'outstanding': outstanding,
            'new_members_month': new_members_month,
            'attendance_rate': attendance_rate,
            'at_risk_count': at_risk,
            'pending_applications': pending_applications,
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


class StaffListView(OrgAdminMixin, View):
    def get(self, request, org_slug):
        from django.shortcuts import render
        staff = (
            OrganisationMember.objects.filter(organisation=self.org)
            .select_related('user')
            .order_by('user__first_name', 'user__username')
        )
        return render(request, 'org/staff.html', {
            'org': self.org,
            'org_membership': self.org_membership,
            'staff': staff,
            'roles': OrganisationMember.Role.choices,
        })

    def post(self, request, org_slug):
        action = request.POST.get('action')

        if action == 'add':
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            password = request.POST.get('password', '').strip()
            role = request.POST.get('role', OrganisationMember.Role.COACH)

            if not username or not password:
                messages.error(request, 'Username and password are required.')
                return redirect('org_staff', org_slug=self.org.slug)

            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" is already taken.')
                return redirect('org_staff', org_slug=self.org.slug)

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            OrganisationMember.objects.create(user=user, organisation=self.org, role=role)
            messages.success(request, f'{user.get_full_name() or username} added as {role}.')

        elif action == 'change_role':
            member_pk = request.POST.get('member_pk')
            new_role = request.POST.get('role')
            om = get_object_or_404(OrganisationMember, pk=member_pk, organisation=self.org)
            if om.user == request.user:
                messages.error(request, "You can't change your own role.")
            else:
                om.role = new_role
                om.save(update_fields=['role'])
                messages.success(request, f'Role updated for {om.user.get_full_name() or om.user.username}.')

        elif action == 'remove':
            member_pk = request.POST.get('member_pk')
            om = get_object_or_404(OrganisationMember, pk=member_pk, organisation=self.org)
            if om.user == request.user:
                messages.error(request, "You can't remove yourself.")
            else:
                name = om.user.get_full_name() or om.user.username
                om.delete()
                messages.success(request, f'{name} removed from {self.org.name}.')

        return redirect('org_staff', org_slug=self.org.slug)


class TestEmailView(OrgAdminMixin, View):
    def post(self, request, org_slug):
        from django.core.mail import send_mail
        recipient = request.user.email
        if not recipient:
            messages.error(request, 'Your user account has no email address set — add one in the Django admin first.')
            return redirect('org_settings', org_slug=self.org.slug)
        try:
            send_mail(
                subject=f'Test email from {self.org.name} (Dojo)',
                message=f'This is a test email from Dojo to confirm your email settings are working.\n\n— {self.org.name}',
                from_email=None,
                recipient_list=[recipient],
            )
            messages.success(request, f'Test email sent to {recipient}.')
        except Exception as e:
            messages.error(request, f'Email failed: {e}')
        return redirect('org_settings', org_slug=self.org.slug)


class OrgSettingsView(OrgAdminMixin, View):
    template_name = 'org/settings.html'

    def get(self, request, org_slug):
        from django.shortcuts import render
        return render(request, self.template_name, {
            'org': self.org,
            'org_membership': self.org_membership,
        })

    def post(self, request, org_slug):
        from django.shortcuts import render
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        website = request.POST.get('website', '').strip()

        if not name:
            messages.error(request, 'Organisation name is required.')
            return render(request, self.template_name, {
                'org': self.org,
                'org_membership': self.org_membership,
            })

        self.org.name = name
        self.org.email = email
        self.org.phone = phone
        self.org.website = website
        self.org.save(update_fields=['name', 'email', 'phone', 'website'])
        messages.success(request, 'Settings saved.')
        return redirect('org_settings', org_slug=self.org.slug)


class CustomFieldSettingsView(OrgAdminMixin, View):
    def get(self, request, org_slug):
        from django.shortcuts import render
        from members.models import CustomField
        fields = CustomField.objects.filter(organisation=self.org)
        return render(request, 'org/custom_fields.html', {
            'org': self.org,
            'org_membership': self.org_membership,
            'fields': fields,
            'field_types': CustomField.FieldType.choices,
        })

    def post(self, request, org_slug):
        from django.shortcuts import render
        from members.models import CustomField
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            field_type = request.POST.get('field_type', 'text')
            options_raw = request.POST.get('options', '').strip()
            if name:
                options = [o.strip() for o in options_raw.splitlines() if o.strip()] if options_raw else []
                order = CustomField.objects.filter(organisation=self.org).count()
                CustomField.objects.create(
                    organisation=self.org,
                    name=name,
                    field_type=field_type,
                    options=options,
                    order=order,
                )
                messages.success(request, f'Field "{name}" added.')

        elif action == 'delete':
            field_pk = request.POST.get('field_pk')
            field = get_object_or_404(CustomField, pk=field_pk, organisation=self.org)
            field.delete()
            messages.success(request, f'Field "{field.name}" deleted.')

        return redirect('org_custom_fields', org_slug=self.org.slug)
