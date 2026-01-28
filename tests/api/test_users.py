from fastapi import status
from httpx import AsyncClient

from app.auth.services import TokenService
from tests.types import CreateUserCallable


async def test_successful_get_me(
    create_user: CreateUserCallable, token_service: TokenService, client: AsyncClient
) -> None:
    user = await create_user()

    access_token = token_service.create_access_token(user.id)

    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.get(url="/users/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()

    assert response_data["id"] == str(user.id)
    assert response_data["email"] == user.email
