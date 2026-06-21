from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from organisations.models import Organisation
from .models import MemberApplication


class SignupView(View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organisation, slug=org_slug)
        return render(request, 'members/signup.html', {'org': org})

    def post(self, request, org_slug):
        org = get_object_or_404(Organisation, slug=org_slug)
        name = request.POST.get('name', '').strip()
        errors = []
        if not name:
            errors.append('Name is required.')
        if errors:
            return render(request, 'members/signup.html', {
                'org': org, 'errors': errors, 'data': request.POST,
            })

        dob_raw = request.POST.get('date_of_birth', '').strip()
        dob = None
        if dob_raw:
            from datetime import date
            try:
                dob = date.fromisoformat(dob_raw)
            except ValueError:
                pass

        MemberApplication.objects.create(
            organisation=org,
            name=name,
            date_of_birth=dob,
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            guardian_name=request.POST.get('guardian_name', '').strip(),
            guardian_email=request.POST.get('guardian_email', '').strip(),
            guardian_phone=request.POST.get('guardian_phone', '').strip(),
            notes=request.POST.get('notes', '').strip(),
        )
        return render(request, 'members/signup_done.html', {'org': org})
