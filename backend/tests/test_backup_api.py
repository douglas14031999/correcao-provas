import os
import sys
import io
import json
import zipfile

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_backup_security_and_flow():
    # 1. Login as admin first to create professor user
    res_admin = client.post("/api/auth/login", json={"username": "admin", "password": "semed2026"})
    assert res_admin.status_code == 200
    adm_token = res_admin.json()["token"]

    client.post(
        "/api/users",
        headers={"X-Auth-Token": adm_token},
        json={
            "name": "Professor Teste",
            "username": "prof_backup_test",
            "password": "senha_prof_123",
            "role": "professor"
        }
    )

    # 2. Login as Professor
    prof_res = client.post("/api/auth/login", json={"username": "prof_backup_test", "password": "senha_prof_123"})
    assert prof_res.status_code == 200
    prof_token = prof_res.json()["token"]

    # 3. Non-admin (Professor) must be rejected with 403
    export_prof = client.get("/api/backup/export", headers={"X-Auth-Token": prof_token})
    assert export_prof.status_code == 403, f"Expected 403, got {export_prof.status_code}"

    stats_prof = client.get("/api/backup/stats", headers={"X-Auth-Token": prof_token})
    assert stats_prof.status_code == 403, f"Expected 403, got {stats_prof.status_code}"

    # 4. Login as Admin again to get active admin session
    res_admin2 = client.post("/api/auth/login", json={"username": "admin", "password": "semed2026"})
    assert res_admin2.status_code == 200
    admin_token = res_admin2.json()["token"]

    # 2. Admin can get stats
    stats_admin = client.get("/api/backup/stats", headers={"X-Auth-Token": admin_token})
    assert stats_admin.status_code == 200, f"Stats failed: {stats_admin.status_code} - {stats_admin.text}"
    stats_data = stats_admin.json()
    assert "schools" in stats_data
    assert "users" in stats_data
    assert stats_data["users"] >= 1
    print(f"Stats OK: {stats_data}")

    # 3. Admin can export backup zip
    export_admin = client.get("/api/backup/export", headers={"X-Auth-Token": admin_token})
    assert export_admin.status_code == 200
    assert export_admin.headers["content-type"] == "application/zip"
    zip_bytes = export_admin.content
    assert len(zip_bytes) > 100

    # 4. Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "database.json" in namelist
        assert "manifest.json" in namelist

        db_json = json.loads(zf.read("database.json").decode("utf-8"))
        assert "users" in db_json
        assert "schools" in db_json
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["version"] == "1.0.0"
        print(f"Export ZIP validated! Tables: {list(db_json.keys())}")

    # 5. Admin can import/restore backup zip
    files = {
        "file": ("backup_test.zip", io.BytesIO(zip_bytes), "application/zip")
    }
    import_res = client.post("/api/backup/import", headers={"X-Auth-Token": admin_token}, files=files)
    assert import_res.status_code == 200, f"Import failed: {import_res.text}"
    import_data = import_res.json()
    assert import_data["success"] is True
    assert "stats" in import_data
    print(f"Import Restore OK: {import_data['message']}")

if __name__ == "__main__":
    test_backup_security_and_flow()
    print("\n[SUCCESS] Todos os testes de Backup (Exportação, Importação e RBAC) passaram com sucesso!")
