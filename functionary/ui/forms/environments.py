from django.forms import ModelForm

from core.models import EnvironmentUserRole


class EnvUserRoleForm(ModelForm):
    class Meta:
        model = EnvironmentUserRole
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove empty label from role field, which is a TypedChoiceField
        self.fields["role"].choices = self.fields["role"].choices[1:]
