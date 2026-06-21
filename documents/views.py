from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.http import FileResponse, Http404

from dojo.mixins import OrgAdminMixin
from members.models import Member
from .models import Document


class DocumentUploadView(OrgAdminMixin, View):
    def post(self, request, org_slug, member_pk):
        member = get_object_or_404(Member, pk=member_pk, organisation=self.org)
        f = request.FILES.get('file')
        name = request.POST.get('name', '').strip() or (f.name if f else '')
        category = request.POST.get('category', Document.Category.OTHER)
        notes = request.POST.get('notes', '').strip()
        if not f:
            messages.error(request, 'No file selected.')
            return redirect('member_detail', org_slug=org_slug, pk=member_pk)
        Document.objects.create(
            member=member,
            name=name,
            category=category,
            file=f,
            uploaded_by=request.user,
            notes=notes,
        )
        messages.success(request, f'"{name}" uploaded.')
        return redirect('member_detail', org_slug=org_slug, pk=member_pk)


class DocumentDeleteView(OrgAdminMixin, View):
    def post(self, request, org_slug, member_pk, pk):
        member = get_object_or_404(Member, pk=member_pk, organisation=self.org)
        doc = get_object_or_404(Document, pk=pk, member=member)
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('member_detail', org_slug=org_slug, pk=member_pk)


class DocumentDownloadView(OrgAdminMixin, View):
    def get(self, request, org_slug, member_pk, pk):
        member = get_object_or_404(Member, pk=member_pk, organisation=self.org)
        doc = get_object_or_404(Document, pk=pk, member=member)
        try:
            return FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.name)
        except FileNotFoundError:
            raise Http404
