# hncu-sdk: 湖南城市学院 Python 开发工具包

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`hncu-sdk` 是面向**湖南城市学院（HNCU）**在校师生与校园开发者的 Python 自动化开发工具包。
本项目完整封装了学校**移动校园后端 API** 以及 **正方教务管理系统（JWGLXT）** 的核心功能，提供极简的 Python 接口、自动化的 CAS 单点登录（SSO）票据维护，以及开箱即用的结构化数据类型。

---

## 🖥️ 终端效果演示 (Terminal Demo)

<p align="center">
  <img src="assets/demo.gif" alt="HNCU SDK 终端字符解码与考试日程查询演示" width="880">
</p>

---

## ✨ 核心特性

1. **统一多维认证体系**：
   * 自动处理移动校园端 `AES-128-ECB` 数据加解密与 `Access-Token` 动态维护。
   * 支持统一身份认证平台 Web 端短信验证码免密登录与 Barrett RSA 密码加密。
   * 全自动模拟 CAS 单点登录（SSO）获取 `CASTGC`、`route`、`sid`、`JSESSIONID` 等关键 Cookies，免密打通正方教务系统。
2. **正方教务深度支持**：
   * **一键全自动教学评价**：秒级自动遍历所有未评课程，自动提取打分指标 GUID 树，智能轮换优质评语池批量提交。
   * **空闲自习室 / 考研教室深度检索**：支持按黄金时段（全天连续空闲 `all_day`、晚自习 `evening`、上午 `morning`）、教学楼别名及最低座位数要求智能过滤。
   * 学籍完整详细档案查询（姓名拼音、性别、身份证号、民族、政治面貌、籍贯、学制等）。
   * 成绩查询（包含绩点、学分、平时成绩、期末卷面、补考/重修标识）。
   * 学期课表查询（周次、星期、节次、教师、教室自动解析）。
   * 期末考试日程安排与考场座位查询。
3. **智慧门户与一卡通服务 (v0.4.0)**：
   * 一卡通实时余额查询、卡挂失与冻结状态监控。
   * 智慧门户个人综合档案与一寸高清免冠照片 Base64 提取。
4. **校园服务与资讯**：
   * 班级通讯录与学生联系方式获取。
   * 个人档案及教工信息查询。
   * 官方 6 大分类新闻通知（通知公告、会议安排、教务通知、学工通知、城院新闻、媒体城院）。
5. **类型友好 & 容错健壮**：
   * 全流程内置 Python Dataclass 强类型模型（`StudentProfile`, `StudentDetail`, `EmptyClassroomItem`, `GradeItem`, `CourseItem`, `ExamItem`, `EvaluationSummary`, `EvaluationCourseItem`, `ECardInfo`, `PortalProfile` 等）。
   * 内置对教务端脏数据与畸变控制字符（如 `\u0004` 等截断符）的自动清洗容错。

---

## 📦 安装说明

### 本地开发安装
克隆仓库后，进入 `hncu_sdk` 目录直接安装：

```bash
git clone https://github.com/bobisuperplus-sys/hncu-sdk.git
cd hncu-sdk
pip install -e .
```

或者通过依赖列表安装：
```bash
pip install -r requirements.txt
```

---

## 🚀 快速上手 (Quick Start)

### 1. 登录并查询历史成绩

```python
from hncu import HncuClient, Term

# 初始化客户端
client = HncuClient()

# 1. 登录（自动建立移动校园会话并打通正方教务系统单点登录）
profile = client.login(user_id="你的学号", password="你的密码")

print(f"欢迎你，{profile.user_name} 同学！")
print(f"所属学院: {profile.department} | 班级: {profile.class_name}")

# 2. 查询成绩 (默认查询全部，也可指定年份和学期)
# 学期支持传入直觉数字: 1 (第1学期), 2 (第2学期), 3 (第3学期/暑假实习)，或使用 Term 枚举
grades = client.get_grades(year=2023, term=1)

for g in grades:
    print(f"【{g.course_name}】({g.term_display}) 成绩: {g.score} | 绩点: {g.grade_point} | 学分: {g.credit}")
```

### 2. 获取个人课表

```python
# 查询 2023 学年第 1 学期课表 (传 1 或 Term.FIRST 均可，底层自动映射教务系统代码)
courses = client.get_schedule(year=2023, term=1)
for c in courses:
    print(f"星期{c.day_of_week} {c.section_display} - {c.course_name} ({c.classroom}, 教师: {c.teacher})")
```

### 3. 获取班级通讯录

```python
members = client.get_class_address_book()
for m in members:
    print(f"{m.user_name} ({m.user_id}) - 电话: {m.phone} - 宿舍: {m.dormitory}")
```

### 4. 查询学籍详细档案 (正方教务)

```python
detail = client.get_student_detail()
print(f"姓名: {detail.user_name} ({detail.pinyin}) | 身份证: {detail.id_card_number}")
print(f"政治面貌: {detail.political_status} | 民族: {detail.nation} | 籍贯: {detail.native_place}")
print(f"学院: {detail.department} | 专业: {detail.major} | 学制: {detail.schooling_years}年")
```

