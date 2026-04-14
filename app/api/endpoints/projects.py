from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.project import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    ProjectDetail,
)

router = APIRouter()


@router.get("", response_model=list[ProjectSchema])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List projects the current user owns or has tasks in."""
    skip = (page - 1) * limit

    owned_ids = db.query(Project.id).filter(Project.owner_id == current_user.id)
    assigned_ids = db.query(Task.project_id).filter(
        Task.assignee_id == current_user.id
    )
    all_ids = owned_ids.union(assigned_ids).subquery()

    projects = (
        db.query(Project)
        .filter(Project.id.in_(db.query(all_ids)))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.post("", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_in: ProjectCreate,
) -> Any:
    if not project_in.name or not project_in.name.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation failed",
                "fields": {"name": "is required"},
            },
        )

    project = Project(
        **project_in.model_dump(),
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    is_owner = project.owner_id == current_user.id
    is_assigned = (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.assignee_id == current_user.id)
        .first()
        is not None
    )

    if not is_owner and not is_assigned:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    return project


@router.patch("/{project_id}", response_model=ProjectSchema)
def update_project(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=None)
def delete_project(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
) -> Response:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/stats")
def get_project_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: uuid.UUID,
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    status_counts = (
        db.query(Task.status, func.count(Task.id))
        .filter(Task.project_id == project_id)
        .group_by(Task.status)
        .all()
    )

    assignee_counts = (
        db.query(Task.assignee_id, func.count(Task.id))
        .filter(Task.project_id == project_id)
        .group_by(Task.assignee_id)
        .all()
    )

    return {
        "status_counts": {s: c for s, c in status_counts},
        "assignee_counts": {
            str(a) if a else "unassigned": c for a, c in assignee_counts
        },
    }
