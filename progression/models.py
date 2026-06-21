from django.db import models
from organisations.models import Organisation
from members.models import Member


class ProgressionStage(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='progression_stages')
    name = models.CharField(max_length=255)
    colour = models.CharField(max_length=7, blank=True, help_text='Hex colour, e.g. #FF0000')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.organisation} — {self.name}"

    class Meta:
        ordering = ['organisation', 'order', 'name']
        unique_together = ('organisation', 'name')


class MemberProgression(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='progressions')
    stage = models.ForeignKey(ProgressionStage, on_delete=models.CASCADE, related_name='achievements')
    achieved_date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} — {self.stage.name} ({self.achieved_date})"

    class Meta:
        ordering = ['-achieved_date']
