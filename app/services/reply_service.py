"""
답글 서비스 : 저장된 리뷰를 꺼내 프롬프트를 만들고, await로 LLM을 호출해 사장님 답글 초안을 만든다.

chap02의 AiService와 다른 점
- AiService는 손님이 보낸 질문을 그대로 LLM에 넘겼다.
- ReplyService는 저장소에서 리뷰를 꺼내, 그 내용(손님 이름, 별점, 리뷰 내용)으로 프롬프트를 직접 조립한다.
  그래서 저장소와 LLM 클라이언트 두 개를 주입받는다.

async def와 await
- LLM 응답을 기다리는 동안 이 코루틴은 await 지점에서 멈추고, 이벤트 루프는 다른 요청을 처리한다.
- await는 async def 안에서만 쓸 수 있으므로, 이 메서드를 부르는 핸들러도 async def가 된다.
"""

from app.clients.llm_client import LlmClient
from app.core.exceptions import ReviewNotFoundError
from app.domain.review import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReplyResponse

# 지시문(시스템 프롬프트) : LLM에게 맡길 역할과 응답 규칙. 리뷰마다 바뀌지 않으므로 상수로 둔다.
INSTRUCTIONS = (
    "너는 식당 사장님이다. 손님이 남긴 리뷰에 사장님 답글을 쓴다.\n"
    "- 손님 이름을 불러 주고, 리뷰에 적힌 구체적인 내용을 짚어서 답한다.\n"
    "- 정중하고 따뜻한 말투로 3~4문장으로 쓴다.\n"
    "- 답글 본문만 쓰고, 따옴표나 제목은 붙이지 않는다."
)


def build_prompt(review: Review) -> str:
    """저장된 리뷰로 LLM에 보낼 입력(프롬프트)을 만든다."""
    return (
        f"손님 이름: {review.customer_name}\n"
        f"별점: {review.rating}점 (5점 만점)\n"
        f"리뷰 내용: {review.content}"
    )


class ReplyService:

    # 생성자 주입 : 저장소(리뷰를 꺼낼 곳)와 LLM 클라이언트(답글을 만들 곳). 진짜든 가짜든 상관없다.
    def __init__(self, repository: ReviewRepository, llm_client: LlmClient):
        self.repository = repository
        self.llm_client = llm_client

    async def create_reply(self, review_id: int) -> ReplyResponse:
        """
        리뷰 하나에 대한 사장님 답글 초안을 만든다. (비동기)

        Raises:
            ReviewNotFoundError: 리뷰가 없을 때 (-> 404)
            AiRequestError: OpenAI 호출이 실패했을 때 (-> 502, LLM 클라이언트가 던진다)
        """

        # 1. 저장된 리뷰를 꺼낸다. 없으면 404
        review = self.repository.find_by_id(review_id)
        if review is None:
            raise ReviewNotFoundError(review_id)

        # 2. 리뷰 내용으로 프롬프트를 만든다.
        prompt = build_prompt(review)

        # 3. await로 LLM을 호출한다. 응답을 기다리는 동안 이벤트 루프는 다른 요청을 처리한다.
        reply = await self.llm_client.ask_async(INSTRUCTIONS, prompt)

        # 4. 응답 DTO로 반환한다.
        return ReplyResponse(review_id=review.review_id, reply=reply, model=self.llm_client.model)
