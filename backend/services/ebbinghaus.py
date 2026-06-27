from datetime import date, timedelta, datetime

EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]


def generate_review_plans(question_id: int, user_id: int, created_date: date | None = None) -> list[dict]:
    """为新增错题生成 6 轮艾宾浩斯复习计划"""
    created_date = created_date or date.today()
    plans = []
    for i, interval in enumerate(EBBINGHAUS_INTERVALS):
        plans.append({
            "question_id": question_id,
            "user_id": user_id,
            "review_date": created_date + timedelta(days=interval),
            "review_round": i + 1,
            "interval_days": interval,
            "status": "pending",
        })
    return plans


def get_adjusted_interval(base_interval: int, mastery_level: int) -> int:
    """根据掌握程度动态调整复习间隔

    mastery_level: 1-5（1=完全不会，5=完全掌握）
    """
    if mastery_level <= 1:
        return max(1, base_interval // 2)
    elif mastery_level <= 3:
        return base_interval
    else:
        return int(base_interval * 1.5)


def get_next_review_date(question_id: int, completed_round: int, mastery_level: int, completed_date: date | None = None) -> dict | None:
    """计算下一轮复习日期"""
    next_round = completed_round + 1
    if next_round > len(EBBINGHAUS_INTERVALS):
        return None

    completed_date = completed_date or date.today()
    base_interval = EBBINGHAUS_INTERVALS[next_round - 1]
    adjusted = get_adjusted_interval(base_interval, mastery_level)

    return {
        "question_id": question_id,
        "review_date": completed_date + timedelta(days=adjusted),
        "review_round": next_round,
        "interval_days": adjusted,
        "status": "pending",
    }
