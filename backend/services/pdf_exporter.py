import base64
import io
import os
import re
from datetime import date

from jinja2 import Template


def _image_to_data_uri(image_path: str) -> str | None:
    """将本地图片文件转为 base64 data URI，供 WeasyPrint 嵌入"""
    if not image_path or not os.path.isfile(image_path):
        return None

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(ext, "image/jpeg")

    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


def _latex_to_svg(latex: str) -> str | None:
    """将 LaTeX 公式渲染为 SVG 字符串（使用 matplotlib mathtext）"""
    text = latex.strip().strip("$")
    if not text:
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import mathtext

        parser = mathtext.MathTextParser("svg")
        buf = io.BytesIO()
        parser.to_svg(buf, text, fontsize=14)
        return buf.getvalue().decode()
    except Exception:
        return None


def render_pdf(questions, export_date: date) -> bytes:
    """将错题列表渲染为 PDF，嵌入原始图片 + LaTeX 公式渲染"""
    from weasyprint import HTML

    processed = []
    for q in questions:
        item = {
            "subject": q.subject,
            "topic": q.topic or "",
            "created_at": str(q.created_at)[:10] if q.created_at else "",
            "error_type": q.error_type or "",
            "question_text": q.question_text or "",
            "student_answer": q.student_answer or "",
            "correct_answer": q.correct_answer or "",
            "error_analysis": q.error_analysis or "",
            "tags": q.tags or [],
            "original_image_uri": _image_to_data_uri(q.original_image),
            "formula_svgs": [],
            "figures": q.figures or [],
        }

        for formula in (q.formulas or []):
            svg = _latex_to_svg(formula)
            if svg:
                item["formula_svgs"].append(svg)
            else:
                item["formula_svgs"].append(None)

        processed.append(item)

    template = Template(PDF_HTML_TEMPLATE)
    html = template.render(questions=processed, export_date=export_date)
    return HTML(string=html).write_pdf()


PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif; font-size: 14px; }

  .error-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    page-break-inside: avoid;
  }

  .meta { color: #666; font-size: 12px; margin-bottom: 10px; }
  .meta span { margin-right: 12px; }

  .question { font-size: 15px; line-height: 1.8; margin: 8px 0; }

  .formula-svg { margin: 8px 0; text-align: center; }
  .formula-fallback { font-family: "Times New Roman", serif; font-size: 16px; margin: 8px 0; }

  .figure { text-align: center; margin: 12px 0; }

  .original-image {
    max-width: 100%;
    max-height: 300px;
    margin: 12px 0;
    border: 1px solid #eee;
    border-radius: 4px;
  }

  .answer-section {
    display: flex;
    gap: 40px;
    margin: 12px 0;
  }
  .answer-item { flex: 1; }
  .answer-label { color: #999; font-size: 12px; }
  .answer-value { font-size: 15px; font-weight: 600; }
  .answer-wrong { color: #e74c3c; }
  .answer-right { color: #27ae60; }

  .write-area {
    border: 1px dashed #ccc;
    border-radius: 4px;
    min-height: 80px;
    margin-top: 12px;
    padding: 8px;
    color: #bbb;
    font-size: 12px;
  }

  .error-analysis {
    background: #fff8e1;
    border-left: 3px solid #ffc107;
    padding: 8px 12px;
    margin-top: 12px;
    font-size: 13px;
    color: #666;
    border-radius: 0 4px 4px 0;
  }

  .tags { margin-top: 10px; }
  .tag {
    display: inline-block;
    background: #f0f0f0;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    margin-right: 6px;
  }
</style>
</head>
<body>
  <h2 style="text-align: center; margin-bottom: 24px;">错题本 - {{ export_date }}</h2>

  {% for q in questions %}
  <div class="error-card">
    <div class="meta">
      <span>科目：{{ q.subject }}</span>
      <span>知识点：{{ q.topic }}</span>
      <span>日期：{{ q.created_at }}</span>
      {% if q.error_type %}<span>错因：{{ q.error_type }}</span>{% endif %}
    </div>

    <div class="question">{{ q.question_text }}</div>

    {% for svg in q.formula_svgs %}
      {% if svg %}
        <div class="formula-svg">{{ svg | safe }}</div>
      {% endif %}
    {% endfor %}

    {% for fig in q.figures %}
      <div class="figure">{{ fig.svg | safe }}</div>
    {% endfor %}

    {% if q.original_image_uri %}
      <img class="original-image" src="{{ q.original_image_uri }}" />
    {% endif %}

    <div class="answer-section">
      <div class="answer-item">
        <div class="answer-label">我的答案</div>
        <div class="answer-value answer-wrong">{{ q.student_answer or '-' }}</div>
      </div>
      <div class="answer-item">
        <div class="answer-label">正确答案</div>
        <div class="answer-value answer-right">{{ q.correct_answer or '-' }}</div>
      </div>
    </div>

    <div class="write-area">订正区域（手写）</div>

    {% if q.error_analysis %}
      <div class="error-analysis">📝 {{ q.error_analysis }}</div>
    {% endif %}

    {% if q.tags %}
      <div class="tags">
        {% for tag in q.tags %}
          <span class="tag">{{ tag }}</span>
        {% endfor %}
      </div>
    {% endif %}
  </div>
  {% endfor %}
</body>
</html>"""


MONTHLY_REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif; font-size: 14px; }
  h2 { text-align: center; margin-bottom: 8px; }
  .subtitle { text-align: center; color: #666; margin-bottom: 24px; }
  .summary { display: flex; gap: 20px; margin-bottom: 24px; }
  .summary-box { flex: 1; text-align: center; padding: 16px; background: #f8f8f8; border-radius: 8px; }
  .summary-num { font-size: 28px; font-weight: 700; color: #4A90D9; }
  .summary-label { font-size: 12px; color: #999; margin-top: 4px; }
  .error-card {
    border: 1px solid #ddd; border-radius: 8px; padding: 16px;
    margin-bottom: 16px; page-break-inside: avoid;
  }
  .meta { color: #666; font-size: 12px; margin-bottom: 8px; }
  .meta span { margin-right: 12px; }
  .question { font-size: 14px; line-height: 1.8; }
  .answer { font-size: 13px; margin-top: 8px; }
  .answer-wrong { color: #e74c3c; }
  .answer-right { color: #27ae60; }
  .error-analysis {
    background: #fff8e1; border-left: 3px solid #ffc107;
    padding: 8px 12px; margin-top: 8px; font-size: 13px; color: #666;
  }
</style>
</head>
<body>
  <h2>错题月度报告</h2>
  <div class="subtitle">{{ year }}年{{ month }}月</div>

  <div class="summary">
    <div class="summary-box">
      <div class="summary-num">{{ total }}</div>
      <div class="summary-label">本月新增错题</div>
    </div>
    <div class="summary-box">
      <div class="summary-num">{{ completed_reviews }}</div>
      <div class="summary-label">已完成复习</div>
    </div>
    <div class="summary-box">
      <div class="summary-num">{{ subjects }}</div>
      <div class="summary-label">涉及科目</div>
    </div>
  </div>

  {% for q in questions %}
  <div class="error-card">
    <div class="meta">
      <span>{{ q.subject }}</span>
      <span>{{ q.topic }}</span>
      <span>{{ q.created_at }}</span>
      {% if q.error_type %}<span>{{ q.error_type }}</span>{% endif %}
    </div>
    <div class="question">{{ q.question_text }}</div>
    <div class="answer">
      <span class="answer-wrong">我的答案：{{ q.student_answer or '-' }}</span>
      &nbsp;&nbsp;
      <span class="answer-right">正确答案：{{ q.correct_answer or '-' }}</span>
    </div>
    {% if q.error_analysis %}
      <div class="error-analysis">{{ q.error_analysis }}</div>
    {% endif %}
  </div>
  {% endfor %}
</body>
</html>"""


def render_monthly_report(questions, year: int, month: int, completed_reviews: int) -> bytes:
    """渲染月度报告 PDF"""
    from weasyprint import HTML

    subjects = len(set(q.subject for q in questions))

    processed = []
    for q in questions:
        processed.append({
            "subject": q.subject,
            "topic": q.topic or "",
            "created_at": str(q.created_at)[:10] if q.created_at else "",
            "error_type": q.error_type or "",
            "question_text": q.question_text or "",
            "student_answer": q.student_answer or "",
            "correct_answer": q.correct_answer or "",
            "error_analysis": q.error_analysis or "",
        })

    template = Template(MONTHLY_REPORT_TEMPLATE)
    html = template.render(
        questions=processed,
        year=year,
        month=month,
        total=len(questions),
        completed_reviews=completed_reviews,
        subjects=subjects,
    )
    return HTML(string=html).write_pdf()
