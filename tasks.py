from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from limiter import limiter
from models import Category, Task, db
from validators import parse_json_request, validate_task_payload

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _get_user_task(task_id, user_id):
    return Task.query.filter_by(
        id=task_id,
        user_id=user_id,
        is_deleted=False
    ).first()


# -------------------------
# CREATE TASK
# -------------------------
@tasks_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
def create_task():
    user_id = int(get_jwt_identity())
    data = validate_task_payload(parse_json_request(request))

    category_id = data.get("category_id")
    if category_id is not None:
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if not category:
            return {"error": "category not found"}, 404

    task = Task(
        title=data["title"],
        priority=data.get("priority", "MEDIUM"),
        due_date=data.get("due_date"),
        category_id=category_id,
        user_id=user_id
    )

    db.session.add(task)
    db.session.commit()

    return {"message": "task created", "task": task.to_dict()}, 201


# -------------------------
# GET TASKS
# -------------------------
@tasks_bp.route("", methods=["GET"])
@jwt_required()
def get_tasks():
    user_id = int(get_jwt_identity())

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 5, type=int)
    completed = request.args.get("completed")
    search = request.args.get("search")

    query = Task.query.filter_by(user_id=user_id, is_deleted=False)

    if completed is not None:
        query = query.filter(Task.completed == (completed.lower() == "true"))

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    pagination = query.order_by(Task.created_at.desc()).paginate(
        page=page,
        per_page=limit
    )

    return {
        "page": page,
        "limit": limit,
        "total_tasks": pagination.total,
        "tasks": [task.to_dict() for task in pagination.items]
    }


# -------------------------
# TASK STATS
# -------------------------
@tasks_bp.route("/stats", methods=["GET"])
@jwt_required()
def task_stats():
    user_id = int(get_jwt_identity())

    total = Task.query.filter_by(user_id=user_id, is_deleted=False).count()
    completed = Task.query.filter_by(
        user_id=user_id,
        completed=True,
        is_deleted=False
    ).count()
    pending = Task.query.filter_by(
        user_id=user_id,
        completed=False,
        is_deleted=False
    ).count()

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending
    }


# -------------------------
# GET SINGLE TASK
# -------------------------
@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    user_id = int(get_jwt_identity())
    task = _get_user_task(task_id, user_id)

    if not task:
        return {"error": "task not found"}, 404

    return task.to_dict()


# -------------------------
# UPDATE TASK
# -------------------------
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    user_id = int(get_jwt_identity())
    task = _get_user_task(task_id, user_id)

    if not task:
        return {"error": "task not found"}, 404

    data = validate_task_payload(parse_json_request(request), partial=True)

    if "category_id" in data and data["category_id"] is not None:
        category = Category.query.filter_by(
            id=data["category_id"],
            user_id=user_id
        ).first()
        if not category:
            return {"error": "category not found"}, 404

    for field, value in data.items():
        setattr(task, field, value)

    db.session.commit()

    return {"message": "task updated", "task": task.to_dict()}


# -------------------------
# TOGGLE TASK
# -------------------------
@tasks_bp.route("/<int:task_id>/toggle", methods=["PATCH"])
@jwt_required()
def toggle_task(task_id):
    user_id = int(get_jwt_identity())
    task = _get_user_task(task_id, user_id)

    if not task:
        return {"error": "task not found"}, 404

    task.completed = not task.completed
    db.session.commit()

    return {
        "message": "task toggled",
        "completed": task.completed
    }


# -------------------------
# COMPLETE ALL TASKS
# -------------------------
@tasks_bp.route("/complete-all", methods=["PATCH"])
@jwt_required()
def complete_all_tasks():
    user_id = int(get_jwt_identity())

    updated_count = Task.query.filter_by(
        user_id=user_id,
        completed=False,
        is_deleted=False
    ).update({"completed": True})

    db.session.commit()

    return {
        "message": "tasks marked as completed",
        "updated_tasks": updated_count
    }


# -------------------------
# CLEAR COMPLETED TASKS
# -------------------------
@tasks_bp.route("/clear-completed", methods=["DELETE"])
@jwt_required()
def clear_completed_tasks():
    user_id = int(get_jwt_identity())

    deleted_count = Task.query.filter_by(
        user_id=user_id,
        completed=True,
        is_deleted=False
    ).delete()

    db.session.commit()

    return {
        "message": "completed tasks deleted",
        "deleted_tasks": deleted_count
    }


# -------------------------
# DELETE TASK
# -------------------------
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())
    task = _get_user_task(task_id, user_id)

    if not task:
        return {"error": "task not found"}, 404

    db.session.delete(task)
    db.session.commit()

    return {"message": "task deleted"}
