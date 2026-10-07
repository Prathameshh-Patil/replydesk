def test_login_with_correct_password_returns_token(client, staff):
    r = client.post(
        "/auth/login", data={"username": "asha@example.com", "password": "correct-horse"}
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_email_is_case_insensitive(client, staff):
    r = client.post(
        "/auth/login", data={"username": "ASHA@example.com", "password": "correct-horse"}
    )
    assert r.status_code == 200


def test_login_with_wrong_password_fails(client, staff):
    r = client.post("/auth/login", data={"username": "asha@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_with_unknown_email_fails_the_same_way(client, staff):
    r = client.post("/auth/login", data={"username": "nobody@example.com", "password": "x"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect email or password"


def test_password_is_stored_hashed(staff):
    assert staff.password_hash != "correct-horse"
    assert staff.password_hash.startswith("$2b$")  # bcrypt


def test_me_returns_logged_in_user(client, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "Asha", "email": "asha@example.com"}


def test_me_without_token_is_rejected(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_forged_token_is_rejected(client, staff):
    import jwt

    forged = jwt.encode(
        {"sub": "1"}, "not-the-real-secret-but-just-as-long-as-one", algorithm="HS256"
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401
