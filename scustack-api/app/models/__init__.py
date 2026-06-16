from app.core.database import Base
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.calendar import AcademicCalendar
from app.models.college import College
from app.models.account_deletion import AccountDeletion
from app.models.collection import Collection, CollectionItem
from app.models.comment import Comment
from app.models.content_blocklist import ContentBlocklist
from app.models.copyright_complaint import CopyrightComplaint
from app.models.correction import CorrectionSuggestion
from app.models.course import Course
from app.models.material import Material, MaterialVersion
from app.models.notification import Notification
from app.models.report import Report
from app.models.review_log import ReviewLog
from app.models.user import RefreshToken, User
from app.models.user_badge import UserBadge
from app.models.user_consent import UserConsent
from app.models.wish import Wish, WishVote

__all__ = [
    'Base', 'User', 'RefreshToken', 'UserBadge', 'College', 'Course',
    'Material', 'MaterialVersion', 'Bookmark', 'CorrectionSuggestion', 'Notification',
    'ReviewLog', 'Report', 'AuditLog', 'AcademicCalendar',
    'Wish', 'WishVote', 'CopyrightComplaint', 'AccountDeletion',
    'Collection', 'CollectionItem', 'Comment', 'ContentBlocklist',
]
