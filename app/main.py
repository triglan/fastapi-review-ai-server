"""
앱 조립 : FastAPI 앱 객체를 만든다.

uv run fastapi dev 를 실행하면 pyproject.toml의 entrypoint("app.main:app")를 보고
이 파일의 app 변수를 찾아 서버를 실행한다.
(2단계에서 예외 처리기와 라우터, 3단계에서 lifespan을 여기에 붙인다)
"""

from fastapi import FastAPI

# /docs 화면 맨 위에 나오는 서버 이름과 버전
app = FastAPI(title="FastAPI 리뷰 프로젝트", version="1.0.0")
