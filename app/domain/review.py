"""
리뷰 도메인 객체 (엔티티)

DB를 쓰지 않으므로 값만 가진 평범한 @dataclass다.
필드 이름은 파이썬 관례대로 snake_case로 적고, JSON의 camelCase는 DTO(schemas/review.py)가 맡는다.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Review:
    # 리뷰 번호(PK). 새 리뷰는 0으로 만들고, ReviewRepository가 저장할 때 1, 2, 3 ... 번호를 붙인다.
    review_id: int
    # 손님 이름
    customer_name: str
    # 별점 (1 ~ 5)
    rating: int
    # 리뷰 내용
    content: str
    # 작성 시각. 값을 주지 않으면 객체를 만드는 순간의 현재 시각이 들어간다.
    created_at: datetime = field(default_factory=datetime.now)
