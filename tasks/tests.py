
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Task


class TaskAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="kirtana",
            password="TestPass123!"
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="TestPass456!"
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Learn Django REST Framework",
            description="Practice API testing",
            priority="High",
            status="Pending"
        )

        # Authenticate as the first user using a JWT access token.
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    # ---------- Registration and Authentication ----------

    def test_user_can_register(self):
        data = {
            "username": "newuser",
            "password": "NewPass123!"
        }

        response = self.client.post(
            "/api/register/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_can_obtain_jwt_tokens(self):
        # Remove existing authentication to test the login endpoint itself.
        self.client.credentials()

        response = self.client.post(
            "/api/token/",
            {
                "username": "kirtana",
                "password": "TestPass123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # ---------- List and Create ----------

    def test_user_can_list_own_tasks(self):
        response = self.client.get("/api/tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["title"],
            "Learn Django REST Framework"
        )

    def test_user_can_create_task(self):
        data = {
            "title": "Write automated tests",
            "description": "Test task creation",
            "priority": "Medium",
            "status": "Pending"
        }

        response = self.client.post(
            "/api/tasks/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["title"], "Write automated tests"
        )

        created_task = Task.objects.get(id=response.data["id"])
        self.assertEqual(created_task.user, self.user)

    # ---------- Retrieve ----------

    def test_user_can_retrieve_own_task(self):
        response = self.client.get(f"/api/tasks/{self.task.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["title"],
            "Learn Django REST Framework"
        )
        self.assertEqual(response.data["priority"], "High")

    # ---------- Update (PUT) ----------

    def test_user_can_update_own_task(self):
        data = {
            "title": "Updated task title",
            "description": "Updated description",
            "priority": "Low",
            "status": "In Progress",
            "due_date": None
        }

        response = self.client.put(
            f"/api/tasks/{self.task.id}/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated task title")
        self.assertEqual(self.task.description, "Updated description")
        self.assertEqual(self.task.priority, "Low")
        self.assertEqual(self.task.status, "In Progress")

    # ---------- Partial Update (PATCH) ----------

    def test_user_can_partially_update_own_task(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"status": "Completed"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "Completed")
        # Other fields should remain unchanged.
        self.assertEqual(
            self.task.title, "Learn Django REST Framework"
        )

    # ---------- Delete ----------

    def test_user_can_delete_own_task(self):
        task_id = self.task.id

        response = self.client.delete(f"/api/tasks/{task_id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    # ---------- Authorization and Security ----------

    def test_unauthenticated_user_cannot_list_tasks(self):
        self.client.credentials()

        response = self.client.get("/api/tasks/")

        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_user_cannot_retrieve_another_users_task(self):
        other_task = Task.objects.create(
            user=self.other_user,
            title="Private task"
        )

        response = self.client.get(f"/api/tasks/{other_task.id}/")

        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_user_cannot_update_another_users_task(self):
        other_task = Task.objects.create(
            user=self.other_user,
            title="Private task"
        )

        response = self.client.patch(
            f"/api/tasks/{other_task.id}/",
            {"title": "Trying to change this"},
            format="json"
        )

        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )

        other_task.refresh_from_db()
        self.assertEqual(other_task.title, "Private task")

    def test_user_cannot_delete_another_users_task(self):
        other_task = Task.objects.create(
            user=self.other_user,
            title="Private task"
        )

        response = self.client.delete(f"/api/tasks/{other_task.id}/")

        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertTrue(
            Task.objects.filter(id=other_task.id).exists()
        )