### 5. 检索空闲教室 (正方教务)

```python
# 查询 2024 学年第 1 学期，第 1 周星期一，第 1-2 节的空闲教室
classrooms = client.get_empty_classrooms(
    year=2024,
    term=1,
    week=1,
    day_of_week=1,
    section_start=1,
    section_end=2
)
for room in classrooms:
    print(f"[{room.building_name}] {room.room_name} - 座位数: {room.seats} (类别: {room.room_type})")
```

### 6. 获取校园最新教务通知（公开接口，无需登录）

```python
from hncu import HncuClient, NewsCategory

client = HncuClient()
news = client.get_news(category=NewsCategory.ACADEMIC, page=1, page_size=5)

for item in news:
    print(f"[{item.date}] {item.title}")
    print(f"链接: {item.url}\n")
```

### 7. 一键全自动教学评价 (v0.5.0)

```python
# 1. 查询当前学期评价进度概况
summary = client.get_evaluation_summary()
print(f"已评: {summary.submitted_count} 门, 剩余未评: {summary.unrated_count} 门")

# 2. 一键全自动秒级评教（自动随机轮换优质评语并提交锁定）
if not summary.is_all_completed:
    result = client.auto_evaluate_all(submit=True)
    print(f"评教完成！成功: {result['success_count']} 门, 失败: {result['failed_count']} 门")
```

### 8. 深度考研教室 / 空闲自习室检索 (v0.5.0)

```python
# 检索一教全天 (1-10节) 连续空闲、座位数 >= 60 的优质自习教室
rooms = client.query_study_rooms(
    period="all_day",   # 支持: all_day(全天), morning(上午), afternoon(下午), evening(晚自习)
    building="1教",     # 支持智能别名识别
    min_seats=60,       # 过滤最低座位数要求
)
for r in rooms:
    print(f"[{r.building_name}] {r.room_name} - 座位数: {r.seats} ({r.room_type})")
```

### 9. 智慧门户与一卡通实时数据查询 (v0.4.0)

```python
# 1. 一卡通实时余额与状态
ecard = client.portal.get_ecard_info()
print(f"一卡通余额: {ecard.balance} 元 | 卡状态: {ecard.loss_status} | 冻结状态: {ecard.freeze_status}")

# 2. 门户个人综合档案与一寸高清照片
profile = client.portal.get_profile()
print(f"学号: {profile.user_id} | 姓名: {profile.user_name} | 学院: {profile.department}")
print(f"身份证: {profile.id_card_masked} | 是否含头像: {bool(profile.photo_base64)}")
```

---

## 📂 项目模块化多目录架构

```text
hncu_sdk/
├── hncu/                         # SDK 核心源码包
│   ├── __init__.py               # 顶级统一入口（导出门面、服务、模型、常量）
│   ├── client.py                 # HncuClient 外观门面 (Facade)，聚合所有子系统 API
│   ├── core/                     # 底层公共核心模块
│   │   ├── __init__.py
│   │   ├── session.py            # HncuSession 统一会话管理（防代理劫持、Cookie安全获取）
│   │   ├── crypto.py             # AES-128-ECB 与畸形控制字符清洗引擎
│   │   ├── constants.py          # 路由表、Header常量、枚举（Term, NewsCategory等）
│   │   ├── exceptions.py         # 业务与网络异常定义体系
│   │   └── models.py             # 全系统 Dataclass 强类型实体模型
│   ├── auth/                     # 统一身份认证与单点登录模块
│   │   ├── __init__.py
│   │   └── auth_service.py       # 移动端 Token 认证与正方教务 CAS SSO 双层打通
│   ├── jwglxt/                   # 正方教务系统子服务（单文件单功能）
│   │   ├── __init__.py
│   │   ├── grades.py             # 成绩查询服务（历年全部考试、平时与期末拆解）
│   │   ├── schedule.py           # 个人学期课表查询服务
│   │   ├── exams.py              # 期末考试日程与考场座位服务
│   │   ├── classrooms.py         # 空闲自习教室与考研教室检索服务
│   │   ├── student.py            # 学籍详细档案抓取与清洗服务
│   │   └── evaluation.py         # 一键全自动教学评价服务 (v0.5.0)
│   ├── portal/                   # 智慧门户与一卡通子服务 (v0.4.0)
│   │   ├── __init__.py
│   │   ├── models.py             # 一卡通与门户身份强类型数据模型
│   │   └── portal_service.py     # 一卡通余额、状态与综合档案服务
│   ├── mobile/                   # 移动校园后端子服务（单文件单功能）
│   │   ├── __init__.py
│   │   ├── address_book.py       # 班级通讯录与人员名单服务
│   │   ├── user_info.py          # 移动端用户详细资料服务
│   │   └── calendar.py           # 学年学期校历日程服务
│   ├── news/                     # 校园资讯子服务
│   │   ├── __init__.py
│   │   └── news_service.py       # 6 大分类官方新闻与教务通知服务（公开免登）
│   └── account/                  # 账号安全子服务
│       ├── __init__.py
│       └── account_service.py    # 统一身份认证账号核验与密码修改服务
├── examples/                     # 独立单元测试与功能演示目录
│   ├── terminal_fx.py            # 终端 Anime.js 风格 scrambleText 动态字符解码特效引擎
│   ├── test_crypto.py            # [单测 1] 底层加解密与畸变清洗闭环测试 (离线)
│   ├── test_news.py              # [单测 2] 校园官方资讯与通知抓取测试 (免登)
│   ├── test_auth.py              # [单测 3] 移动端认证与教务 CAS SSO 票据获取测试
│   ├── test_portal.py            # [单测 4] 智慧门户档案与一卡通模型及业务测试
│   ├── test_evaluation.py        # [单测 5] 教学评价指标逆向与考研自习室多维检索测试
│   ├── test_grades.py            # [单测 6] 正方教务学生历年考试成绩查询测试
│   ├── test_schedule.py          # [单测 7] 正方教务个人学期课程表查询测试
│   ├── test_exams.py             # [单测 8] 正方教务期末考试考场日程查询测试
│   ├── test_classrooms.py        # [单测 9] 正方教务空闲自习教室位掩码检索测试
│   ├── test_student_detail.py    # [单测 10] 正方教务个人完整学籍详细档案测试
│   ├── test_address_book.py      # [单测 11] 移动校园班级通讯录成员检索测试
│   ├── test_calendar.py          # [单测 12] 移动校园当前学年学期校历日程测试
│   ├── example_portal.py         # 智慧门户与一卡通调用示例
│   └── example_evaluation.py     # 全自动教学评价与考研自习室调用示例
├── pyproject.toml                # 标准 Python 打包构建规范 (v0.5.0)
├── requirements.txt              # 核心依赖项 (requests, pycryptodome, beautifulsoup4)
└── README.md                     # 项目技术说明文档
```

