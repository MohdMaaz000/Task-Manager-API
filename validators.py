import re
from datetime import datetime

from flask import request
from werkzeug.exceptions import BadRequest

ALLOWED_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_json_request(req):
    if not req.is_json:
        raise BadRequest("request must be json")

    data = req.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("invalid json body")

    return data


def validate_registration_payload(req):
    data = parse_json_request(req)

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name or not email or not password:
        raise BadRequest("name, email and password are required")

    if len(name) < 2 or len(name) > 120:
        raise BadRequest("name must be between 2 and 120 characters")

    if not EMAIL_PATTERN.match(email):
        raise BadRequest("email format is invalid")

    if len(password) < 8:
        raise BadRequest("password must be at least 8 characters long")

    return {
        "name": name,
        "email": email,
        "password": password,
    }


def validate_login_payload(req):
    data = parse_json_request(req)

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        raise BadRequest("email and password are required")

    if not EMAIL_PATTERN.match(email):
        raise BadRequest("email format is invalid")

    return {
        "email": email,
        "password": password,
    }


def validate_task_payload(data, partial=False):
    cleaned = {}

    if not partial or "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            raise BadRequest("title is required")
        if len(title) > 255:
            raise BadRequest("title must be 255 characters or fewer")
        cleaned["title"] = title

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            raise BadRequest("completed must be true or false")
        cleaned["completed"] = data["completed"]

    if "priority" in data:
        priority = str(data["priority"]).strip().upper()
        if priority not in ALLOWED_PRIORITIES:
            raise BadRequest("priority must be one of LOW, MEDIUM, HIGH")
        cleaned["priority"] = priority

    if "due_date" in data:
        due_date = data["due_date"]
        if due_date in (None, ""):
            cleaned["due_date"] = None
        else:
            try:
                cleaned["due_date"] = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise BadRequest("due_date must use YYYY-MM-DD format") from exc

    if "category_id" in data:
        category_id = data["category_id"]
        if category_id in (None, ""):
            cleaned["category_id"] = None
        else:
            try:
                cleaned["category_id"] = int(category_id)
            except (TypeError, ValueError) as exc:
                raise BadRequest("category_id must be an integer") from exc

    return cleaned
