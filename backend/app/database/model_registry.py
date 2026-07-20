"""
Central import hub so every SQLAlchemy model is registered on Base.metadata
before Alembic autogenerate or create_all() runs.
"""
from app.modules.users.models import (  
    User, UserSession, RefreshToken, EmailVerificationToken, PasswordResetToken,
)
from app.modules.students.models import StudentProfile  
from app.modules.universities.models import (  
    University, Faculty, Department, Degree, Stream, Subject, ExpertiseTag,
)
from app.modules.mentors.models import (  
    MentorProfile, MentorSubject, MentorExpertiseTag, MentorLanguage, MentorRegistrationProgress,
)
from app.modules.subscriptions.models import SubscriptionPlan, UserSubscription  
from app.modules.feedback.models import SessionFeedback  
from app.modules.verification.models import VerificationDocument, VerificationReview  
from app.modules.availability.models import AvailabilitySlot  
from app.modules.bookings.models import Booking, BookingStatusHistory  
from app.modules.payments.models import Payment, PaymentEvent, RefundRequest  
from app.modules.chat.models import Conversation, ConversationMember, Message, MessageAttachment  
from app.modules.questions.models import Question, QuestionAttachment, Answer, HelpfulVote  
from app.modules.resources.models import Resource, ResourceDownload  
from app.modules.video_sessions.models import VideoSession, SessionAttendance  
from app.modules.notifications.models import Notification  
from app.modules.bookmarks.models import Bookmark  
from app.modules.reports.models import Report, ReportEvidence, BlockedUser  
from app.modules.admin.models import AdminAction, AuditLog, SystemSetting  