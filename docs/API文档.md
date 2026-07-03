# 错题本 API 文档

> 基础路径：`/api`  
> 认证方式：JWT Bearer Token（`Authorization: Bearer <token>`）  
> 响应格式：统一 JSON，成功时 `code: 0`，失败时返回 HTTP 错误码 + `detail` 字段

---

## 目录

- [1. 认证](#1-认证)
- [2. 错题管理](#2-错题管理)
- [3. 复习管理](#3-复习管理)
- [4. PDF 导出](#4-pdf-导出)
- [5. 统计](#5-统计)
- [6. 用户](#6-用户)
- [7. 消息通知](#7-消息通知)
- [8. 孩子管理](#8-孩子管理)
- [9. 健康检查](#9-健康检查)

---

## 1. 认证

前缀：`/api/auth`

### 1.1 微信登录

```
POST /api/auth/login
```

通过微信小程序 `wx.login()` 获取的 `code` 换取 openid，自动创建或返回已有用户。

**请求参数（Query）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 微信登录凭证 |

**响应**

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...",
    "user_id": 1,
    "nickname": null,
    "child_name": null
  }
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 400 | 微信登录失败 |

---

### 1.2 账号密码注册

```
POST /api/auth/register
```

**请求体（JSON）**

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|----------|
| username | string | 是 | 3-32 字符，自动去除首尾空格 |
| password | string | 是 | 6-64 字符 |

**请求示例**

```json
{
  "username": "zhangsan",
  "password": "123456"
}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...",
    "user_id": 2,
    "nickname": null,
    "child_name": null
  }
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 400 | 用户名已存在 |
| 422 | 用户名/密码校验失败 |

---

### 1.3 账号密码登录

```
POST /api/auth/login/account
```

**请求体（JSON）**

| 字段 | 类型 | 必填 |
|------|------|------|
| username | string | 是 |
| password | string | 是 |

**响应**

同注册响应格式。

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 400 | 用户名或密码错误 |

---

## 2. 错题管理

前缀：`/api/errors`  
所有接口需要认证（Bearer Token）。

### 2.1 上传错题图片（同步）

```
POST /api/errors/upload
Content-Type: multipart/form-data
```

上传错题图片，调用 Qwen-VL 进行 AI 识别并存储，自动生成艾宾浩斯复习计划。

**请求参数（Form-Data）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | file | 是 | 图片文件，支持 jpg/jpeg/png/webp，最大 1MB |
| subject | string | 否 | 科目名称，不传则使用 AI 识别结果 |
| note | string | 否 | 备注 |
| child_id | int | 否 | 孩子 ID |
| do_perspective | bool | 否 | 是否做透视矫正，默认 false |

**响应**

```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "subject": "数学",
      "topic": "分数运算",
      "question_text": "计算 1/2 + 1/3",
      "formulas": ["1/2 + 1/3"],
      "figures": null,
      "student_answer": "2/5",
      "correct_answer": "5/6",
      "error_type": "计算错误",
      "error_analysis": "通分错误",
      "tags": ["分数", "加法"],
      "review_plans": [
        {
          "question_id": 1,
          "review_date": "2026-07-04",
          "review_round": 1,
          "interval_days": 1
        }
      ]
    }
  ]
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 400 | 不支持的图片格式 / 图片过大 |
| 500 | 图片识别失败，请重试 |

---

### 2.2 上传错题图片（异步）

```
POST /api/errors/upload/async
Content-Type: multipart/form-data
```

立即返回 task_id，后台异步处理 Qwen-VL 识别。

**请求参数（Form-Data）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | file | 是 | 图片文件 |
| subject | string | 否 | 科目名称 |
| note | string | 否 | 备注 |
| do_perspective | bool | 否 | 是否做透视矫正 |

**响应**

```json
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "pending"
  }
}
```

---

### 2.3 查询异步上传状态

```
GET /api/errors/upload/status/{task_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 异步任务 ID |

**响应（处理中）**

```json
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "pending",
    "created_at": "2026-07-03T10:00:00"
  }
}
```

**响应（已完成）**

```json
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "completed",
    "created_at": "2026-07-03T10:00:00",
    "data": { ... }
  }
}
```

**响应（失败）**

```json
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "failed",
    "created_at": "2026-07-03T10:00:00",
    "error": "识别超时"
  }
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 任务不存在 |

---

### 2.4 错题列表

```
GET /api/errors
```

分页查询错题列表，支持按科目、标签、孩子筛选。

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| subject | string | 否 | - | 按科目筛选 |
| tag | string | 否 | - | 按标签筛选 |
| child_id | int | 否 | - | 按孩子筛选 |
| status | string | 否 | active | 状态：active / archived |
| page | int | 否 | 1 | 页码，≥1 |
| page_size | int | 否 | 20 | 每页条数，1-100 |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "subject": "数学",
        "topic": "分数运算",
        "question_text": "计算 1/2 + 1/3",
        "formulas": ["1/2 + 1/3"],
        "figures": null,
        "student_answer": "2/5",
        "correct_answer": "5/6",
        "error_type": "计算错误",
        "error_analysis": "通分错误",
        "tags": ["分数", "加法"],
        "original_image": "/uploads/abc.jpg",
        "processed_image": null,
        "status": "active",
        "created_at": "2026-07-01 10:00:00",
        "updated_at": null
      }
    ]
  }
}
```

---

### 2.5 错题详情

```
GET /api/errors/{question_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| question_id | int | 错题 ID |

**响应**

同列表中单个 item 的字段结构。

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 错题不存在 |

---

### 2.6 修改错题

```
PUT /api/errors/{question_id}
```

手动纠正 AI 识别结果或补充信息。不允许传入未定义的字段。

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | string | 否 | 科目 |
| topic | string | 否 | 知识点 |
| question_text | string | 否 | 题目文本 |
| formulas | list | 否 | 公式列表 |
| figures | list | 否 | 图形描述列表 |
| student_answer | string | 否 | 学生答案 |
| correct_answer | string | 否 | 正确答案 |
| error_type | string | 否 | 错误类型 |
| error_analysis | string | 否 | 错因分析 |
| tags | list | 否 | 标签列表 |

**响应**

同错题详情。

---

### 2.7 删除错题

```
DELETE /api/errors/{question_id}
```

软删除，将状态标记为 `deleted`。

**响应**

```json
{
  "code": 0,
  "message": "已删除"
}
```

---

## 3. 复习管理

前缀：`/api/review`  
所有接口需要认证。

### 3.1 今日待复习列表

```
GET /api/review/today
```

**响应**

```json
{
  "code": 0,
  "data": {
    "date": "2026-07-03",
    "total": 3,
    "items": [
      {
        "plan_id": 10,
        "question_id": 1,
        "subject": "数学",
        "topic": "分数运算",
        "question_text": "计算 1/2 + 1/3",
        "review_round": 1,
        "interval_days": 1,
        "created_at": "2026-07-01 10:00:00"
      }
    ]
  }
}
```

---

### 3.2 未来复习计划

```
GET /api/review/upcoming
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | int | 否 | 7 | 查询天数范围，1-30 |

**响应**

```json
{
  "code": 0,
  "data": [
    {
      "plan_id": 10,
      "question_id": 1,
      "review_date": "2026-07-04",
      "review_round": 1,
      "interval_days": 1,
      "subject": "数学",
      "topic": "分数运算"
    }
  ]
}
```

---

### 3.3 完成复习

```
POST /api/review/{plan_id}/complete
```

标记复习完成，根据掌握程度自动计算下一轮复习日期。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| plan_id | int | 复习计划 ID |

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mastery_level | int | 是 | 掌握程度 1-5（1=完全不会，5=完全掌握） |

**响应**

```json
{
  "code": 0,
  "message": "复习完成",
  "data": {
    "next_review": {
      "question_id": 1,
      "review_date": "2026-07-06",
      "review_round": 2,
      "interval_days": 3
    }
  }
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 复习计划不存在 |

---

## 4. PDF 导出

前缀：`/api/export`  
所有接口需要认证。

### 4.1 导出错题 PDF

```
GET /api/export/pdf
```

按条件筛选并导出错题为 PDF 文件。

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | string | 否 | 逗号分隔的题目 ID，如 `1,2,3` |
| subject | string | 否 | 按科目筛选 |
| tags | string | 否 | 逗号分隔的标签 |
| date_from | string | 否 | 起始日期，格式 YYYY-MM-DD |
| date_to | string | 否 | 截止日期，格式 YYYY-MM-DD |

**响应**

`Content-Type: application/pdf`，二进制 PDF 文件流。

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 400 | 日期格式错误 |
| 404 | 没有找到符合条件的错题 |
| 501 | PDF 导出功能尚未实现 |

---

### 4.2 导出月度报告 PDF

```
GET /api/export/monthly-report
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | int | 否 | 年份，默认当前年 |
| month | int | 否 | 月份，默认当前月 |
| child_id | int | 否 | 按孩子筛选 |

**响应**

`Content-Type: application/pdf`，二进制 PDF 文件流。

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 该月没有错题记录 |
| 501 | PDF 导出功能尚未实现 |

---

## 5. 统计

前缀：`/api/stats`  
所有接口需要认证。

### 5.1 统计概览

```
GET /api/stats/summary
```

**响应**

```json
{
  "code": 0,
  "data": {
    "total_questions": 120,
    "by_subject": {
      "数学": 60,
      "语文": 30,
      "英语": 30
    },
    "by_error_type": {
      "计算错误": 25,
      "概念混淆": 18,
      "审题不清": 12
    },
    "review_total": 200,
    "review_completed": 150,
    "review_rate": 75.0
  }
}
```

---

### 5.2 每日错题录入趋势

```
GET /api/stats/trend
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | int | 否 | 30 | 查询天数，7-90 |

**响应**

```json
{
  "code": 0,
  "data": [
    { "date": "2026-06-04", "count": 3 },
    { "date": "2026-06-05", "count": 0 },
    { "date": "2026-06-06", "count": 5 }
  ]
}
```

---

### 5.3 掌握程度分布

```
GET /api/stats/mastery
```

**响应**

```json
{
  "code": 0,
  "data": [
    { "level": 1, "label": "完全不会", "count": 10 },
    { "level": 2, "label": "比较生疏", "count": 15 },
    { "level": 3, "label": "基本掌握", "count": 25 },
    { "level": 4, "label": "比较熟练", "count": 20 },
    { "level": 5, "label": "完全掌握", "count": 30 }
  ]
}
```

---

## 6. 用户

前缀：`/api/users`  
所有接口需要认证。

### 6.1 获取用户信息

```
GET /api/users/profile
```

**响应**

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "nickname": "张三妈妈",
    "avatar_url": "https://...",
    "child_name": "张三",
    "child_grade": "三年级",
    "serverchan_key": "SCT..."
  }
}
```

---

### 6.2 更新用户信息

```
PUT /api/users/profile
```

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar_url | string | 否 | 头像 URL |
| child_name | string | 否 | 孩子姓名 |
| child_grade | string | 否 | 孩子年级 |
| serverchan_key | string | 否 | Server酱推送 Key |

**响应**

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "nickname": "张三妈妈",
    "child_name": "张三",
    "child_grade": "四年级",
    "serverchan_key": "SCT..."
  }
}
```