---

## 🧪 单元测试与原型验证 (Unit Testing)

所有验证脚本均置于 `examples/` 目录下，**严格遵循一个测试脚本对应一个独立功能模块**的原则。测试脚本内置了类似于 **Anime.js `scrambleText`** 的终端动态乱码渐变解码动效，在真实终端输出中提供科技感的字符逐步解密揭示体验！

> **共享认证设计**：各教务与移动端测试单元均通过 `from test_auth import get_authenticated_client` 复用统一的认证会话，无需在每个单测中重复输入账号密码。

### 1. 离线/免登录测试单元
```bash
# 测试底层 AES 加解密与畸变清洗 (无需网络)
python3 examples/test_crypto.py

# 测试校园官方资讯与教务通知 (免登)
python3 examples/test_news.py
```

### 2. 教务与移动端核心服务测试单元
您可以通过配置环境变量 `HNCU_USER` 和 `HNCU_PASS` 直接运行（或直接运行脚本通过终端安全隐藏输入密码）；对于需要指定学年和学期的模块，可通过 `HNCU_YEAR` 与 `HNCU_TERM` 灵活控制：

```bash
# 必填认证凭据
export HNCU_USER="你的学号"
export HNCU_PASS="你的密码"

# 可选学年与学期参数（支持 1: 第1学期, 2: 第2学期, 3: 暑假实习/短学期，底层自动映射对应代码）
export HNCU_YEAR="2024"       # 学年 (如 2023, 2024，不填则默认当前或全部)
export HNCU_TERM="1"          # 学期 (1: 上学期, 2: 下学期, 3: 暑假实习)

# 1. 认证单点登录测试
python3 examples/test_auth.py

# 2. 成绩查询测试 (支持 HNCU_YEAR / HNCU_TERM)
python3 examples/test_grades.py

# 3. 课表查询测试 (支持 HNCU_YEAR / HNCU_TERM)
python3 examples/test_schedule.py

# 4. 考试日程测试 (支持 HNCU_YEAR / HNCU_TERM)
python3 examples/test_exams.py

# 5. 空闲自习教室检索测试 (支持 HNCU_YEAR / HNCU_TERM)
python3 examples/test_classrooms.py

# 6. 学籍详细档案抓取测试
python3 examples/test_student_detail.py

# 7. 班级通讯录检索测试
python3 examples/test_address_book.py

# 8. 校历日程信息测试
python3 examples/test_calendar.py
```

---

## ⚠️ 免责声明 (Disclaimer)

1. 本项目仅供技术交流与学术学习研究使用，作者不对使用本项目造成的任何直接或间接后果负责。
2. 严禁利用本项目进行高频恶意爬取、暴力破解或对校园网络进行 DOS 攻击。
3. 请严格遵守《中华人民共和国网络安全法》以及学校相关网络管理规范。

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 许可开源。
