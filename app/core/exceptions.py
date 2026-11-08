"""
예외와 예외 처리기 (Spring의 GlobalExceptionHandler 역할)

서비스는 예외를 던지기만 하고, 그 예외를 HTTP 응답(상태 코드 + JSON)으로 바꾸는 일은 이 파일의 처리기가 한다.
처리기는 main.py에서 register_exception_handlers(app)를 호출해 등록한다.
(OpenAI 호출 실패 예외 AiRequestError(502)는 3단계에서 추가한다)
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# 리뷰를 찾지 못했을 때 ReviewService가 던지는 사용자 정의 예외
class ReviewNotFoundError(Exception):

    def __init__(self, review_id: int):
        super().__init__(f"해당 리뷰가 존재하지 않습니다. reviewId={review_id}")
        self.review_id = review_id


def register_exception_handlers(app: FastAPI) -> None:

    # ReviewNotFoundError가 던져지면 FastAPI가 이 함수를 호출하고, 반환한 응답을 보낸다.
    @app.exception_handler(ReviewNotFoundError)
    def handle_review_not_found(request: Request, e: ReviewNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "code": "ERROR_CODE_00001",
                "description": "조회 실패",
                # str(e)는 예외를 만들 때 전달한 메시지다. (Java의 e.getMessage())
                "detail": str(e),
            },
        )
