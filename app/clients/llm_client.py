"""
LLM 호출 클라이언트 (Spring Boot에서 RestClient로 OpenAI를 호출하던 클래스의 역할)

1) Spring Boot (RestClient)
- 요청 JSON(model, instructions, input)을 직접 Map으로 만들어 RestClient로 보냈다.
- 응답 JSON에서 output[].content[].text를 찾아 응답 문장을 꺼냈다.

2) FastAPI (openai 라이브러리)
- OpenAI 공식 라이브러리가 요청 JSON을 만들고, 응답 JSON을 객체로 바꿔 준다.
  응답 문장은 response.output_text로 꺼낸다.
- 동기 클라이언트(openai.OpenAI)와 비동기 클라이언트(openai.AsyncOpenAI)를 함께 제공한다.
  사용하는 방법은 똑같고, 비동기 클라이언트의 메서드는 async def라서 호출할 때 앞에 await를 붙인다는 것만 다르다.
  - 동기   : response = self._client.responses.create(...)
  - 비동기 : response = await self._async_client.responses.create(...)

이 클래스는 두 종류의 클라이언트를 함께 가지고, 동일한 작업을 수행하는 메서드를 두 개 제공한다.
- ask()       : 동기. OpenAI의 응답이 올 때까지 이 메서드를 실행한 스레드가 멈춰서 기다린다
- ask_async() : 비동기. 응답을 기다리는 동안 이벤트 루프가 다른 일을 할 수 있다
두 메서드를 언제 사용하는지는 routers/ai_router.py에서 비교한다.

키가 없거나 FAKE_LLM=true면 OpenAI를 호출하지 않는 FakeLlmClient를 대신 사용한다(main.py의 lifespan).
두 클래스의 메서드 이름과 매개변수가 같아서, AiService는 어느 쪽을 전달받든 코드를 바꾸지 않아도 된다.
"""

import asyncio
import time

import openai

from app.core.config import Settings
from app.core.exceptions import AiRequestError


