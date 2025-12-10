from app import models
import json


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_owner_creates_manager(client, db_session, create_user, get_token):
    owner = create_user(phone="owner1", password="pass1", role=models.Role.OWNER)
    token = get_token(owner.phone, "pass1")

    payload = {"first_name": "Mgr", "last_name": "One", "phone_number": "mgr1", "password": "mgrpass", "role": "MANAGER"}
    resp = client.post("/users/create", json=payload, headers=auth_header(token))
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("status") == "success"


def test_manager_creates_user(client, db_session, create_user, get_token):
    manager = create_user(phone="mgr2", password="m2pass", role=models.Role.MANAGER)
    token = get_token(manager.phone, "m2pass")

    payload = {"first_name": "User", "last_name": "One", "phone_number": "user1", "password": "userpass", "role": "JESTER"}
    resp = client.post("/users/create", json=payload, headers=auth_header(token))
    assert resp.status_code == 201


def test_user_cannot_create_manager(client, db_session, create_user, get_token):
    user = create_user(phone="plainuser", password="u1", role=models.Role.JESTER)
    token = get_token(user.phone, "u1")

    payload = {"first_name": "Attempt", "last_name": "", "phone_number": "attempt_mgr", "password": "x", "role": "MANAGER"}
    resp = client.post("/users/create", json=payload, headers=auth_header(token))
    assert resp.status_code == 403


def test_manager_cannot_create_manager(client, db_session, create_user, get_token):
    manager = create_user(phone="mgr3", password="m3", role=models.Role.MANAGER)
    token = get_token(manager.phone, "m3")

    payload = {"first_name": "NewMgr", "last_name": "", "phone_number": "new_mgr", "password": "x", "role": "MANAGER"}
    resp = client.post("/users/create", json=payload, headers=auth_header(token))
    assert resp.status_code == 403
