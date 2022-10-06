import pytest

from core.models import Team


class TestModelSaveHookMixin:
    """Tests for ModelSaveHookMixin

    NOTE: The included tests use the Team model, as it is a known, simple case where
    the ModelSaveHookMixin gets used. If a test specific app and models are created
    in the future, these tests should be updated to use an independent model instead.
    """

    @pytest.fixture
    def save_hook_mocks(self, mocker):
        mocker.patch("core.models.Team.pre_create")
        mocker.patch("core.models.Team.post_create")
        mocker.patch("core.models.Team.pre_save")
        mocker.patch("core.models.Team.post_save")

    @pytest.mark.django_db
    @pytest.mark.usefixtures("save_hook_mocks")
    def test_all_hooks_called_on_create(self):
        """All of the create and save hooks are called during creation"""
        instance = Team()
        instance.save()

        assert instance.pre_create.call_count == 1
        assert instance.post_create.call_count == 1
        assert instance.pre_save.call_count == 1
        assert instance.post_save.call_count == 1

    @pytest.mark.django_db
    @pytest.mark.usefixtures("save_hook_mocks")
    def test_save_after_creation_does_not_call_create_hooks(self):
        """After creation, subsequent save() calls do not call the create hooks"""
        instance = Team()
        instance.save()  # initial creation
        instance.save()  # subsequent save

        assert instance.pre_create.call_count == 1
        assert instance.post_create.call_count == 1
        assert instance.pre_save.call_count == 2
        assert instance.post_save.call_count == 2
