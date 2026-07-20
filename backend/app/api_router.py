from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.analytics.router import router as analytics_admin_router
from app.modules.analytics.public_router import router as public_router
from app.modules.auth.router import router as auth_router
from app.modules.availability.router import router as availability_router
from app.modules.bookings.router import router as bookings_router
from app.modules.bookmarks.router import router as bookmarks_router
from app.modules.chat.router import router as chat_router
from app.modules.feedback.router import router as feedback_router
from app.modules.mentors.router import router as mentors_router
from app.modules.notifications.router import router as notifications_router
from app.modules.payments.router import router as payments_router
from app.modules.questions.router import router as questions_router
from app.modules.reports.router import router as reports_router
from app.modules.resources.router import router as resources_router
from app.modules.search.router import router as search_router
from app.modules.students.router import router as students_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.universities.router import admin_router as universities_admin_router
from app.modules.universities.router import router as universities_router
from app.modules.verification.router import router as verification_router
from app.modules.video_sessions.router import router as video_sessions_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(mentors_router)
api_router.include_router(verification_router)
api_router.include_router(universities_router)
api_router.include_router(universities_admin_router)
api_router.include_router(search_router)
api_router.include_router(availability_router)
api_router.include_router(bookings_router)
api_router.include_router(payments_router)
api_router.include_router(video_sessions_router)
api_router.include_router(chat_router)
api_router.include_router(questions_router)
api_router.include_router(resources_router)
api_router.include_router(notifications_router)
api_router.include_router(bookmarks_router)
api_router.include_router(reports_router)
api_router.include_router(admin_router)
api_router.include_router(analytics_admin_router)
api_router.include_router(public_router)
api_router.include_router(subscriptions_router)
api_router.include_router(feedback_router)
