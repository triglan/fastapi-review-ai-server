"""
앱 조립 : FastAPI 앱 객체를 만들고, 예외 처리기와 라우터를 등록한다.

uv run fastapi dev 를 실행하면 pyproject.toml의 entrypoint("app.main:app")를 보고
이 파일의 app 변수를 찾아 서버를 실행한다.
(3단계에서 lifespan을 여기에 붙인다)
"""

from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.routers import review_router

# 1. 앱 객체. title, version은 /docs 화면 맨 위에 나온다.
app = FastAPI(title="FastAPI 리뷰 프로젝트", version="1.0.0")

# 2. 예외 처리기 등록 (Spring은 @ControllerAdvice를 알아서 찾지만, FastAPI는 직접 등록한다)
register_exception_handlers(app)

# 3. 라우터 등록. 등록하지 않은 라우터의 주소는 모두 404가 된다.
app.include_router(review_router.router)
