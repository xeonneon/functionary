import pytest
from django.urls import reverse

from core.auth import Role
from core.models import EnvironmentUserRole, Team, TeamUserRole


@pytest.fixture
def team1():
    return Team.objects.create(name="team1")


@pytest.fixture
def team2():
    return Team.objects.create(name="team2")


@pytest.fixture
def team3():
    return Team.objects.create(name="team3")


@pytest.fixture()
def all_teams(team1, team2, team3):
    return [team1, team2, team3]


def test_list(admin_client, all_teams):
    """List all teams"""
    url = reverse("team-list")
    response = admin_client.get(url)

    assert len(all_teams) == len(response.data["results"])


def test_retrieve(admin_client, team1):
    """Retrieve a specific team"""
    url = f"{reverse('team-list')}{team1.id}/"
    response = admin_client.get(url)

    assert response.data["name"] == team1.name


def test_list_filters_based_on_assigned_roles(
    client, django_user_model, team1, team2, team3
):
    """List should only show Teams on which the user has an assigned role"""
    user = django_user_model.objects.create(username="testuser", password="password")

    TeamUserRole.objects.create(user=user, team=team1, role=Role.DEVELOPER.value)
    EnvironmentUserRole.objects.create(
        user=user,
        environment=team2.environments.get(name="default"),
        role=Role.DEVELOPER.value,
    )

    url = reverse("team-list")
    client.force_login(user)
    response = client.get(url)
    team_ids = [result["id"] for result in response.data["results"]]

    # Results should include only:
    #   - The Team the user has a role on (team1)
    #   - The Team of the environment the user a role on (team2)
    assert str(team1.id) in team_ids
    assert str(team2.id) in team_ids
    assert str(team3.id) not in team_ids
