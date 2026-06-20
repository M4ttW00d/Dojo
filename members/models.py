import secrets
from django.db import models
from organisations.models import Organisation


def generate_token():
    return secrets.token_urlsafe(32)


class Member(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='club_members')
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    joined_date = models.DateField(null=True, blank=True)
    custom_field_values = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Guardian(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='guardians')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    relationship = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} (guardian of {self.member})"


class CustomField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = 'text', 'Text'
        DATE = 'date', 'Date'
        SELECT = 'select', 'Select'
        BOOLEAN = 'boolean', 'Boolean'

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='custom_fields')
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    options = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.organisation} — {self.name}"

    class Meta:
        ordering = ['organisation', 'order', 'name']
