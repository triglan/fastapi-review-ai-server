"""
예외와 예외 처리기 (Spring의 GlobalExceptionHandler 역할)

서비스는 예외를 던지기만 하고, 그 예외를 HTTP 응답(상태 코드 + JSON)으로 바꾸는 일은 이 파일의 처리기가 한다.
처리기는 main.py에서 register_exception_handlers(app)를 호출해 등록한다.
- ReviewNotFoundError -> 404
- AiRequestError      -> 502
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# 리뷰를 찾지 못했을 때 ReviewService가 던지는 사용자 정의 예외
class ReviewNotFoundError(Exception):

    def __init__(self, review_id: int):
        super().__init__(f"해당 리뷰가 존재하지 않습니다. reviewId={review_id}")
        self.review_id = review_id


# OpenAI 호출이 실패했을 때 LLM 클라이언트가 던지는 예외 (키 오류, 한도 초과, 시간 초과, 연결 실패)
# 추가할 필드가 없으므로 본문은 pass다. 메시지는 예외를 만들 때 전달한다.
class AiRequestError(Exception):
    pass


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

    # OpenAI 호출이 실패하면 502 Bad Gateway로 응답한다.
    # 502는 "우리 서버가 호출한 다른 서버(OpenAI)가 실패했다"는 뜻이다. 우리 서버의 잘못(500)과 구분한다.
    @app.exception_handler(AiRequestError)
    def handle_ai_request_error(request: Request, e: AiRequestError):
        return JSONResponse(
            status_code=502,
            content={
                "code": "ERROR_CODE_00011",
                "description": "AI 응답 실패",
                "detail": str(e),
            },
        )
