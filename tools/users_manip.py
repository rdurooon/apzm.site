from tools.db import update_user_password as db_update_user_password, user_exists as db_user_exists


def update_user_password(email: str, new_password: str) -> bool:
    return db_update_user_password(email, new_password)


def user_exists(email: str) -> bool:
    return db_user_exists(email)

