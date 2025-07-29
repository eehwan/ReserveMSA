import pytest
import httpx


# 사용자 생성 테스트
@pytest.mark.asyncio
async def test_create_user(client: httpx.AsyncClient):
    """
    새로운 사용자를 생성하는 API 엔드포인트를 테스트합니다.
    """
    response = await client.post(
        "/user/users/",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()

# 로그인 테스트
@pytest.mark.asyncio # 주석 해제
async def test_login_for_access_token(client: httpx.AsyncClient):
    """
    사용자 로그인 및 액세스 토큰 발급 API 엔드포인트를 테스트합니다.
    """
    # 사용자 생성
    response_create = await client.post(
        "/user/users/",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response_create.status_code == 201

    response = await client.post(
        "/user/auth/",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# 로그인 후 내 정보 조회 테스트
@pytest.mark.asyncio # 주석 해제
async def test_read_users_me(client: httpx.AsyncClient):
    """
    로그인한 사용자의 정보를 조회하는 API 엔드포인트를 테스트합니다.
    """
    # 사용자 생성
    response_create = await client.post(
        "/user/users/",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response_create.status_code == 201

    login_response = await client.post(
        "/user/auth/",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    token = login_response.json()["access_token"]
    response = await client.get(
        "/user/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()
