import os
import tempfile
import unittest

from app import create_app
from config import TestingConfig
from models import db


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        class LocalTestingConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db.name.replace(os.sep, '/')}"

        self.app = create_app(LocalTestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def register_user(self, name="Test User", email="test@example.com", password="secret123"):
        return self.client.post(
            "/auth/register",
            json={
                "name": name,
                "email": email,
                "password": password
            }
        )

    def login_user(self, email="test@example.com", password="secret123"):
        return self.client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

    def auth_headers(self):
        self.register_user()
        response = self.login_user()
        token = response.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_home_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Task Manager API", response.data)
        self.assertIn(b"API is live and responding", response.data)

    def test_register_and_login_flow(self):
        register_response = self.register_user()
        login_response = self.login_user()

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access_token", login_response.get_json())
        self.assertIn("refresh_token", login_response.get_json())

    def test_register_requires_valid_data(self):
        response = self.client.post(
            "/auth/register",
            json={
                "name": "A",
                "email": "bad-email",
                "password": "123"
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid request")

    def test_create_update_and_delete_task(self):
        headers = self.auth_headers()

        create_response = self.client.post(
            "/tasks",
            json={
                "title": "Prepare resume project",
                "priority": "high",
                "due_date": "2026-04-15"
            },
            headers=headers
        )

        self.assertEqual(create_response.status_code, 201)
        task = create_response.get_json()["task"]
        self.assertEqual(task["priority"], "HIGH")

        task_id = task["id"]

        update_response = self.client.put(
            f"/tasks/{task_id}",
            json={
                "title": "Prepare polished resume project",
                "completed": True
            },
            headers=headers
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(update_response.get_json()["task"]["completed"])

        delete_response = self.client.delete(f"/tasks/{task_id}", headers=headers)
        self.assertEqual(delete_response.status_code, 200)

        get_response = self.client.get(f"/tasks/{task_id}", headers=headers)
        self.assertEqual(get_response.status_code, 404)

    def test_task_bulk_endpoints(self):
        headers = self.auth_headers()

        self.client.post("/tasks", json={"title": "Task One"}, headers=headers)
        self.client.post("/tasks", json={"title": "Task Two"}, headers=headers)

        list_response = self.client.get("/tasks", headers=headers)
        tasks = list_response.get_json()["tasks"]
        task_id = tasks[0]["id"]

        toggle_response = self.client.patch(f"/tasks/{task_id}/toggle", headers=headers)
        self.assertEqual(toggle_response.status_code, 200)
        self.assertTrue(toggle_response.get_json()["completed"])

        complete_all_response = self.client.patch("/tasks/complete-all", headers=headers)
        self.assertEqual(complete_all_response.status_code, 200)

        stats_response = self.client.get("/tasks/stats", headers=headers)
        stats = stats_response.get_json()
        self.assertEqual(stats["total_tasks"], 2)
        self.assertEqual(stats["completed_tasks"], 2)

        clear_response = self.client.delete("/tasks/clear-completed", headers=headers)
        self.assertEqual(clear_response.status_code, 200)
        self.assertEqual(clear_response.get_json()["deleted_tasks"], 2)

    def test_protected_routes_require_token(self):
        response = self.client.get("/tasks")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "authorization required")


if __name__ == "__main__":
    unittest.main()
