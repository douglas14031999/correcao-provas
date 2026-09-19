import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.services.database import (
    init_db,
    get_connection,
    create_user,
    get_user_by_username,
    get_user_session
)
from app.api.auth import hash_password

class TestMultiUserSessions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

        # Create or ensure two test users
        if not get_user_by_username("user_alpha"):
            create_user(
                name="Usuario Alpha",
                username="user_alpha",
                email="alpha@test.com",
                role="admin",
                password_hash=hash_password("senha123"),
                is_active=1
            )
        if not get_user_by_username("user_beta"):
            create_user(
                name="Usuario Beta",
                username="user_beta",
                email="beta@test.com",
                role="professor",
                password_hash=hash_password("senha456"),
                is_active=1
            )

    def test_multi_user_concurrent_sessions(self):
        """Tests that two different users can be logged in concurrently without dropping each other."""
        # 1. Login User Alpha
        res_a = self.client.post("/api/auth/login", json={"username": "user_alpha", "password": "senha123"})
        self.assertEqual(res_a.status_code, 200)
        token_a = res_a.json()["token"]

        # 2. Login User Beta
        res_b = self.client.post("/api/auth/login", json={"username": "user_beta", "password": "senha456"})
        self.assertEqual(res_b.status_code, 200)
        token_b = res_b.json()["token"]

        # Tokens must be distinct
        self.assertNotEqual(token_a, token_b)

        # 3. User Alpha accesses /me -> MUST succeed and return Alpha
        me_a = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(me_a.status_code, 200)
        self.assertEqual(me_a.json()["user"]["username"], "user_alpha")

        # 4. User Beta accesses /me -> MUST succeed and return Beta
        me_b = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(me_b.status_code, 200)
        self.assertEqual(me_b.json()["user"]["username"], "user_beta")

    def test_same_user_multi_device_sessions(self):
        """Tests that the same user logged in on PC and Mobile can use both concurrently."""
        # Login 1 (e.g. PC)
        res_pc = self.client.post("/api/auth/login", json={"username": "user_alpha", "password": "senha123"})
        self.assertEqual(res_pc.status_code, 200)
        token_pc = res_pc.json()["token"]

        # Login 2 (e.g. Smartphone)
        res_mob = self.client.post("/api/auth/login", json={"username": "user_alpha", "password": "senha123"})
        self.assertEqual(res_mob.status_code, 200)
        token_mob = res_mob.json()["token"]

        self.assertNotEqual(token_pc, token_mob)

        # Both tokens remain valid simultaneously
        check_pc = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_pc}"})
        self.assertEqual(check_pc.status_code, 200)

        check_mob = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_mob}"})
        self.assertEqual(check_mob.status_code, 200)

    def test_single_device_logout_isolation(self):
        """Tests that logging out from one device does NOT disconnect other devices or other users."""
        res_dev1 = self.client.post("/api/auth/login", json={"username": "user_alpha", "password": "senha123"})
        token_dev1 = res_dev1.json()["token"]

        res_dev2 = self.client.post("/api/auth/login", json={"username": "user_alpha", "password": "senha123"})
        token_dev2 = res_dev2.json()["token"]

        # Logout Dev 1
        logout_res = self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_dev1}"})
        self.assertEqual(logout_res.status_code, 200)

        # Dev 1 token is revoked -> 401
        check_dev1 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_dev1}"})
        self.assertEqual(check_dev1.status_code, 401)

        # Dev 2 token is STILL VALID -> 200
        check_dev2 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_dev2}"})
        self.assertEqual(check_dev2.status_code, 200)
        self.assertEqual(check_dev2.json()["user"]["username"], "user_alpha")

if __name__ == "__main__":
    unittest.main()
