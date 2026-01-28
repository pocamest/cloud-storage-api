from fastapi import status
from httpx import AsyncClient

from app.auth.services import TokenService
from tests.types import CreateUserCallable


async def test_successful_login(
    create_user: CreateUserCallable, client: AsyncClient, token_service: TokenService
) -> None:
    email = "test@example.com"
    password = "test_password"
    user = await create_user(email=email, password=password)

    user_data = {"email": email.upper(), "password": password}

    response = await client.post(url="/auth/login", json=user_data)

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()

    assert response_data["user"]["id"] == str(user.id)
    assert response_data["user"]["email"] == user.email

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]

    assert token_service.verify_access_token(access_token) == user.id
    assert await token_service.verify_refresh_token(refresh_token) == user.id
