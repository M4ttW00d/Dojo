from django.db import models
from django.contrib.auth.models import User
from members.models import Member


class Document(models.Model):
    class Category(models.TextChoices):
        CONSENT = 'consent', 'Consent form'
        MEDICAL = 'medical', 'Medical'
        WAIVER = 'waiver', 'Waiver'
        MEMBERSHIP = 'membership', 'Membership agreement'
        OTHER = 'other', 'Other'

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} — {self.name}"

    class Meta:
        ordering = ['-uploaded_at']
