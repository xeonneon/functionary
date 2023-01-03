from django.forms import ModelForm

from core.models import EnvironmentUserRole


class EnvUserRoleForm(ModelForm):
    class Meta:
        model = EnvironmentUserRole
        fields = "__all__"
