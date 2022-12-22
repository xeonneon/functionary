from django.forms import ChoiceField, Form, ModelChoiceField

from core.auth import Role
from core.models import Environment, User

ROLE_CHOICES = [(role.name, role.value) for role in Role]


class EnvUserRoleForm(Form):
    environment = ModelChoiceField(queryset=Environment.objects.all(), required=True)
    user = ModelChoiceField(queryset=User.objects.all(), required=True)
    role = ChoiceField(choices=ROLE_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
