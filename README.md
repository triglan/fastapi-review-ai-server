# FastAPI 리뷰 프로젝트

리뷰를 등록·조회하고, 저장된 리뷰로 LLM에게 사장님 답글 초안을 받는 FastAPI 서버입니다.

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

## 과제 체크리스트

- [x] `uv run fastapi dev`로 실행, `/docs`와 Postman에서 API 호출
- [x] 리뷰 등록 201, 잘못된 값 422, 없는 리뷰 404
- [x] 저장된 리뷰 내용으로 답글 응답, 터미널 스레드 이름 `MainThread`
- [x] OpenAI 호출 실패 시 502

**심화**

- [x] 별점 2 이하면 "죄송합니다"로 시작
- [x] 생성한 답글을 리뷰에 저장, 리뷰 조회 응답에 표시
- [x] 답글 API 동기 버전 추가 (`.env`에 `FAKE_LLM=true`, `FAKE_LLM_DELAY_SECONDS=5`, `THREAD_POOL_SIZE=1`로 두 버전 비교)
