"""Seed mock data: users, courses, materials, calendar.
Usage: python -m scripts.seed_mock_data
"""
import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.database import async_session
from app.models.calendar import AcademicCalendar
from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.models.user import User

COURSE_DATA = {
    '计算机学院': [
        ('数据结构与算法', 'shuju-jiegou', '必修', 4.0, '计算机专业核心课程，涵盖线性表、树、图、排序算法等'),
        ('操作系统', 'caozuo-xitong', '必修', 4.0, '进程管理、内存管理、文件系统、I/O等操作系统核心概念'),
        ('计算机网络', 'jisuanji-wangluo', '必修', 3.0, 'TCP/IP协议栈、网络层、传输层、应用层协议'),
        ('数据库系统概论', 'shujuku-xitong', '必修', 3.0, '关系模型、SQL、事务、并发控制、数据库设计'),
    ],
    '数学学院': [
        ('高等数学A（上）', 'gaoshu-a1', '必修', 5.0, '极限、导数、积分、微分方程'),
        ('高等数学A（下）', 'gaoshu-a2', '必修', 5.0, '多元微积分、曲线积分、曲面积分、无穷级数'),
        ('线性代数', 'xianxing-daishu', '必修', 3.0, '矩阵、行列式、向量空间、特征值、二次型'),
        ('概率论与数理统计', 'gailvlun', '必修', 3.0, '随机事件、分布、参数估计、假设检验'),
    ],
    '物理学院': [
        ('大学物理（上）', 'daxue-wuli1', '必修', 4.0, '力学、热学、电磁学基础'),
        ('大学物理（下）', 'daxue-wuli2', '必修', 4.0, '光学、近代物理、量子力学导论'),
    ],
    '外国语学院': [
        ('大学英语（综合）1', 'daying1', '必修', 2.0, '综合英语听说读写训练，基础级'),
        ('大学英语（综合）2', 'daying2', '必修', 2.0, '综合英语听说读写训练，进阶级'),
    ],
    # ── New colleges (3× expansion) ──
    '经济学院': [
        ('微观经济学', 'weiguan-jingji', '必修', 3.0, '供求理论、消费者行为、厂商理论、市场结构'),
        ('宏观经济学', 'hongguan-jingji', '必修', 3.0, '国民收入、IS-LM模型、AD-AS模型、经济增长'),
        ('计量经济学', 'jiliang-jingji', '必修', 3.0, '回归分析、假设检验、时间序列、面板数据'),
    ],
    '法学院': [
        ('宪法学', 'xianfa-xue', '必修', 3.0, '宪法基本理论、国家制度、公民基本权利与义务'),
        ('民法学', 'minfa-xue', '必修', 4.0, '民法总则、物权法、合同法、侵权责任法'),
        ('刑法学', 'xingfa-xue', '必修', 4.0, '犯罪构成要件、刑罚体系、刑法分则重点罪名'),
    ],
    '文学与新闻学院': [
        ('中国古代文学', 'gudai-wenxue', '必修', 3.0, '先秦至近代文学发展脉络与经典作品赏析'),
        ('现代汉语', 'xiandai-hanyu', '必修', 2.0, '语音、词汇、语法、修辞等现代汉语基础知识'),
        ('新闻学概论', 'xinwenxue-gailun', '必修', 3.0, '新闻传播原理、媒介伦理、新闻写作基础'),
    ],
    '化学学院': [
        ('有机化学', 'youji-huaxue', '必修', 4.0, '烃类、醇酚醚、醛酮、羧酸及其衍生物'),
        ('无机化学', 'wuji-huaxue', '必修', 4.0, '元素周期律、化学键理论、配位化学、酸碱理论'),
        ('分析化学', 'fenxi-huaxue', '必修', 3.0, '定量分析、仪器分析、色谱与光谱技术'),
    ],
    '生命科学学院': [
        ('生物化学', 'shengwu-huaxue', '必修', 4.0, '蛋白质、核酸、酶学、代谢途径与调控'),
        ('分子生物学', 'fenzi-shengwuxue', '必修', 3.0, 'DNA复制、转录、翻译、基因表达调控'),
        ('遗传学', 'yichuanxue', '必修', 3.0, '孟德尔遗传、连锁交换、群体遗传、分子遗传'),
    ],
    '电子信息学院': [
        ('信号与系统', 'xinhao-xitong', '必修', 4.0, '连续与离散信号分析、傅里叶变换、拉普拉斯变换'),
        ('数字电路', 'shuzi-dianlu', '必修', 3.0, '逻辑门、组合电路、时序电路、PLD设计'),
        ('通信原理', 'tongxin-yuanli', '必修', 4.0, '模拟与数字通信、调制解调、信道编码、同步技术'),
    ],
    '电气工程学院': [
        ('电路原理', 'dianlu-yuanli', '必修', 4.0, '电路基本定律、网络定理、一阶二阶电路分析'),
        ('电机学', 'dianji-xue', '必修', 3.0, '变压器、直流电机、异步电机、同步电机原理'),
        ('电力系统分析', 'dianli-xitong', '必修', 4.0, '潮流计算、短路分析、稳定分析、电力市场'),
    ],
    '建筑与环境学院': [
        ('建筑设计基础', 'jianzhu-sheji', '必修', 4.0, '建筑设计原理与方法、空间构成、建筑表达'),
        ('结构力学', 'jiegou-lixue', '必修', 4.0, '静定结构、超静定结构、矩阵位移法、有限元基础'),
        ('环境工程原理', 'huanjing-gongcheng', '必修', 3.0, '水处理、大气污染控制、固废处理与资源化'),
    ],
}

