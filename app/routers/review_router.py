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
# {"customerName": "최신규", "rating": 4, "content": "친구들과 재미있게 즐겼어요"}
# 응답 : 201
# {"reviewId": 4, "customerName": "최신규", "rating": 4, "content": "친구들과 재미있게 즐겼어요", "createdAt": "...", "reply": null}
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


# 4. 사장님 답글 초안 생성 (def, 비교용)
# 3번과 같은 일을 동기로 한다. def 핸들러라서 이벤트 루프가 아니라 스레드 풀에서 실행되고,
# LLM 응답을 기다리는 동안 그 스레드 하나가 통째로 멈춘다.
@router.post("/{review_id}/reply/sync", summary="사장님 답글 초안 생성 (sync, 비교용)")
def create_reply_sync(review_id: int, service: ReplyServiceDep) -> ReplyResponse:
    log("reply-sync", f"요청 받음 reviewId={review_id}")
    response = service.create_reply_sync(review_id)
    log("reply-sync", "응답 보냄")
    return response

# 터미널 : 22:30:01 [reply-sync] 요청 받음 reviewId=1 (스레드: AnyIO worker thread)
#
# [Postman 탭 두 개로 비교하기]
# .env에 FAKE_LLM=true, FAKE_LLM_DELAY_SECONDS=5, THREAD_POOL_SIZE=1을 적고 서버를 다시 실행한다.
# 탭 A의 Send를 누른 직후 탭 B의 Send를 누른다.
# - 둘 다 /reply/sync : A는 5초, B는 약 10초. 스레드가 하나뿐이라 B는 A가 끝날 때까지 시작하지 못한다.
# - 둘 다 /reply      : 둘 다 약 5초. await로 기다리는 동안 이벤트 루프가 B를 받는다.
# 확인했으면 .env를 원래대로 되돌린다.
