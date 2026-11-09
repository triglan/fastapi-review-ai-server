"""
앱 조립 : lifespan, 예외 처리기와 라우터를 등록한다.

uv run fastapi dev 를 실행하면 pyproject.toml의 entrypoint("app.main:app")를 보고
이 파일의 app 변수를 찾아 서버를 실행한다.
"""

from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI

from app.clients.llm_client import FakeLlmClient, OpenAiLlmClient
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.routers import review_router


# lifespan : 서버가 시작할 때(yield 이전)와 종료될 때(yield 이후) 실행할 코드
# (Spring의 @PostConstruct와 @PreDestroy를 한 함수에 적은 것)
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # 1. 서버 시작 : 모든 요청이 함께 쓸 LLM 클라이언트를 만들어 app.state에 넣는다.
    #    FAKE_LLM=true거나 API 키가 없으면 OpenAI를 호출하지 않는 가짜 클라이언트를 쓴다.
    if settings.fake_llm or settings.openai_api_key is None:
        print(f"[lifespan] 가짜 LLM 클라이언트를 사용한다 (FAKE_LLM={settings.fake_llm}, "
              f"키 있음={settings.openai_api_key is not None}, 응답까지 {settings.fake_llm_delay_seconds}초)")
        app.state.llm_client = FakeLlmClient(settings)
    else:
        print(f"[lifespan] OpenAI 클라이언트를 사용한다 (model={settings.openai_model})")
        app.state.llm_client = OpenAiLlmClient(settings)

    # 2. 실험용 : 설정에 THREAD_POOL_SIZE가 있으면 def 핸들러를 실행하는 스레드 풀의 크기를 바꾼다.
    #    (기본 40개. 1로 줄이면 def 핸들러가 한 번에 하나씩만 실행되는 것을 볼 수 있다)
    if settings.thread_pool_size is not None:
        anyio.to_thread.current_default_thread_limiter().total_tokens = settings.thread_pool_size
        print(f"[lifespan] 스레드 풀 크기 : {settings.thread_pool_size}개")

    # 3. 이 지점에서 멈춰 있는 동안 서버가 요청을 받는다.
    yield

    # 4. 서버 종료 : OpenAI 서버와의 연결을 닫는다.
    await app.state.llm_client.close()


# 1. 앱 객체. title, version은 /docs 화면 맨 위에 나온다. lifespan을 등록해야 위 함수가 실행된다.
app = FastAPI(title="FastAPI 리뷰 프로젝트", version="1.0.0", lifespan=lifespan)

# 2. 예외 처리기 등록 (Spring은 @ControllerAdvice를 알아서 찾지만, FastAPI는 직접 등록한다)
register_exception_handlers(app)

# 3. 라우터 등록. 등록하지 않은 라우터의 주소는 모두 404가 된다.
app.include_router(review_router.router)
