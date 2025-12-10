import pytest
from app import models


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_package_transfer_and_revoke(client, db_session, create_user, get_token):
    # create owner and manager
    owner = create_user(phone="owner_fin", password="opass", role=models.Role.OWNER, remaining_balance=100.0)
    manager = create_user(phone="mgr_fin", password="mpass", role=models.Role.MANAGER, remaining_balance=0.0)

    owner_token = get_token(owner.phone, "opass")

    # transfer 30 using new transactions API
    payload = {"receiver_id": manager.id, "amount": 30}
    resp = client.post("/transactions/send-package", json=payload, headers=auth_header(owner_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["sender_new_balance"] == "UNLIMITED"
    assert body["data"]["receiver_new_balance"] == pytest.approx(30.0)

    # find the package transaction
    tx = db_session.query(models.PackageTransaction).filter(models.PackageTransaction.sender_id == owner.id).order_by(models.PackageTransaction.id.desc()).first()
    assert tx is not None

    # revoke
    rev_payload = {"transaction_id": tx.id}
    resp2 = client.post("/api/management/package/revoke", json=rev_payload, headers=auth_header(owner_token))
    assert resp2.status_code == 200


def test_revoke_fails_when_receiver_spent(client, db_session, create_user, get_token):
    # owner -> receiver transfer
    owner = create_user(phone="owner_r", password="op", role=models.Role.OWNER, remaining_balance=100.0)
    receiver = create_user(phone="recv_r", password="rp", role=models.Role.JESTER, remaining_balance=0.0)
    owner_token = get_token(owner.phone, "op")

    payload = {"receiver_id": receiver.id, "amount": 50}
    resp = client.post("/transactions/send-package", json=payload, headers=auth_header(owner_token))
    assert resp.status_code == 200

    tx = db_session.query(models.PackageTransaction).filter(models.PackageTransaction.sender_id == owner.id).order_by(models.PackageTransaction.id.desc()).first()
    assert tx is not None

    # simulate receiver spending the money (make balance < tx amount)
    recv = db_session.query(models.User).filter(models.User.id == receiver.id).one()
    recv.wallet_balance = 10.0
    db_session.add(recv)
    db_session.commit()

    # attempt revoke using existing revoke endpoint
    rev_payload = {"transaction_id": tx.id}
    resp2 = client.post("/api/management/package/revoke", json=rev_payload, headers=auth_header(owner_token))
    assert resp2.status_code == 400
