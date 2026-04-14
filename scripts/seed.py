import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.security import get_password_hash


def seed_db():
    db: Session = SessionLocal()
    try:
        # Check if seed user already exists
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("Seeding user...")
            user = User(
                id=uuid.uuid4(),
                name="Test User",
                email="test@example.com",
                password=get_password_hash("password123"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            print("User already exists, skipping...")

        # Create project
        project = db.query(Project).filter(Project.name == "Main Project").first()
        if not project:
            print("Seeding project...")
            project = Project(
                id=uuid.uuid4(),
                name="Main Project",
                description="This is the primary project for testing.",
                owner_id=user.id,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        else:
            print("Project already exists, skipping...")

        # Create tasks
        existing_count = db.query(Task).filter(Task.project_id == project.id).count()
        if existing_count == 0:
            print("Seeding tasks...")
            tasks = [
                Task(
                    id=uuid.uuid4(),
                    title="Setup Environment",
                    description="Configure the project environment and database.",
                    status=TaskStatus.DONE,
                    priority=TaskPriority.HIGH,
                    project_id=project.id,
                    creator_id=user.id,
                    assignee_id=user.id,
                ),
                Task(
                    id=uuid.uuid4(),
                    title="Implement Auth",
                    description="Build JWT based registration and login.",
                    status=TaskStatus.IN_PROGRESS,
                    priority=TaskPriority.MEDIUM,
                    project_id=project.id,
                    creator_id=user.id,
                    assignee_id=user.id,
                ),
                Task(
                    id=uuid.uuid4(),
                    title="Write Documentation",
                    description="Write the README and API guide.",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.LOW,
                    project_id=project.id,
                    creator_id=user.id,
                ),
            ]
            db.add_all(tasks)
            db.commit()
            print("Seeding complete.")
        else:
            print("Tasks already exist, skipping...")

    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