# [실행해보기]
class OpenAiLlmClient:

    def __init__(self, settings: Settings):
        # 전달받은 설정 객체(Settings)를 보관한다
        self.settings = settings
        # 응답 DTO에 담을 모델 이름
        self.model = settings.openai_model

        # 설정 파일로부터 읽어들인 API 키가 없는 경우를 대비해 if문으로 검사한다.
        # 만약 키가 없다면 FastAPI의 lifespan이 이 클래스 대신 FakeLlmClient를 만든다.
        # 그래도 lifespan을 거치지 않고 이 클래스를 직접 만드는 경우(테스트 등)에는 여기서 원인을 알려 주며 멈춘다.
        if settings.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY가 없어 OpenAI 클라이언트를 만들 수 없습니다.")

        # 동기 클라이언트와 비동기 클라이언트를 동일한 설정으로 만든다.
        # (기존 Spring Boot에서는 LLM 서버를 다녀오기 위해 RestClient를 만들었다)
        # - api_key : SecretStr에서 실제 키 문자열을 꺼내 전달한다
        # - timeout : 응답을 기다리는 최대 시간(초)
        # - max_retries : 연결 실패나 서버 오류일 때 다시 시도할 횟수

        # API 키값 준비
        api_key = settings.openai_api_key.get_secret_value()

        # 동기 처리용 클라이언트 객체 생성
        self._client = openai.OpenAI(
            api_key=api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=1,
        )

        # 비동기 처리용 클라이언트 객체 생성
        self._async_client = openai.AsyncOpenAI(
            api_key=api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=1,
        )

    # 1. 동기 질문:
    # 응답이 올 때까지 이 라인에서 스레드가 멈춰 있다. 따라서 그동안 이 스레드는 다른 일을 하지 못한다.
    def ask(self, instructions: str, question: str) -> str:
        """
        질문을 OpenAI에 보내고 응답 문장을 반환한다. (동기)

        Args:
            instructions (str): 지시문(시스템 프롬프트). LLM이 어떤 역할로, 어떻게 응답할지 정한다.
            question (str): 손님의 질문

        Returns:
            str: LLM이 만든 응답 문장

        Raises:
            AiRequestError: OpenAI 호출이 실패했을 때 (키 오류, 한도 초과, 시간 초과, 연결 실패)
        """

        # 요청 시작시간 기록
        start = time.perf_counter()

        # try문 내에서 OpenAI 서버로 요청 전송
        try:
            # OpenAI Responses API 호출 (POST https://api.openai.com/v1/responses)
            response = self._client.responses.create(
                # 사용할 모델
                model=self.settings.openai_model,
                # 지시문(시스템 프롬프트)
                instructions=instructions,
                # 손님의 질문. 문자열 하나를 전달하면 사용자(user)가 보낸 메시지 하나로 처리된다.
                input=question,
                # 출력 토큰 상한
                max_output_tokens=self.settings.openai_max_output_tokens,
                # 추론 정도 (기본값 none : 추론 없이 바로 응답한다)
                reasoning={"effort": self.settings.openai_reasoning_effort},
                # 대화 내용을 OpenAI 서버에 저장하지 않는다
                store=False,
            )
        # openai 라이브러리의 예외(401, 429, 시간 초과 등)를 우리 예외로 바꿔서 다시 던진다.
        # 이때 'from e'를 붙이면 원래 예외가 트레이스백에 함께 찍혀서 원인을 찾기 쉽다.
        except openai.OpenAIError as e:
            raise to_ai_request_error(e) from e

        # 앞서 기록한 시작시간을 전달인자로 하여 콘솔 출력 함수를 호출한다
        print_usage("ask", response, start)

        # OpenAI 서버의 응답 문장을 반환한다
        return response.output_text

    # [작성하기]
    # 2. 비동기 질문:
    # 위 동기식 ask()와 같은 요청을 보내지만, 아래와 같이 세 가지 차이점이 존재한다.
    # 1) def -> async def
    # 2) self._client -> self._async_client (AsyncOpenAI)
    # 3) 호출 앞에 await
    # await 지점에서 이 코루틴은 멈추고, 응답이 오기 전까지 이벤트 루프는 다른 요청을 처리한다.
    async def ask_async(self, instructions: str, question: str) -> str:
        """
        질문을 OpenAI에 보내고 응답 문장을 반환한다. (비동기)

        Args:
            instructions (str): 지시문(시스템 프롬프트)
            question (str): 손님의 질문

        Returns:
            str: LLM이 만든 응답 문장

        Raises:
            AiRequestError: OpenAI 호출이 실패했을 때
        """

        # 요청 시작시간 기록
        start = time.perf_counter()

        # try문 내에서 OpenAI 서버로 요청 전송
        try:
            response = await self._async_client.responses.create(
                model=self.settings.openai_model,
                instructions=instructions,
                input=question,
                max_output_tokens=self.settings.openai_max_output_tokens,
                reasoning={"effort": self.settings.openai_reasoning_effort},
                store=False,
            )
        except openai.OpenAIError as e:
            raise to_ai_request_error(e) from e

        # 앞서 기록한 시작시간을 전달인자로 하여 콘솔 출력 함수를 호출한다
        print_usage("ask_async", response, start)

        # OpenAI 서버의 응답 문장을 반환한다
        return response.output_text

    # [실행해보기]
    # 서버가 종료될 때(lifespan) 호출해서 OpenAI 서버와의 연결을 닫는다.
    # 비동기 클라이언트의 close()도 async def라서 await가 필요하다.
    # 그래서 이 메서드도 async def다.
    async def close(self) -> None:
        self._client.close()
        await self._async_client.close()


def print_usage(method: str, response, start: float) -> None:
    """걸린 시간과 토큰 사용량을 콘솔에 찍는다. 비용을 확인할 때 사용한다."""

    # 요청 처리 시간 계산
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # OpenAI의 응답 객체로부터 토큰 사용량(usage)을 추출.
    usage = response.usage

    # response.usage에서 아래와 같은 정보를 확인할 수 있다.
    # - input_tokens: 입력 토큰 수
    # - output_tokens: 출력 토큰 수
    # - total_tokens: 입력/출력 토큰의 합
    # - input_tokens_details.cached_tokens: 입력 중 캐시에서 재사용한 토큰 수
    # - output_tokens_details.reasoning_tokens: 출력 중 추론에 사용한 토큰 수
    if usage is not None:
        print(f"[OpenAiLlmClient.{method}] model={response.model}, "
              f"입력 토큰={usage.input_tokens}, 출력 토큰={usage.output_tokens}, {elapsed_ms}ms")


