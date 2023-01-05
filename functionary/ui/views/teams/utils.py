from core.models import Team, TeamUserRole


def get_users(team: Team) -> list[dict]:
    team_user_roles: list[TeamUserRole] = team.user_roles.all()

    user_details = []
    for team_user_role in team_user_roles:
        user_element = {}
        user_element["user"] = team_user_role.user
        user_element["role"] = team_user_role.role
        user_details.append(user_element)
    return user_details
