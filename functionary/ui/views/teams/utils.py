from typing import Union

from core.models import Team, TeamUserRole, User


def get_users(team: Team) -> list[dict]:
    """Get user data about all the users in the team

    Get a list of metadata about the users that are currently
    assigned to the given team.

    Args:
        team: The team to get the users from

    Returns:
        user_details: A list of dictionaries that contains information
            about the user and their relationship with the team
    """
    team_user_roles: list[TeamUserRole] = team.user_roles.all()

    user_details = []
    for team_user_role in team_user_roles:
        user_element = {}
        user_element["user"] = team_user_role.user
        user_element["role"] = team_user_role.role
        user_element["team_user_role_id"] = team_user_role.id
        user_details.append(user_element)
    return user_details


def get_user_from_username(username: str) -> Union[User, None]:
    """Simple helper method for getting a User from the Username

    Retrieve a User object from the given username if it exists.
    If a User does not exist with the given username, returns None.

    Args:
        username: A string of the username

    Returns:
        User or None: Returns the corresponding User object if a user
            with that username exists. Else, returns None
    """
    return User.objects.filter(username=username).first()
