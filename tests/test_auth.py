from app import models


def test_login_success(client, db_session, create_user, get_token):
    # arrange
    phone = "auth_test_user"
    password = "secret123"
    user = create_user(phone=phone, password=password, role=models.Role.JESTER)

    # act
    data = {"phone_number": phone, "password": password}
    resp = client.post("/auth/signin", json=data)

    # assert
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "token" in body["data"]


def test_login_incorrect_password(client, db_session, create_user):
    phone = "auth_bad_user"
    password = "rightpass"
    create_user(phone=phone, password=password, role=models.Role.JESTER)

    data = {"phone_number": phone, "password": "wrongpass"}
    resp = client.post("/auth/signin", json=data)
    assert resp.status_code == 401
