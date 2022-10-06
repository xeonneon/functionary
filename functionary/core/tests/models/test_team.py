import pytest

from core.models import Environment, Team


@pytest.mark.django_db
def test_default_environment_created():
    """Creating a Team creates a corresponding default Environment"""
    team_name = "test"
    assert not Environment.objects.filter(team__name=team_name).exists()

    Team(name=team_name).save()
    assert Environment.objects.filter(team__name=team_name).exists()
