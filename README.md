# FastAPI 보드게임 카페 리뷰 프로젝트

보드게임 카페 방문 경험에 대한 리뷰를 등록·조회하고, 저장된 리뷰로 LLM에게 사장님 답글 초안을 받는 FastAPI 서버입니다.

## 실행 방법

```bash
uv sync
cp .env.example .env
uv run fastapi dev
```

- OpenAI API 키는 환경 변수 `OPENAI_API_KEY`로 등록합니다. (`.env`에 적어도 동작합니다)
- 키가 없거나 `.env`에 `FAKE_LLM=true`를 적으면 OpenAI 대신 가짜 LLM으로 응답합니다.
- API 문서 : http://127.0.0.1:8000/docs

## API

| 메서드 | 주소 | 함수 | 설명 | 응답 |
|---|---|---|---|---|
| POST | `/api/reviews` | `def` | 리뷰 등록 | 201, 422 |
| GET | `/api/reviews/{review_id}` | `def` | 리뷰 하나 조회 | 200, 404 |
| POST | `/api/reviews/{review_id}/reply` | `async def` | 사장님 답글 초안 생성 | 200, 404, 502 |
| POST | `/api/reviews/{review_id}/reply/sync` | `def` | 답글 초안 생성 (동기, 비교용) | 200, 404, 502 |

### 리뷰 등록 요청 예시

```json
{
  "customerName": "김민수",
  "rating": 5,
  "content": "스플렌더와 카탄을 즐겼어요. 규칙 설명도 친절해서 좋았습니다."
}
```

### 사장님 답글 예시
```json
{
  "reviewId": 1,
  "reply": "감사합니다, 김민수님! 스플렌더와 카탄을 즐겁게 플레이하시고 규칙 설명도 친절하게 느껴 주셔서 기쁩니다. 좋은 시간을 보내셨다니 저희도 보람을 느껴요. 다음에도 편하게 놀러 와 주세요!",
  "model": "gpt-6-luna"
}
```