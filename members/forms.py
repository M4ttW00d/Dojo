from django import forms
from django.forms import inlineformset_factory
from .models import Guardian, Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'name', 'date_of_birth', 'email', 'phone',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_2_name', 'emergency_contact_2_phone',
            'joined_date', 'is_active',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'joined_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['name'].widget.attrs['autofocus'] = True


class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['name', 'relationship', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['name'].required = False


GuardianFormSet = inlineformset_factory(
    Member, Guardian,
    form=GuardianForm,
    extra=1,
    can_delete=True,
)