---

## 7. 消息通知

前缀：`/api/notify`  
所有接口需要认证。

### 7.1 记录消息订阅授权

```
POST /api/notify/subscribe
```

前端弹窗授权后调用，记录用户的消息模板订阅。

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_ids | string[] | 是 | 微信消息模板 ID 列表 |

**响应**

```json
{
  "code": 0,
  "message": "订阅成功"
}
```

---

## 8. 孩子管理

前缀：`/api/children`  
所有接口需要认证。

### 8.1 孩子列表

```
GET /api/children
```

**响应**

```json
{
  "code": 0,
  "data": [
    { "id": 1, "name": "张三", "grade": "三年级" },
    { "id": 2, "name": "李四", "grade": "五年级" }
  ]
}
```

---

### 8.2 添加孩子

```
POST /api/children
```

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 孩子姓名 |
| grade | string | 否 | 年级 |

**响应**

```json
{
  "code": 0,
  "data": { "id": 3, "name": "王五", "grade": "二年级" }
}
```

---

### 8.3 修改孩子信息

```
PUT /api/children/{child_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| child_id | int | 孩子 ID |

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 孩子姓名 |
| grade | string | 否 | 年级 |

**响应**

```json
{
  "code": 0,
  "data": { "id": 1, "name": "张三", "grade": "四年级" }
}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 孩子不存在 |

---

### 8.4 删除孩子

```
DELETE /api/children/{child_id}
```

**错误**

| HTTP 状态码 | detail |
|-------------|--------|
| 404 | 孩子不存在 |

**响应**

```json
{
  "code": 0,
  "message": "已删除"
}
```

---

## 9. 健康检查

```
GET /health
```

无需认证。

**响应**

```json
{ "status": "ok" }
```

---

## 附录

### 通用错误响应格式

```json
{
  "detail": "错误描述"
}
```

### 认证失败响应

```json
{
  "detail": "未登录"
}
```

```json
{
  "detail": "登录已过期，请重新登录"
}
```

### 支持的文件格式

图片上传仅支持：`jpg`、`jpeg`、`png`、`webp`，最大 1MB。

### 复习掌握程度说明

| 等级 | 含义 |
|------|------|
| 1 | 完全不会 |
| 2 | 比较生疏 |
| 3 | 基本掌握 |
| 4 | 比较熟练 |
| 5 | 完全掌握 |

掌握程度影响下一轮复习间隔：等级越高，间隔越长。
