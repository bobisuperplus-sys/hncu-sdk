"""
HNCU SDK 示例：一键全自动教学评价与深度空闲自习室检索 (v0.5.0)

本示例展示：
1. 教学评价概况统计与各门课程评教进度查询
2. 一键全自动批量好评（高分指标自动勾选，优质评语库智能轮换）
3. 考研自习室/空闲教室深度检索（时段预设、楼栋、座位数智能过滤）
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuClient, Term


def demo_study_rooms(client: HncuClient):
    print("\n" + "=" * 60)
    print(" 📖 功能二：全校空闲自习室 / 考研教室深度多维检索")
    print("=" * 60)

    # 1. 检索全天 (1-10 节) 连续空闲的考研自习室 (要求至少 60 座位)
    print("\n[检索 1] 正在检索一教全天 (1-10节) 连续空闲、座位数 >= 60 的优质自习教室...")
    rooms_all_day = client.query_study_rooms(
        period="all_day",
        building="1教",
        min_seats=60,
    )
    print(f"-> 找到 {len(rooms_all_day)} 间全天空闲自习室：")
    for r in rooms_all_day[:5]:
        print(f"   🏛️  [{r.building_name}] {r.room_name:<12} 座位数: {r.seats:<4} 类型: {r.room_type}")

    # 2. 检索晚自习 (9-10 节) 空闲教室
    print("\n[检索 2] 正在检索晚自习 (9-10节) 空闲教室...")
    rooms_evening = client.query_study_rooms(
        period="evening",
        min_seats=30,
        page_size=10,
    )
    print(f"-> 找到 {len(rooms_evening)} 间晚自习教室：")
    for r in rooms_evening[:5]:
        print(f"   🌙 [{r.building_name}] {r.room_name:<12} 座位数: {r.seats:<4} 校区: {r.campus_name}")


def demo_evaluation(client: HncuClient):
    print("\n" + "=" * 60)
    print(" ⭐ 功能一：正方教务教学评价 (学生评价) 概况与一键全自动评教")
    print("=" * 60)

    try:
        # 1. 查询当前学期评价概况
        summary = client.get_evaluation_summary()
        print(f"\n[评教概况]")
        print(f"  已提交门次: {summary.submitted_count}")
        print(f"  暂存保存门次: {summary.saved_count}")
        print(f"  未评门次: {summary.unrated_count}")
        print(f"  是否全部评完: {'✅ 是' if summary.is_all_completed else '❌ 否'}")
        print(f"  系统提示: {summary.prompt_message}")

        # 2. 获取所有课程及教师列表
        courses = client.get_evaluable_courses()
        print(f"\n[课程评价列表 (共 {len(courses)} 门次)]")
        for idx, c in enumerate(courses, start=1):
            status_tag = "✅ 已提交" if c.is_submitted else ("⏳ 已保存" if c.is_saved else "⚠️ 未评")
            score_tag = f"(得分: {c.score})" if c.score else ""
            print(f"  {idx:2d}. {status_tag} {c.course_name:<20} | 教师: {c.teacher_name:<8} {score_tag}")

        # 3. 演示一键全自动批量评价 (若有未评课程则自动秒级打分提交)
        if not summary.is_all_completed:
            print("\n正在启动一键全自动评教...")
            res = client.auto_evaluate_all(submit=True, delay=0.5)
            print(f"批量评价结果: 成功 {res['success_count']} 门, 失败 {res['failed_count']} 门")
        else:
            print("\n🎉 本学期所有课程已全部完成评价，无需重复提交！")

    except Exception as e:
        print(f"评价模块调用提示 (如未登录或会话过期): {e}")


def main():
    print("=" * 60)
    print(" HNCU SDK v0.5.0 全自动评教与考研教室深度检索功能演示")
    print("=" * 60)

    client = HncuClient()

    # 提示：登录流程可以使用 client.login(学号, 密码) 或 client.login_web(...)
    # 如已登录，直接调用相关方法即可：
    # client.login("2021000000", "password")

    print("\n[模拟检索演示] 深度考研教室查询:")
    # 模拟演示时段预设转换逻辑
    demo_study_rooms(client)


if __name__ == "__main__":
    main()
