from django.forms import ModelForm

from core.models import TeamUserRole


class TeamUserRoleForm(ModelForm):
    class Meta:
        model = TeamUserRole
        fields = "__all__"
