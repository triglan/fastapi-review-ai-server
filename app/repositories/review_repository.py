"""
리뷰 저장소 (딕셔너리 저장소)

DB 대신 딕셔너리에 저장한다. 키는 리뷰 번호, 값은 Review 객체다.
서버를 다시 실행하면 처음 상태(더미 리뷰 3개)로 돌아간다.
서버 전체에 객체가 하나만 있어야 하므로 dependencies.py에서 한 번만 만든다.
"""

from app.domain.review import Review


# 서버가 실행될 때 미리 넣어 둘 더미 리뷰. 번호는 0으로 두고 저장할 때 붙인다.
# 별점을 5, 3, 1로 나눠 두면 답글 API에서 별점별 말투 차이를 바로 시험할 수 있다.
def init_reviews() -> list[Review]:
    return [
        Review(0, "김민수", 5, "스플렌더와 카탄을 즐겼어요. 규칙 설명도 친절해서 좋았습니다."),
        Review(0, "이손님", 3, "게임은 재미있었는데 설명을 듣기까지 오래 기다렸어요."),
        Review(0, "박단골", 1, "게임 구성품이 부족하고 테이블도 끈적거려서 실망했습니다."),
    ]


class ReviewRepository:

    def __init__(self):
        # 리뷰 번호 -> Review 객체
        self._reviews: dict[int, Review] = {}
        # 다음에 저장할 리뷰에 붙일 번호 (DB의 AUTO_INCREMENT 흉내)
        self._next_id = 1

        for review in init_reviews():
            self.save(review)

    def find_by_id(self, review_id: int) -> Review | None:
        """리뷰 번호로 리뷰 하나를 찾는다. 없으면 None을 반환한다."""
        # dict[키]는 키가 없으면 KeyError가 나지만, get()은 None을 돌려준다.
        return self._reviews.get(review_id)

    def save(self, review: Review) -> Review:
        """리뷰를 저장한다. 번호가 0인 새 리뷰에는 다음 번호를 붙인다. 같은 번호가 있으면 덮어쓴다(수정)."""
        if review.review_id == 0:
            review.review_id = self._next_id
            self._next_id += 1

        self._reviews[review.review_id] = review
        return review
