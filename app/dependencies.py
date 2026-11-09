"""
의존성 함수 (Spring의 빈 등록 + 생성자 주입 역할)

핸들러의 매개변수에 Depends(의존성 함수)를 적으면, 요청이 들어올 때마다 FastAPI가 그 함수를 호출해
반환값을 넣어 준다. 의존성 함수의 매개변수에도 Depends를 적을 수 있어서
핸들러 -> ReviewService -> ReviewRepository 순서로 줄줄이 이어진다.
"""

from typing import Annotated

from fastapi import Depends, Request

from app.clients.llm_client import LlmClient
from app.repositories.review_repository import ReviewRepository
from app.services.reply_service import ReplyService
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


# LLM 클라이언트는 서버가 시작할 때(main.py의 lifespan) 한 번 만들어 app.state에 넣어 두었다.
# 여기서는 꺼내 주기만 한다. request.app은 main.py의 app 객체다.
# (저장소처럼 이 모듈에서 바로 만들지 않는 이유 : 서버가 꺼질 때 연결을 닫아야 해서, 만들고 닫는 일을 lifespan 한곳에서 한다)
def get_llm_client(request: Request) -> LlmClient:
    return request.app.state.llm_client


# ReplyService는 저장소와 LLM 클라이언트 두 개를 주입받는다.
# 저장소는 ReviewService와 같은 객체라서, 방금 등록한 리뷰로도 바로 답글을 만들 수 있다.
def get_reply_service(
    repository: Annotated[ReviewRepository, Depends(get_review_repository)],
    llm_client: Annotated[LlmClient, Depends(get_llm_client)],
) -> ReplyService:
    return ReplyService(repository, llm_client)


ReplyServiceDep = Annotated[ReplyService, Depends(get_reply_service)]
