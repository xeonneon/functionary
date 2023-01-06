from django.forms import ModelForm, ValidationError

from core.models import EnvironmentUserRole


class EnvUserRoleForm(ModelForm):
    class Meta:
        model = EnvironmentUserRole
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove empty label from role field, which is a TypedChoiceField
        self.fields["role"].choices = self.fields["role"].choices[1:]

    def clean(self) -> dict:
        """Override clean method to include User DNE error message"""
        cleaned_data = super().clean()
        if not cleaned_data.get("user"):
            self.add_error(
                "user", ValidationError("User does not exist.", code="invalid")
            )
        return cleaned_data
