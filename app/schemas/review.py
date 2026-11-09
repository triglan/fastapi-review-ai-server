"""
리뷰 요청, 응답 DTO와 답글 응답 DTO

- 요청 DTO에 Field 조건을 적어 두면, 조건에 맞지 않는 요청은 핸들러를 실행하지 않고 422로 응답한다.
- 엔티티(Review)를 그대로 내보내지 않고 응답 DTO로 바꿔서 응답한다.
"""

from datetime import datetime

from pydantic import Field

from app.domain.review import Review
from app.schemas.base import CamelModel


class ReviewCreateRequest(CamelModel):
    """리뷰 등록 요청 DTO. POST /api/reviews의 요청 본문이다."""

    # 손님 이름 : 1글자 이상 20글자 이하
    customer_name: str = Field(min_length=1, max_length=20)
    # 별점 : 1 이상 5 이하 (6을 보내면 422)
    rating: int = Field(ge=1, le=5)
    # 리뷰 내용 : 1글자 이상 1000글자 이하
    content: str = Field(min_length=1, max_length=1000)


class ReviewResponse(CamelModel):
    """리뷰 응답 DTO. 등록과 조회 API가 이 형태로 응답한다."""

    review_id: int
    customer_name: str
    rating: int
    content: str
    created_at: datetime

    @classmethod
    def from_review(cls, review: Review) -> ReviewResponse:
        """Review 엔티티를 ReviewResponse로 바꾼다."""
        return cls(
            review_id=review.review_id,
            customer_name=review.customer_name,
            rating=review.rating,
            content=review.content,
            created_at=review.created_at,
        )


class ReplyResponse(CamelModel):
    """사장님 답글 초안 응답 DTO. POST /api/reviews/{review_id}/reply의 응답이다."""

    # 어떤 리뷰에 대한 답글인지
    review_id: int
    # LLM이 만든 답글 초안
    reply: str
    # 응답한 모델 이름. 가짜 LLM 클라이언트면 "fake-llm"
    model: str
