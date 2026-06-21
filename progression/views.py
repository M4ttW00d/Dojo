from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from dojo.mixins import OrgAdminMixin
from .models import ProgressionStage


class ProgressionSettingsView(OrgAdminMixin, View):
    def get(self, request, org_slug):
        stages = ProgressionStage.objects.filter(organisation=self.org)
        return render(request, 'progression/settings.html', {
            'org': self.org,
            'org_membership': self.org_membership,
            'stages': stages,
        })


class AddStageView(OrgAdminMixin, View):
    def post(self, request, org_slug):
        name = request.POST.get('name', '').strip()
        colour = request.POST.get('colour', '').strip()
        if not name:
            messages.error(request, 'Stage name is required.')
            return redirect('progression_settings', org_slug=self.org.slug)
        if ProgressionStage.objects.filter(organisation=self.org, name=name).exists():
            messages.error(request, f'A stage named "{name}" already exists.')
            return redirect('progression_settings', org_slug=self.org.slug)
        order = ProgressionStage.objects.filter(organisation=self.org).count()
        ProgressionStage.objects.create(
            organisation=self.org,
            name=name,
            colour=colour,
            order=order,
        )
        messages.success(request, f'"{name}" added.')
        return redirect('progression_settings', org_slug=self.org.slug)


class DeleteStageView(OrgAdminMixin, View):
    def post(self, request, org_slug, pk):
        stage = get_object_or_404(ProgressionStage, pk=pk, organisation=self.org)
        if stage.achievements.exists():
            messages.error(request, f'Cannot delete "{stage.name}" — members have been awarded this grade.')
            return redirect('progression_settings', org_slug=self.org.slug)
        stage.delete()
        messages.success(request, f'"{stage.name}" deleted.')
        return redirect('progression_settings', org_slug=self.org.slug)


class MoveStageView(OrgAdminMixin, View):
    def post(self, request, org_slug, pk):
        stage = get_object_or_404(ProgressionStage, pk=pk, organisation=self.org)
        direction = request.POST.get('direction')
        stages = list(ProgressionStage.objects.filter(organisation=self.org).order_by('order'))
        idx = next((i for i, s in enumerate(stages) if s.pk == stage.pk), None)
        if idx is None:
            return redirect('progression_settings', org_slug=self.org.slug)
        if direction == 'up' and idx > 0:
            stages[idx], stages[idx - 1] = stages[idx - 1], stages[idx]
        elif direction == 'down' and idx < len(stages) - 1:
            stages[idx], stages[idx + 1] = stages[idx + 1], stages[idx]
        for i, s in enumerate(stages):
            s.order = i
            s.save(update_fields=['order'])
        return redirect('progression_settings', org_slug=self.org.slug)