def to_ai_request_error(e: openai.OpenAIError) -> AiRequestError:
    """
    openai 라이브러리의 예외를 우리 예외로 바꾼다. (Spring Boot에서 HTTP 상태 코드를 보고 우리 예외로 바꿨던 일)

    Args:
        e (openai.OpenAIError): OpenAI 호출 중 발생한 예외

    Returns:
        AiRequestError: 대신 던질 예외. 던지는 것은 호출한 쪽(raise ... from e)이다.
    """

    # AuthenticationError: OpenAI 서버의 401 응답. API 키가 틀렸거나, 삭제되었거나, 빈 문자열이다.
    if isinstance(e, openai.AuthenticationError):
        return AiRequestError("OpenAI API 키가 올바르지 않습니다. OPENAI_API_KEY를 확인하세요.")

    # RateLimitError: OpenAI 서버의 429 응답. 짧은 시간에 요청을 너무 많이 보냈거나, 계정의 충전 잔액이 바닥났다.
    if isinstance(e, openai.RateLimitError):
        return AiRequestError("OpenAI 요청 한도를 넘었거나 충전 잔액이 부족합니다.")

    # APITimeoutError: 요청은 보냈지만 timeout(OPENAI_TIMEOUT_SECONDS) 안에 응답이 오지 않음.
    # APITimeoutError는 APIConnectionError의 자식 클래스라서 예외 계층 구조상 먼저 검사한다.
    if isinstance(e, openai.APITimeoutError):
        return AiRequestError("OpenAI 응답이 제한 시간 안에 오지 않았습니다.")

    # APIConnectionError: OpenAI 서버에 닿지 못함. 인터넷 연결이 끊겼거나, 방화벽·프록시가 막았다.
    # (응답 자체를 받지 못했으므로 HTTP 상태 코드가 없다)
    if isinstance(e, openai.APIConnectionError):
        return AiRequestError("OpenAI 서버에 연결할 수 없습니다.")

    # 그 밖의 오류: 400(요청 형식 오류, 없는 모델 이름 등), 403(권한 없음), 500번대(OpenAI 서버 오류) 등.
    # 메시지에 원래 예외의 내용을 함께 담는다.
    return AiRequestError(f"OpenAI 호출 실패 : {e}")


# [실행해보기]
class FakeLlmClient:
    """
    OpenAI를 호출하지 않는 가짜 클라이언트. 키가 없거나 FAKE_LLM=true일 때 사용한다.
    LLM이 응답하는 데 걸리는 시간만 흉내 내고, 정해진 문장을 반환한다.
    """

    def __init__(self, settings: Settings):
        self.delay_seconds = settings.fake_llm_delay_seconds
        self.model = "fake-llm"

    # time.sleep : 이 스레드를 멈춰 세운다. 동기 클라이언트가 응답을 기다리는 것과 같은 상황을 만든다.
    def ask(self, instructions: str, question: str) -> str:
        time.sleep(self.delay_seconds)
        return f"(가짜 응답) '{question}'에 대한 응답입니다. {self.delay_seconds}초 기다렸습니다."

    # await asyncio.sleep : 이 코루틴만 멈춘다. 기다리는 동안 이벤트 루프는 다른 요청을 처리한다.
    # 비동기 클라이언트가 응답을 기다리는 것과 같은 상황을 만든다.
    async def ask_async(self, instructions: str, question: str) -> str:
        await asyncio.sleep(self.delay_seconds)
        return f"(가짜 응답) '{question}'에 대한 응답입니다. {self.delay_seconds}초 기다렸습니다."

    async def close(self) -> None:
        pass


# 두 클라이언트 중 하나라는 뜻의 타입 이름. 의존성 함수와 AiService의 타입 힌트에 사용한다.
LlmClient = OpenAiLlmClient | FakeLlmClient
