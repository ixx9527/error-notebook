import json
import re
import asyncio
from functools import partial

import dashscope
from dashscope import MultiModalConversation

from config import DASHSCOPE_API_KEY, QWEN_VL_MODEL

dashscope.api_key = DASHSCOPE_API_KEY

ANALYZE_PROMPT = """你是一个专业的小学错题整理助手。请仔细分析这张错题照片，提取所有信息并输出JSON。

如果照片中包含多道题目，请将每道题目作为数组中的一个元素输出。

输出格式（只输出JSON，不要其他内容）：

[
  {
    "subject": "语文|数学|英语|其他",
    "topic": "具体知识点",
    "question_text": "完整的题目正文文字，保留原有的编号和结构。如果是阅读理解题，保留原文和问题。不要省略任何文字。",
    "formulas": ["数学公式用LaTeX格式，如 $a^2 + b^2 = c^2$。没有公式则为空数组。"],
    "figures": [
      {
        "description": "图形的文字描述",
        "svg": "用标准SVG代码重绘图形。要求：1.保持原始比例 2.保留所有标注（数字、字母、单位）3.区分实线和虚线 4.设置合适的viewBox 5.不要包含题目文字，只画图形。没有图形则为空数组。"
      }
    ],
    "student_answer": "学生的原始答案（从手写内容识别）。如果无法识别或照片中没有答案，填null。",
    "correct_answer": "正确答案。如果无法确定，填null。",
    "error_type": "错因分类：计算错误|概念混淆|审题不清|格式错误|粗心大意|方法错误|其他",
    "error_analysis": "详细分析学生为什么做错，以及正确的解题思路。50-100字。",
    "tags": ["2-4个标签，用于分类和检索"]
  }
]

注意事项：
1. 只输出JSON数组，不要输出任何解释、markdown标记或其他内容
2. SVG代码必须是合法的、可直接渲染的SVG
3. 数学公式必须使用LaTeX语法
4. 如果整张照片只有一道题，也输出数组格式（单个元素的数组）
5. 如果照片质量太差无法识别，返回空数组 []"""


def safe_parse_json(text: str) -> list | dict | None:
    """多策略 JSON 解析容错"""
    # 策略1：直接解析
    try:
        result = json.loads(text)
        return result
    except (json.JSONDecodeError, TypeError):
        pass

    # 策略2：去掉 markdown 代码块标记
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    # 策略3：提取第一个 [ 或 { 到最后一个 ] 或 }
    match = re.search(r'[\[{].*[\]}]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def analyze_error_image(image_path: str, max_retries: int = 2) -> list[dict]:
    """分析错题图片，返回结构化结果列表"""
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{image_path}"},
                {"text": ANALYZE_PROMPT},
            ],
        }
    ]

    for attempt in range(max_retries + 1):
        try:
            response = MultiModalConversation.call(
                model=QWEN_VL_MODEL,
                messages=messages,
            )

            if response.status_code != 200:
                if attempt < max_retries:
                    continue
                return []

            content = response.output.choices[0].message.content[0]["text"]
            result = safe_parse_json(content)

            if result is None:
                if attempt < max_retries:
                    continue
                return []

            if isinstance(result, dict):
                return [result]
            if isinstance(result, list):
                return result
            return []

        except Exception:
            if attempt < max_retries:
                continue
            return []

    return []


async def analyze_error_image_async(image_path: str) -> list[dict]:
    """异步包装，避免阻塞事件循环"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(analyze_error_image, image_path))
