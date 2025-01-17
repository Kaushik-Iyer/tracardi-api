from uuid import uuid4

from app.api.auth.user_db import TokenDb
from tracardi.domain.user import User


def test_user_set_delete():
    token2user = TokenDb()
    user = User(id=str(uuid4()),
                password="pass",
                full_name="Name",
                email="test@test.pl",
                roles=['admin']
                )
    token = token2user.set(user)
    user_cache = token2user.get(token)
    assert user_cache.email == user.email
    assert user_cache.id == user.id

    token2user.delete(token)

    user_cache = token2user.get(token)
    assert user_cache is None
