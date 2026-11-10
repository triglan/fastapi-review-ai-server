"""
리뷰 도메인 객체 (엔티티)

DB를 쓰지 않으므로 값만 가진 평범한 @dataclass다.
필드 이름은 파이썬 관례대로 snake_case로 적고, JSON의 camelCase는 DTO(schemas/review.py)가 맡는다.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Review:
    review_id: int
    customer_name: str
    rating: int
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    reply: str | None = None
