from services.qwen_vl import safe_parse_json


def test_parse_valid_json_array():
    text = '[{"subject": "数学", "topic": "三位数乘法"}]'
    result = safe_parse_json(text)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["subject"] == "数学"


def test_parse_valid_json_object():
    text = '{"subject": "数学", "topic": "加法"}'
    result = safe_parse_json(text)
    assert isinstance(result, dict)
    assert result["subject"] == "数学"


def test_parse_with_markdown_code_block():
    text = '```json\n[{"subject": "数学"}]\n```'
    result = safe_parse_json(text)
    assert isinstance(result, list)
    assert result[0]["subject"] == "数学"


def test_parse_with_markdown_no_lang():
    text = '```\n{"subject": "语文"}\n```'
    result = safe_parse_json(text)
    assert isinstance(result, dict)
    assert result["subject"] == "语文"


def test_parse_with_surrounding_text():
    text = '好的，以下是分析结果：\n[{"subject": "英语"}]\n希望对你有帮助！'
    result = safe_parse_json(text)
    assert isinstance(result, list)
    assert result[0]["subject"] == "英语"


def test_parse_empty_array():
    text = '[]'
    result = safe_parse_json(text)
    assert isinstance(result, list)
    assert len(result) == 0


def test_parse_invalid_returns_none():
    text = '这不是JSON'
    result = safe_parse_json(text)
    assert result is None


def test_parse_complex_structure():
    text = '''[
      {
        "subject": "数学",
        "topic": "三位数乘法",
        "question_text": "小红有235本书",
        "formulas": ["$235 \\\\times 12 = ?$"],
        "figures": [{"description": "数轴", "svg": "<svg></svg>"}],
        "student_answer": "247",
        "correct_answer": "2820",
        "error_type": "计算错误",
        "error_analysis": "忘记进位",
        "tags": ["进位乘法", "三位数"]
      }
    ]'''
    result = safe_parse_json(text)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["formulas"] == ["$235 \\times 12 = ?$"]
    assert result[0]["tags"] == ["进位乘法", "三位数"]
