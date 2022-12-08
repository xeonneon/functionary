from typing import Union

from django.db.models import QuerySet

from core.models import Environment, EnvironmentUserRole, TeamUserRole, User


def get_user_env_role(user: User, environment: Environment) -> EnvironmentUserRole:
    env_user_role = EnvironmentUserRole.objects.filter(
        user=user, environment=environment
    ).first()
    if not env_user_role:
        env_user_role = TeamUserRole.objects.get(user=user, team=environment.team)
    return env_user_role


def get_users(env: Environment) -> list[Union[TeamUserRole, EnvironmentUserRole]]:
    """Get list of users who are part of the environment

    Get a list of users who are part of the environment, including users
    who are inheriting their read access from the team of that environment.
    Users who have inherited their access will have an inherited attribute
    attached to their TeamUserRole object.

    Args:
        env: The environment to get users from

    Returns:
        team_members: A list containing all the users who have
            access to the environment.
    """
    env_members, env_member_ids = get_env_members(env)
    return [user for user in env_members]


def get_env_members(
    env: Environment,
) -> tuple[QuerySet[EnvironmentUserRole], dict[int, EnvironmentUserRole]]:
    """Get a QuerySet of all users in environment and dict of their IDs

    Return a QuerySet of all users in environment, along with a dictionary
    that has all of the user IDs

    Args:
        env: The environment to get the users from

    Returns:
        members: A list of all members of the environment
        ids:  Dictionary with all the user IDs
    """
    members: list[EnvironmentUserRole] = [user for user in env.user_roles.all()]
    ids = {}
    for user in members:
        ids[user.user.id] = user
    return members, ids


def get_team_members(
    env: Environment,
) -> tuple[QuerySet[TeamUserRole], dict[int, TeamUserRole]]:
    """Get a QuerySet of all users in the env->team and their IDs

    Return a QuerySet of all users on the team that owns the environment
    along with a dictionary that has all of the user IDs

    Args:
        env: The environment to get the users from

    Returns:
        members: A list of all members of the env->team
        ids:  Dictionary with all the user IDs
    """
    members: list[TeamUserRole] = [user for user in env.team.user_roles.all()]
    ids = {}
    for user in members:
        ids[user.user.id] = user
    return members, ids
