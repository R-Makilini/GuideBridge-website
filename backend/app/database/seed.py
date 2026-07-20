import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.core.constants import AuthProvider, UserRole, UserStatus, VerificationStatus
from app.core.security import hash_password
from app.database import model_registry  # noqa: F401
from app.database.session import SessionLocal
from app.modules.admin.models import SystemSetting
from app.modules.mentors.models import MentorProfile
from app.modules.students.models import StudentProfile
from app.modules.subscriptions.models import SubscriptionPlan, SubscriptionPlanCode
from app.modules.universities.models import Degree, Department, ExpertiseTag, Faculty, Stream, Subject, University
from app.modules.users.models import User


def get_or_create(db, model, defaults=None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed():
    db = SessionLocal()
    try:
      
        admin, created = get_or_create(
            db, User, email=settings.SUPER_ADMIN_EMAIL,
            defaults=dict(
                full_name="GuideBridge Super Admin",
                hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                is_email_verified=True,
            ),
        )
        print(f"{'Created' if created else 'Exists'}: Super Admin ({admin.email})")

        
        uni, _ = get_or_create(db, University, name="University of Colombo", defaults=dict(short_name="UOC", city="Colombo"))
        get_or_create(db, University, name="University of Moratuwa", defaults=dict(short_name="UOM", city="Moratuwa"))
        get_or_create(db, University, name="University of Peradeniya", defaults=dict(short_name="UOP", city="Peradeniya"))

        faculty, _ = get_or_create(db, Faculty, university_id=uni.id, name="Faculty of Science")
        department, _ = get_or_create(db, Department, faculty_id=faculty.id, name="Department of Computer Science")
        degree, _ = get_or_create(db, Degree, department_id=department.id, name="BSc (Hons) in Computer Science")

      
        streams = {}
        for name in ["Physical Science", "Biological Science", "Commerce", "Arts", "Technology"]:
            streams[name], _ = get_or_create(db, Stream, name=name)

        subjects_data = [
            ("Combined Mathematics", "Physical Science"),
            ("Physics", "Physical Science"),
            ("Chemistry", "Physical Science"),
            ("Biology", "Biological Science"),
            ("Accounting", "Commerce"),
            ("Business Studies", "Commerce"),
            ("Economics", "Commerce"),
            ("English", None),
            ("ICT", "Technology"),
        ]
        subject_objs = {}
        for name, stream_name in subjects_data:
            stream_id = streams[stream_name].id if stream_name else None
            subj, _ = get_or_create(db, Subject, name=name, defaults=dict(stream_id=stream_id))
            subject_objs[name] = subj

        for tag_name in ["University Admissions", "Career Guidance", "Scholarship Advice", "Research Writing", "Interview Prep"]:
            get_or_create(db, ExpertiseTag, name=tag_name)

        db.flush()

        
        student_user, created = get_or_create(
            db, User, email="student.demo@guidebridge.lk",
            defaults=dict(
                full_name="Sanduni Perera",
                hashed_password=hash_password("Student123!"),
                role=UserRole.STUDENT,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                is_email_verified=True,
            ),
        )
        print(f"{'Created' if created else 'Exists'}: Demo Student ({student_user.email})")

        if created:
            db.add(
                StudentProfile(
                    user_id=student_user.id,
                    school="Royal College",
                    grade="A/L",
                    stream_id=streams["Physical Science"].id,
                    district="Colombo",
                    preferred_language="en",
                )
            )

        
        mentor_user, created = get_or_create(
            db, User, email="mentor.demo@guidebridge.lk",
            defaults=dict(
                full_name="Kasun Fernando",
                hashed_password=hash_password("Mentor123!"),
                role=UserRole.MENTOR,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                is_email_verified=True,
            ),
        )
        print(f"{'Created' if created else 'Exists'}: Demo Mentor ({mentor_user.email})")

        if created:
            db.add(
                MentorProfile(
                    user_id=mentor_user.id,
                    university_id=uni.id,
                    faculty_id=faculty.id,
                    department_id=department.id,
                    degree_id=degree.id,
                    academic_year=3,
                    biography="Final-year Computer Science undergraduate passionate about helping A/L students with Combined Maths and university admissions.",
                    skills="Combined Mathematics, ICT, Python",
                    verification_status=VerificationStatus.APPROVED,
                    is_publicly_visible=True,
                    helpful_score=12,
                    completed_session_count=8,
                    average_rating=4.7,
                )
            )

        get_or_create(
            db, SubscriptionPlan, code=SubscriptionPlanCode.FREE,
            defaults=dict(name="Free", price_monthly=0, free_chat_limit=10, can_access_premium_resources=False),
        )
        get_or_create(
            db, SubscriptionPlan, code=SubscriptionPlanCode.PRO,
            defaults=dict(name="Pro", price_monthly=990, free_chat_limit=50, can_access_premium_resources=False),
        )
        get_or_create(
            db, SubscriptionPlan, code=SubscriptionPlanCode.PREMIUM,
            defaults=dict(name="Premium", price_monthly=2490, free_chat_limit=999999, can_access_premium_resources=True),
        )

      
        get_or_create(
            db, SystemSetting, key="platform_commission_percent",
            defaults=dict(value=str(settings.DEFAULT_PLATFORM_COMMISSION_PERCENT), description="Platform commission % taken from each paid booking."),
        )
        get_or_create(
            db, SystemSetting, key="free_chat_limit",
            defaults=dict(value=str(settings.DEFAULT_FREE_CHAT_LIMIT), description="Number of free messages a student can send per conversation."),
        )

        db.commit()
        print("\nSeed completed successfully.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
