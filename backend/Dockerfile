FROM python:3.11-slim

# 系统依赖：
# - WeasyPrint: Pango / Cairo / GDK-PixBuf + CJK 字体（PDF 中文渲染）
# - OpenCV headless: libglib
# - shared-mime-info: WeasyPrint 推断图片 MIME 类型
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
