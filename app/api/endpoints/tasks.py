from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskUpdate

router = APIRouter()


@router.get("/projects/{project_id}/tasks", response_model=list[TaskSchema])
def list_project_tasks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
    status: TaskStatus | None = None,
    assignee: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    # Access check: owner or participant
    is_owner = project.owner_id == current_user.id
    is_participant = (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.assignee_id == current_user.id)
        .first()
        is not None
    )
    if not is_owner and not is_participant:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    skip = (page - 1) * limit
    query = db.query(Task).filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if assignee:
        query = query.filter(Task.assignee_id == assignee)

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
    task_in: TaskCreate,
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    if not task_in.title or not task_in.title.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation failed",
                "fields": {"title": "is required"},
            },
        )

    # Owner or participant can create tasks
    if project.owner_id != current_user.id:
        is_participant = (
            db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.assignee_id == current_user.id,
            )
            .first()
            is not None
        )
        if not is_participant:
            raise HTTPException(status_code=403, detail={"error": "forbidden"})

    task = Task(
        **task_in.model_dump(),
        project_id=project_id,
        creator_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskSchema)
def update_task(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: uuid.UUID,
    task_in: TaskUpdate,
) -> Any:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    project = db.query(Project).filter(Project.id == task.project_id).first()

    is_owner = project.owner_id == current_user.id if project else False
    is_assignee = task.assignee_id == current_user.id
    is_creator = task.creator_id == current_user.id

    if not is_owner and not is_assignee and not is_creator:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", response_model=None)
def delete_task(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: uuid.UUID,
) -> Response:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    project = db.query(Project).filter(Project.id == task.project_id).first()

    is_owner = project.owner_id == current_user.id if project else False
    is_creator = task.creator_id == current_user.id

    if not is_owner and not is_creator:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
