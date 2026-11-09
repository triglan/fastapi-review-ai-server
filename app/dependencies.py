"""
의존성 함수 (Spring의 빈 등록 + 생성자 주입 역할)

핸들러의 매개변수에 Depends(의존성 함수)를 적으면, 요청이 들어올 때마다 FastAPI가 그 함수를 호출해
반환값을 넣어 준다. 의존성 함수의 매개변수에도 Depends를 적을 수 있어서
핸들러 -> ReviewService -> ReviewRepository 순서로 줄줄이 이어진다.
(LLM 클라이언트와 답글 서비스의 의존성 함수는 3단계에서 추가한다)
"""

from typing import Annotated

from fastapi import Depends

from app.repositories.review_repository import ReviewRepository
from app.services.review_service import ReviewService

# ReviewRepository 객체는 이 모듈이 처음 import될 때 딱 한 번 만들어진다.
# 그래서 모든 요청이 같은 객체(같은 딕셔너리)를 사용한다. (Spring의 싱글톤 빈)
# 아래 함수 안에서 ReviewRepository()를 호출하면 요청마다 딕셔너리가 새로 생겨서 등록한 리뷰가 사라진다.
review_repository = ReviewRepository()


def get_review_repository() -> ReviewRepository:
    return review_repository


# ReviewService는 요청마다 새로 만든다. 저장소만 들고 있는 가벼운 객체라서 괜찮다.
def get_review_service(
    repository: Annotated[ReviewRepository, Depends(get_review_repository)],
) -> ReviewService:
    return ReviewService(repository)


# 핸들러에서 service: ReviewServiceDep 한 줄로 쓰기 위한 별칭
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
