"""
리뷰 라우터 (Spring의 @RestController 역할)

핸들러는 요청을 받아 서비스에 넘기고 결과를 반환하기만 한다.
- 주소의 {review_id}와 이름이 같은 매개변수 : 경로 변수(@PathVariable)
- Pydantic 모델 타입의 매개변수 : 요청 본문(@RequestBody + @Valid). 조건에 맞지 않으면 422
- ReviewServiceDep 타입의 매개변수 : 의존성 주입
(답글 핸들러는 3단계에서 추가한다)
"""

from fastapi import APIRouter

from app.dependencies import ReviewServiceDep
from app.schemas.review import ReviewCreateRequest, ReviewResponse

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
