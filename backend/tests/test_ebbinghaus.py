from datetime import date, timedelta

from services.ebbinghaus import (
    EBBINGHAUS_INTERVALS,
    generate_review_plans,
    get_adjusted_interval,
    get_next_review_date,
)


def test_intervals():
    assert EBBINGHAUS_INTERVALS == [1, 2, 4, 7, 15, 30]


def test_generate_review_plans():
    plans = generate_review_plans(question_id=1, user_id=1, created_date=date(2026, 6, 23))

    assert len(plans) == 6
    assert plans[0]["review_date"] == date(2026, 6, 24)  # +1
    assert plans[1]["review_date"] == date(2026, 6, 25)  # +2
    assert plans[2]["review_date"] == date(2026, 6, 27)  # +4
    assert plans[3]["review_date"] == date(2026, 6, 30)  # +7
    assert plans[4]["review_date"] == date(2026, 7, 8)   # +15
    assert plans[5]["review_date"] == date(2026, 7, 23)  # +30

    for i, plan in enumerate(plans):
        assert plan["question_id"] == 1
        assert plan["user_id"] == 1
        assert plan["review_round"] == i + 1
        assert plan["interval_days"] == EBBINGHAUS_INTERVALS[i]
        assert plan["status"] == "pending"


def test_generate_review_plans_default_date():
    plans = generate_review_plans(question_id=1, user_id=1)
    today = date.today()
    assert plans[0]["review_date"] == today + timedelta(days=1)


def test_adjusted_interval_low_mastery():
    assert get_adjusted_interval(7, 1) == 3   # 7//2
    assert get_adjusted_interval(1, 1) == 1   # max(1, 0)


def test_adjusted_interval_medium_mastery():
    assert get_adjusted_interval(7, 3) == 7
    assert get_adjusted_interval(15, 2) == 15


def test_adjusted_interval_high_mastery():
    assert get_adjusted_interval(7, 4) == 10   # int(7*1.5)
    assert get_adjusted_interval(30, 5) == 45  # int(30*1.5)


def test_get_next_review_date():
    result = get_next_review_date(
        question_id=1,
        completed_round=1,
        mastery_level=3,
        completed_date=date(2026, 6, 23),
    )
    assert result is not None
    assert result["review_round"] == 2
    assert result["interval_days"] == 2
    assert result["review_date"] == date(2026, 6, 25)


def test_get_next_review_date_high_mastery():
    result = get_next_review_date(
        question_id=1,
        completed_round=1,
        mastery_level=5,
        completed_date=date(2026, 6, 23),
    )
    assert result is not None
    assert result["review_round"] == 2
    assert result["interval_days"] == 3  # int(2*1.5)


def test_get_next_review_date_last_round():
    result = get_next_review_date(
        question_id=1,
        completed_round=6,
        mastery_level=3,
    )
    assert result is None
