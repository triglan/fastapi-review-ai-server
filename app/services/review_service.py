"""
리뷰 서비스 : 리뷰 등록, 조회

- 생성자로 ReviewRepository를 주입받는다. (객체를 만들어 넣어 주는 일은 dependencies.py가 한다)
- FastAPI를 import하지 않는다. DTO를 받아 DTO를 반환하고, 실패하면 사용자 정의 예외를 던질 뿐이다.
  예외를 404 응답으로 바꾸는 일은 core/exceptions.py의 처리기가 한다.
"""

from app.core.exceptions import ReviewNotFoundError
from app.domain.review import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreateRequest, ReviewResponse


class ReviewService:

    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    def register_review(self, request: ReviewCreateRequest) -> ReviewResponse:
        """새 리뷰를 등록한다. 값의 조건(별점 1~5 등)은 FastAPI가 요청 DTO로 이미 검사했다."""

        # 1. 요청 DTO로 엔티티를 만든다. 번호는 아직 없으므로 0이다.
        review = Review(
            review_id=0,
            customer_name=request.customer_name,
            rating=request.rating,
            content=request.content,
        )

        # 2. 저장한다. 저장소가 번호를 붙인다.
        saved = self.repository.save(review)

        # 3. 응답 DTO로 바꿔서 반환한다.
        return ReviewResponse.from_review(saved)

    def find_review(self, review_id: int) -> ReviewResponse:
        """리뷰 번호로 리뷰 하나를 조회한다. 없으면 ReviewNotFoundError(→ 404)를 던진다."""

        review = self.repository.find_by_id(review_id)

        # 없으면 예외를 던진다. (Java의 orElseThrow())
        if review is None:
            raise ReviewNotFoundError(review_id)

        return ReviewResponse.from_review(review)