MATERIAL_TEMPLATES = [
    # ── Original 10 ──
    {'title': '{course} 历年期末考试真题合集', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末复习提纲（重点版）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 课堂笔记（完整版）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 课后习题答案', 'category': '习题答案', 'format': 'pdf'},
    {'title': '{course} 实验报告模板', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 教材电子版', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 期中测试题及解答', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末重点总结', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} PPT课件合集', 'category': '课件', 'format': 'pptx'},
    {'title': '{course} 考研真题汇编', 'category': '考试资料', 'format': 'pdf'},
    # ── New 20 ──
    {'title': '{course} 思维导图（全章节）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 知识点背诵手册', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 经典例题精讲', 'category': '习题答案', 'format': 'pdf'},
    {'title': '{course} 期末模拟试卷（3套）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 课程设计报告参考', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 教学视频配套讲义', 'category': '课件', 'format': 'pdf'},
    {'title': '{course} 公式速查手册', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 名词解释汇编', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 历年期中考试真题', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 章节练习题集', 'category': '习题答案', 'format': 'pdf'},
    {'title': '{course} 学霸手写笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 实验操作指南', 'category': '实验报告', 'format': 'pdf'},
    {'title': '{course} 期末考点预测', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 案例分析集', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 配套习题解答（全）', 'category': '习题答案', 'format': 'pdf'},
    {'title': '{course} 教学大纲与进度表', 'category': '课件', 'format': 'pdf'},
    {'title': '{course} 易错题专项训练', 'category': '习题答案', 'format': 'pdf'},
    {'title': '{course} 读书笔记与感悟', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 专题研究报告', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 学长学姐经验谈', 'category': '复习提纲', 'format': 'pdf'},
]

SEMESTERS = [
    '2023-2024-1', '2023-2024-2',
    '2024-2025-1', '2024-2025-2',
    '2025-2026-1', '2025-2026-2',
]

TEACHERS = [
    '张教授', '李教授', '王教授', '刘教授', '陈教授',
    '赵老师', '周老师', '孙老师',
    '黄教授', '吴教授', '郑教授', '杨教授', '朱教授',
    '马老师', '胡老师', '林老师', '何老师', '郭老师',
    '谢教授', '韩教授', '唐老师', '冯老师', '曹老师', '许老师',
]

CALENDAR_EVENTS = [
    # ── 2023-2024-1 ──
    ('2023-2024-1', '开学', '开学', '2023-09-01', '2023-09-01'),
    ('2023-2024-1', '选课周', '选课', '2023-09-01', '2023-09-07'),
    ('2023-2024-1', '国庆假期', '假期', '2023-10-01', '2023-10-07'),
    ('2023-2024-1', '期中考试周', '考试', '2023-11-13', '2023-11-19'),
    ('2023-2024-1', '英语四六级考试', '考试', '2023-12-16', '2023-12-16'),
    ('2023-2024-1', '期末复习周', '复习', '2024-01-01', '2024-01-07'),
    ('2023-2024-1', '期末考试周', '考试', '2024-01-08', '2024-01-21'),
    ('2023-2024-1', '寒假', '假期', '2024-01-22', '2024-02-25'),
    # ── 2023-2024-2 ──
    ('2023-2024-2', '开学', '开学', '2024-02-26', '2024-02-26'),
    ('2023-2024-2', '选课周', '选课', '2024-02-26', '2024-03-03'),
    ('2023-2024-2', '期中考试周', '考试', '2024-04-22', '2024-04-28'),
    ('2023-2024-2', '英语四六级考试', '考试', '2024-06-15', '2024-06-15'),
    ('2023-2024-2', '期末复习周', '复习', '2024-07-01', '2024-07-07'),
    ('2023-2024-2', '期末考试周', '考试', '2024-07-08', '2024-07-21'),
    ('2023-2024-2', '暑假', '假期', '2024-07-22', '2024-08-31'),
    # ── 2024-2025-1 ──
    ('2024-2025-1', '开学', '开学', '2024-09-01', '2024-09-01'),
    ('2024-2025-1', '选课周', '选课', '2024-09-01', '2024-09-07'),
    ('2024-2025-1', '国庆假期', '假期', '2024-10-01', '2024-10-07'),
    ('2024-2025-1', '期中考试周', '考试', '2024-11-11', '2024-11-17'),
    ('2024-2025-1', '英语四六级考试', '考试', '2024-12-14', '2024-12-14'),
    ('2024-2025-1', '考研初试', '考试', '2024-12-21', '2024-12-23'),
    ('2024-2025-1', '期末复习周', '复习', '2024-12-30', '2025-01-05'),
    ('2024-2025-1', '期末考试周', '考试', '2025-01-06', '2025-01-19'),
    ('2024-2025-1', '寒假', '假期', '2025-01-20', '2025-02-23'),
    # ── 2024-2025-2 ──
    ('2024-2025-2', '开学', '开学', '2025-02-24', '2025-02-24'),
    ('2024-2025-2', '选课周', '选课', '2025-02-24', '2025-03-02'),
    ('2024-2025-2', '期中考试周', '考试', '2025-04-21', '2025-04-27'),
    ('2024-2025-2', '英语四六级考试', '考试', '2025-06-14', '2025-06-14'),
    ('2024-2025-2', '期末复习周', '复习', '2025-06-30', '2025-07-06'),
    ('2024-2025-2', '期末考试周', '考试', '2025-07-07', '2025-07-20'),
    ('2024-2025-2', '暑假', '假期', '2025-07-21', '2025-08-31'),
    # ── 2025-2026-1 ──
    ('2025-2026-1', '开学', '开学', '2025-09-01', '2025-09-01'),
    ('2025-2026-1', '选课周', '选课', '2025-09-01', '2025-09-07'),
    ('2025-2026-1', '国庆假期', '假期', '2025-10-01', '2025-10-07'),
    ('2025-2026-1', '期中考试周', '考试', '2025-11-10', '2025-11-16'),
    ('2025-2026-1', '英语四六级考试', '考试', '2025-12-13', '2025-12-13'),
    ('2025-2026-1', '考研初试', '考试', '2025-12-20', '2025-12-22'),
    ('2025-2026-1', '期末复习周', '复习', '2025-12-29', '2026-01-04'),
    ('2025-2026-1', '期末考试周', '考试', '2026-01-05', '2026-01-18'),
    ('2025-2026-1', '寒假', '假期', '2026-01-19', '2026-02-22'),
    # ── 2025-2026-2 ──
    ('2025-2026-2', '开学', '开学', '2026-02-23', '2026-02-23'),
    ('2025-2026-2', '选课周', '选课', '2026-02-23', '2026-03-01'),
    ('2025-2026-2', '期中考试周', '考试', '2026-04-20', '2026-04-26'),
    ('2025-2026-2', '英语四六级考试', '考试', '2026-06-13', '2026-06-13'),
    ('2025-2026-2', '期末复习周', '复习', '2026-06-29', '2026-07-05'),
    ('2025-2026-2', '期末考试周', '考试', '2026-07-06', '2026-07-19'),
    ('2025-2026-2', '暑假', '假期', '2026-07-20', '2026-08-31'),
]

MOCK_USERS = [
    {'phone': '13908000001', 'nickname': '川大课小栈', 'role': 'student', 'trust_score': 95, 'display_name': '课栈小助手'},
    {'phone': '13908000002', 'nickname': '学霸小明', 'role': 'student', 'trust_score': 88, 'display_name': '小明同学'},
    {'phone': '13908000003', 'nickname': '考研达人', 'role': 'student', 'trust_score': 92, 'display_name': '考研学长'},
    {'phone': '13908000004', 'nickname': '笔记侠', 'role': 'student', 'trust_score': 85, 'display_name': '笔记达人'},
    {'phone': '13908000005', 'nickname': '实验小能手', 'role': 'student', 'trust_score': 90, 'display_name': '实验达人'},
    {'phone': '13908000006', 'nickname': '编程高手', 'role': 'student', 'trust_score': 87, 'display_name': '代码小哥'},
    {'phone': '13908000007', 'nickname': '英语达人', 'role': 'student', 'trust_score': 86, 'display_name': '英语学霸'},
    {'phone': '13908000008', 'nickname': '复习小王子', 'role': 'student', 'trust_score': 89, 'display_name': '复习助手'},
]

MAINTAINER_PHONE = '13908000000'


def _fake_encrypt(plain: str) -> str:
    """Mock encryption — real impl uses AES-256-GCM."""
    return plain


async def seed():
    async with async_session() as db:
        # ── 1. Get existing colleges ──
        result = await db.execute(select(College))
        colleges = {c.name: c for c in result.scalars().all()}
        if not colleges:
            print('No colleges found. Run seed_colleges.py first.')
            return

        # ── 2. Create mock users ──
        mock_users: dict[str, User] = {}
        for mu in MOCK_USERS:
            result = await db.execute(select(User).where(User.phone == mu['phone']))
            user = result.scalar()
            if not user:
                user = User(
                    phone=_fake_encrypt(mu['phone']),
                    nickname=mu['nickname'],
                    role=mu['role'],
                    trust_score=mu['trust_score'],
                    public_display_name=mu['display_name'],
                )
                db.add(user)
                await db.flush()
            mock_users[mu['phone']] = user

        result = await db.execute(select(User).where(User.phone == MAINTAINER_PHONE))
        maintainer = result.scalar()
        if not maintainer:
            maintainer = User(
                phone=_fake_encrypt(MAINTAINER_PHONE),
                nickname='管理员',
                role='maintainer',
                trust_score=100,
                public_display_name='川大课栈管理员',
            )
            db.add(maintainer)
            await db.flush()

        print(f'Created/verified {len(mock_users)} mock users + 1 maintainer')

        # ── 3. Create courses ──
        existing_courses = (await db.execute(select(Course.name))).scalars().all()
        new_courses: list[Course] = []
        for college_name, courses in COURSE_DATA.items():
            college = colleges.get(college_name)
            if not college:
                continue
            for name, slug, cat, credit, desc in courses:
                if name in existing_courses:
                    continue
                course = Course(
                    college_id=college.id,
                    name=name,
                    slug=slug,
                    category=cat,
                    credit=credit,
                    description=desc,
                    aliases=[],
                )
                db.add(course)
                new_courses.append(course)
        await db.flush()
        print(f'Created {len(new_courses)} courses')

        # ── 4. Create materials ──
        all_courses = (await db.execute(select(Course))).scalars().all()
        existing_titles = set(
            (await db.execute(select(Material.title))).scalars().all()
        )
        new_materials: list[Material] = []
        user_list = list(mock_users.values())

        for course in all_courses:
            n_templates = min(random.randint(5, 10), len(MATERIAL_TEMPLATES))
            templates = random.sample(MATERIAL_TEMPLATES, n_templates)
            contributor = random.choice(user_list)
            for tpl in templates:
                title = tpl['title'].format(course=course.name[:15])
                if title in existing_titles:
                    continue
                days_ago = random.randint(1, 365)
                dl = random.randint(0, 800)
                rc = random.randint(0, dl + random.randint(0, 80))
                m = Material(
                    course_id=course.id,
                    title=title,
                    description=f'{course.name} 相关{tpl["category"]}，由同学整理上传',
                    category=tpl['category'],
                    semester=random.choice(SEMESTERS),
                    teacher=random.choice(TEACHERS),
                    source_type='hosted',
                    format=tpl['format'],
                    file_size=random.randint(200_000, 50_000_000),
                    file_hash=f'abc{random.randint(10000,99999)}def{random.randint(10000,99999)}',
                    trust_status=random.choice(['community_verified', 'maintainer_picked', 'unverified']),
                    review_status='approved',
                    average_rating=round(random.uniform(1.5, 5.0), 2),
                    rating_count=rc,
                    download_count=dl,
                    contributor_id=contributor.id,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                    updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_ago)),
                )
                db.add(m)
                new_materials.append(m)
                existing_titles.add(title)

        await db.flush()
        print(f'Created {len(new_materials)} materials')

        # ── 5. Create academic calendar ──
        result = await db.execute(select(AcademicCalendar.event_name))
        existing_events = set(result.scalars().all())
        new_events = 0
        for semester, name, tag, start, end in CALENDAR_EVENTS:
            if name in existing_events:
                continue
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
            year = start_date.year
            db.add(AcademicCalendar(
                year=year,
                semester=semester,
                event_name=name,
                event_tag=tag,
                start_date=start_date,
                end_date=end_date,
            ))
            new_events += 1

        await db.commit()
        print(f'Created {new_events} calendar events')

        # ── Summary ──
        cc = (await db.execute(select(func.count()).select_from(Course))).scalar()
        mc = (await db.execute(
            select(func.count()).select_from(Material).where(Material.review_status == 'approved')
        )).scalar()
        uc = (await db.execute(select(func.count()).select_from(User))).scalar()
        evc = (await db.execute(select(func.count()).select_from(AcademicCalendar))).scalar()
        print(f'Done. DB now has: {len(colleges)} colleges, {cc} courses, {mc} approved materials, {uc} users, {evc} calendar events')


if __name__ == '__main__':
    asyncio.run(seed())
