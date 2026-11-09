"""
리뷰 라우터 (Spring의 @RestController 역할)

핸들러는 요청을 받아 서비스에 넘기고 결과를 반환하기만 한다.
- 주소의 {review_id}와 이름이 같은 매개변수 : 경로 변수(@PathVariable)
- Pydantic 모델 타입의 매개변수 : 요청 본문(@RequestBody + @Valid). 조건에 맞지 않으면 422
- ReviewServiceDep 타입의 매개변수 : 의존성 주입

등록, 조회는 금방 끝나는 일이라 def(동기), 답글은 LLM을 기다리는 일이라 async def(비동기)로 만든다.
"""

import threading
import time

from fastapi import APIRouter

from app.dependencies import ReplyServiceDep, ReviewServiceDep
from app.schemas.review import ReplyResponse, ReviewCreateRequest, ReviewResponse

router = APIRouter(
    # 이 라우터의 모든 주소 앞에 붙는 공통 주소 (Spring의 @RequestMapping)
    prefix="/api/reviews",
    # /docs 화면에서 API를 묶어 보여 줄 이름
    tags=["리뷰"],
)


# 1. 리뷰 등록 : 성공하면 201 Created
@router.post("", status_code=201, summary="리뷰 등록")
def register_review(request: ReviewCreateRequest, service: ReviewServiceDep) -> ReviewResponse:
    return service.register_review(request)

# 요청 : POST /api/reviews
# {"customerName": "최신규", "rating": 4, "content": "깔끔하고 맛있어요"}
# 응답 : 201
# {"reviewId": 4, "customerName": "최신규", "rating": 4, "content": "깔끔하고 맛있어요", "createdAt": "..."}
#
# 요청 : POST /api/reviews {"customerName": "최신규", "rating": 6, "content": "..."}
# 응답 : 422 (loc: ["body", "rating"], 5 이하여야 한다)


# 2. 리뷰 하나 조회
@router.get("/{review_id}", summary="리뷰 하나 조회")
def find_review(review_id: int, service: ReviewServiceDep) -> ReviewResponse:
    return service.find_review(review_id)

# 요청 : GET /api/reviews/1   -> 200
# 요청 : GET /api/reviews/99  -> 404 {"code": "ERROR_CODE_00001", "description": "조회 실패", "detail": "해당 리뷰가 존재하지 않습니다. reviewId=99"}


# 핸들러가 어느 스레드에서 실행되는지 터미널에 찍는다.
# - MainThread          : 이벤트 루프가 도는 스레드 (async def 핸들러)
# - AnyIO worker thread : def 핸들러를 실행하는 스레드 풀의 스레드
def log(handler: str, message: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"{now} [{handler}] {message} (스레드: {threading.current_thread().name})")


# 3. 사장님 답글 초안 생성 (async def)
# 저장된 리뷰를 꺼내 프롬프트를 만들고 await로 LLM을 호출한다.
# 기다리는 동안 이벤트 루프는 다른 요청을 처리한다. 요청 본문은 없다.
@router.post("/{review_id}/reply", summary="사장님 답글 초안 생성 (async)")
async def create_reply(review_id: int, service: ReplyServiceDep) -> ReplyResponse:
    log("reply", f"요청 받음 reviewId={review_id}")
    response = await service.create_reply(review_id)
    log("reply", "응답 보냄")
    return response

# 요청 : POST /api/reviews/3/reply   (별점 1 리뷰)
# 응답 : 200 {"reviewId": 3, "reply": "박단골님, ... 불편을 드려 죄송합니다. ...", "model": "gpt-6-luna"}
# 터미널 : 21:40:01 [reply] 요청 받음 reviewId=3 (스레드: MainThread)
#
# 요청 : POST /api/reviews/99/reply -> 404
# OpenAI 키가 틀렸을 때            -> 502 {"code": "ERROR_CODE_00011", "description": "AI 응답 실패", ...}
