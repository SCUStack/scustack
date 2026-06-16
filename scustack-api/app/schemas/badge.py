from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


BADGE_META: dict[str, dict] = {
    'first_upload': {'label': '初次上传', 'description': '上传第一份通过审核的资料', 'color': '#3B82F6'},
    'prolific_10': {'label': '高产作者', 'description': '累计上传 10 份资料', 'color': '#8B5CF6'},
    'prolific_50': {'label': '资料达人', 'description': '累计上传 50 份资料', 'color': '#7C3AED'},
    'prolific_100': {'label': '资料大师', 'description': '累计上传 100 份资料', 'color': '#5B21B6'},
    'popular_100': {'label': '小有名气', 'description': '单份资料下载量突破 100', 'color': '#F59E0B'},
    'popular_1000': {'label': '万人迷', 'description': '单份资料下载量突破 1000', 'color': '#EA580C'},
    'popular_10000': {'label': '超级明星', 'description': '单份资料下载量突破 10000', 'color': '#DC2626'},
    'selfless': {'label': '活雷锋', 'description': '上传资料被收藏夹收录 10 次', 'color': '#10B981'},
    'college_contributor': {'label': '学院贡献者', 'description': '所在学院上传量 Top 3', 'color': '#06B6D4'},
    'continuous_3': {'label': '连续贡献', 'description': '连续 3 个月有上传', 'color': '#F97316'},
    'wish_fulfiller': {'label': '心愿达成者', 'description': '上传资料满足了心愿单需求', 'color': '#EC4899'},
}

BADGE_TYPE = list(BADGE_META.keys())


class BadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    badge_type: str
    label: str
    description: str
    color: str
    awarded_at: datetime


class BadgeListResponse(BaseModel):
    badges: list[BadgeResponse]
    total: int
