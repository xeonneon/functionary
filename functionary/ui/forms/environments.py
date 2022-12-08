from django.forms import ChoiceField, Form, ModelChoiceField

from core.auth import Role
from core.models import Environment, User

ROLE_CHOICES = [(role.name, role.value) for role in Role]


class EnvForm(Form):
    environment = ModelChoiceField(queryset=Environment.objects.all(), required=True)
    user = ModelChoiceField(queryset=User.objects.all(), required=True)
    role = ChoiceField(choices=ROLE_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_classes()

    def _setup_field_classes(self):
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "input is-medium"})
