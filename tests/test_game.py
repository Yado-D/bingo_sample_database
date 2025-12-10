from app import models


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_betting_deducts_balance(client, db_session, create_user, get_token):
    user = create_user(phone="gambler1", password="betpass", role=models.Role.JESTER, remaining_balance=100.0)
    token = get_token(user.phone, "betpass")

    payload = {"selected_card_numbers": [1, 2, 3], "bet_amount_per_card": 10.0}
    resp = client.post("/api/game/play", json=payload, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "game_session_id" in body
    assert body["new_balance"] == 70.0


def test_game_win_increases_balance(client, db_session, create_user, get_token):
    user = create_user(phone="gambler2", password="winpass", role=models.Role.JESTER, remaining_balance=100.0)
    token = get_token(user.phone, "winpass")

    # place a bet of 20 (2 cards * 10)
    payload = {"selected_card_numbers": [1, 2], "bet_amount_per_card": 10.0}
    resp = client.post("/api/game/play", json=payload, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    session_id = body["game_session_id"]
    new_balance_after_bet = body["new_balance"]

    # post result as WIN with win_amount 50
    result_payload = {"game_session_id": session_id, "status": "WIN", "win_amount": 50}
    res = client.post("/api/game/result", json=result_payload, headers=auth_header(token))
    assert res.status_code == 200
    res_body = res.json()
    assert res_body["new_balance"] == new_balance_after_bet + 50


def test_insufficient_funds_for_bet(client, db_session, create_user, get_token):
    user = create_user(phone="poor_guy", password="nop", role=models.Role.JESTER, remaining_balance=0.0)
    token = get_token(user.phone, "nop")

    payload = {"selected_card_numbers": [1], "bet_amount_per_card": 10.0}
    resp = client.post("/api/game/play", json=payload, headers=auth_header(token))
    assert resp.status_code == 402


def test_game_end_deducts_jester_balance(client, db_session, create_user, get_token):
    # create a jester and a game session
    user = create_user(phone="jester_end", password="endpass", role=models.Role.JESTER, remaining_balance=1000.0)
    token = get_token(user.phone, "endpass")

    # create a game session directly in DB
    from app import models
    session = models.GameSession(owner_id=user.id, bet_amount_per_card=10.0, total_bet=100.0, selected_cards=[1,2,3], status="FINISHED", total_pot=500.0, house_cut=100.0)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    payload = {"game_id": f"GAME-{session.id}", "winner_cartela_id": "CARD-05"}
    resp = client.post("/game/end", json=payload, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["winner_payout"] == pytest.approx(400.0)
