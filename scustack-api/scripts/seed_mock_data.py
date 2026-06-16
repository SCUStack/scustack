"""Seed mock data: users, courses, materials (with parts), calendar, badges.
Usage: python -m scripts.seed_mock_data
"""
import asyncio
import random
from datetime import date, datetime, timedelta, timezone

import bcrypt
from sqlalchemy import func, select

from app.core.database import async_session
from app.core.security import encrypt_pii
from app.models.calendar import AcademicCalendar
from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.models.user import User
from app.models.user_badge import UserBadge

# ══════════════════════════════════════════════════════════════════════
# College metadata — descriptions for each college
# ══════════════════════════════════════════════════════════════════════

COLLEGE_META = {
    '经济学院': ('国家级重点学科，涵盖理论经济学、应用经济学、金融学等方向，培养经济分析与管理人才。', 'https://econ.scu.edu.cn'),
    '法学院': ('中国法学教育重镇，拥有法学一级学科博士点，在宪法与行政法、民商法、刑法等领域具有深厚学术积淀。', 'https://law.scu.edu.cn'),
    '文学与新闻学院': ('文理工医交叉融合，拥有中国语言文学、新闻传播学两个一级学科博士点，培养文化传播与创意产业人才。', 'https://lj.scu.edu.cn'),
    '外国语学院': ('涵盖英、日、俄、德、法、西班牙等多语种，拥有外国语言文学一级学科博士点。', 'https://flc.scu.edu.cn'),
    '艺术学院': ('集美术、设计、音乐、舞蹈、戏剧影视于一体的综合性艺术学院，注重艺术创新与实践。', 'https://art.scu.edu.cn'),
    '数学学院': ('基础数学国家理科基地，入选国家基础学科拔尖学生培养计划2.0，在代数、几何、拓扑等领域享有盛誉。', 'https://math.scu.edu.cn'),
    '物理学院': ('物理学国家理科基地，拥有物理学一级学科博士点，在凝聚态物理、原子分子物理等方向实力雄厚。', 'https://physics.scu.edu.cn'),
    '化学学院': ('化学国家理科基地，绿色化学与可持续催化研究国内领先，拥有化学一级学科博士点。', 'https://chem.scu.edu.cn'),
    '生命科学学院': ('生物学国家理科基地，在植物学、动物学、微生物学、遗传学等方向具有深厚学术积累。', 'https://life.scu.edu.cn'),
    '电子信息学院': ('信息与通信工程国家一级重点学科培育，涵盖电子科学与技术、信息与通信工程，产教融合特色鲜明。', 'https://ee.scu.edu.cn'),
    '计算机学院': ('计算机科学与技术一级学科博士点，人工智能、大数据、网络空间安全为特色方向，产学研紧密结合。', 'https://cs.scu.edu.cn'),
    '建筑与环境学院': ('建筑学与土木工程双轮驱动，在绿色建筑、BIM技术、环境工程等领域具有鲜明特色。', 'https://ace.scu.edu.cn'),
    '水利水电学院': ('水利工程国家重点学科，在水资源开发利用、水灾害防治、水环境保护等方面具有国际影响力。', 'https://wrh.scu.edu.cn'),
    '电气工程学院': ('电气工程一级学科博士点，在电力系统及其自动化、高电压与绝缘技术等方向具有显著优势。', 'https://ee.scu.edu.cn'),
    '商学院': ('工商管理一级学科博士点，MBA/EMBA教育国内知名，企业管理和会计学为特色方向。', 'https://bs.scu.edu.cn'),
    '华西临床医学院（华西医院）': ('中国西部疑难危急重症诊疗中心，临床医学学科ESI全球前1‰，附属医院综合实力全国领先。', 'https://wcsh.scu.edu.cn'),
    '华西口腔医学院': ('口腔医学学科全国第一，拥有口腔医学国家重点实验室和口腔疾病研究国家临床医学研究中心。', 'https://hxkq.scu.edu.cn'),
    '华西药学院': ('药学一级学科博士点，在药物化学、药剂学、药理学、临床药学等方向具有深厚研究基础。', 'https://pharmacy.scu.edu.cn'),
    '华西基础医学与法医学院': ('基础医学一级学科博士点，在人体解剖学、病理学、法医学等方向具有鲜明特色。', 'https://jcyx.scu.edu.cn'),
    '华西公共卫生学院': ('公共卫生与预防医学一级学科博士点，流行病学、卫生统计学为国家级特色方向。', 'https://gw.scu.edu.cn'),
    '马克思主义学院': ('全国重点马克思主义学院，马克思主义理论一级学科博士点，在思政教育和理论研究方面发挥引领作用。', 'https://marx.scu.edu.cn'),
    '历史文化学院（旅游学院）': ('历史学国家文科基础学科人才培养基地，考古学、中国史、世界史三个一级学科博士点。', 'https://history.scu.edu.cn'),
    '公共管理学院': ('公共管理一级学科博士点，在行政管理、社会保障、土地资源管理等方向具有较强研究实力。', 'https://spa.scu.edu.cn'),
    '材料科学与工程学院': ('材料科学与工程一级学科博士点，在金属材料、无机非金属材料、高分子材料等方向具有特色。', 'https://mse.scu.edu.cn'),
    '机械工程学院': ('机械工程一级学科博士点，智能制造、机器人技术、增材制造为特色方向。', 'https://me.scu.edu.cn'),
}

# ══════════════════════════════════════════════════════════════════════
# Course data — expanded to 25+ colleges, 3-6 courses each
# ══════════════════════════════════════════════════════════════════════

COURSE_DATA: dict[str, list[tuple[str, str, str, float, str]]] = {
    '计算机学院': [
        ('数据结构与算法', 'shuju-jiegou', '必修', 4.0, '计算机专业核心课程，涵盖线性表、树、图、排序算法等'),
        ('操作系统', 'caozuo-xitong', '必修', 4.0, '进程管理、内存管理、文件系统、I/O等操作系统核心概念'),
        ('计算机网络', 'jisuanji-wangluo', '必修', 3.0, 'TCP/IP协议栈、网络层、传输层、应用层协议'),
        ('数据库系统概论', 'shujuku-xitong', '必修', 3.0, '关系模型、SQL、事务、并发控制、数据库设计'),
        ('编译原理', 'bianyi-yuanli', '必修', 3.0, '词法分析、语法分析、语义分析、代码生成与优化'),
        ('人工智能导论', 'rengong-zhineng', '选修', 3.0, '搜索、推理、机器学习基础、神经网络、自然语言处理'),
    ],
    '数学学院': [
        ('高等数学A（上）', 'gaoshu-a1', '必修', 5.0, '极限、导数、积分、微分方程'),
        ('高等数学A（下）', 'gaoshu-a2', '必修', 5.0, '多元微积分、曲线积分、曲面积分、无穷级数'),
        ('线性代数', 'xianxing-daishu', '必修', 3.0, '矩阵、行列式、向量空间、特征值、二次型'),
        ('概率论与数理统计', 'gailvlun', '必修', 3.0, '随机事件、分布、参数估计、假设检验'),
        ('数学分析', 'shuxue-fenxi', '必修', 5.0, '实数理论、极限论、微积分学、级数理论'),
    ],
    '物理学院': [
        ('大学物理（上）', 'daxue-wuli1', '必修', 4.0, '力学、热学、电磁学基础'),
        ('大学物理（下）', 'daxue-wuli2', '必修', 4.0, '光学、近代物理、量子力学导论'),
        ('量子力学', 'liangzi-lixue', '必修', 4.0, '波函数、薛定谔方程、算符理论、微扰论'),
        ('固体物理', 'guti-wuli', '选修', 3.0, '晶体结构、能带理论、晶格振动、电子输运'),
    ],
    '化学学院': [
        ('有机化学', 'youji-huaxue', '必修', 4.0, '烃类、醇酚醚、醛酮、羧酸及其衍生物'),
        ('无机化学', 'wuji-huaxue', '必修', 4.0, '元素周期律、化学键理论、配位化学、酸碱理论'),
        ('分析化学', 'fenxi-huaxue', '必修', 3.0, '定量分析、仪器分析、色谱与光谱技术'),
        ('物理化学', 'wuli-huaxue', '必修', 4.0, '热力学、动力学、电化学、表面与胶体化学'),
    ],
    '生命科学学院': [
        ('生物化学', 'shengwu-huaxue', '必修', 4.0, '蛋白质、核酸、酶学、代谢途径与调控'),
        ('分子生物学', 'fenzi-shengwuxue', '必修', 3.0, 'DNA复制、转录、翻译、基因表达调控'),
        ('遗传学', 'yichuanxue', '必修', 3.0, '孟德尔遗传、连锁交换、群体遗传、分子遗传'),
        ('细胞生物学', 'xibao-shengwuxue', '必修', 3.0, '细胞结构、信号转导、细胞周期、凋亡与癌变'),
    ],
    '电子信息学院': [
        ('信号与系统', 'xinhao-xitong', '必修', 4.0, '连续与离散信号分析、傅里叶变换、拉普拉斯变换'),
        ('数字电路', 'shuzi-dianlu', '必修', 3.0, '逻辑门、组合电路、时序电路、PLD设计'),
        ('通信原理', 'tongxin-yuanli', '必修', 4.0, '模拟与数字通信、调制解调、信道编码、同步技术'),
        ('电磁场与电磁波', 'diancichang', '必修', 3.0, '静电场、恒定磁场、时变电磁场、平面波传播'),
    ],
    '电气工程学院': [
        ('电路原理', 'dianlu-yuanli', '必修', 4.0, '电路基本定律、网络定理、一阶二阶电路分析'),
        ('电机学', 'dianji-xue', '必修', 3.0, '变压器、直流电机、异步电机、同步电机原理'),
        ('电力系统分析', 'dianli-xitong', '必修', 4.0, '潮流计算、短路分析、稳定分析、电力市场'),
    ],
    '外国语学院': [
        ('大学英语（综合）1', 'daying1', '必修', 2.0, '综合英语听说读写训练，基础级'),
        ('大学英语（综合）2', 'daying2', '必修', 2.0, '综合英语听说读写训练，进阶级'),
        ('大学英语（综合）3', 'daying3', '必修', 2.0, '综合英语听说读写训练，提高级'),
        ('基础日语', 'jichu-riyu', '选修', 3.0, '五十音、基础语法、日常会话、日本文化入门'),
    ],
    '经济学院': [
        ('微观经济学', 'weiguan-jingji', '必修', 3.0, '供求理论、消费者行为、厂商理论、市场结构'),
        ('宏观经济学', 'hongguan-jingji', '必修', 3.0, '国民收入、IS-LM模型、AD-AS模型、经济增长'),
        ('计量经济学', 'jiliang-jingji', '必修', 3.0, '回归分析、假设检验、时间序列、面板数据'),
        ('金融学', 'jinrongxue', '必修', 3.0, '货币银行、金融市场、资产定价、风险管理'),
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
    '建筑与环境学院': [
        ('建筑设计基础', 'jianzhu-sheji', '必修', 4.0, '建筑设计原理与方法、空间构成、建筑表达'),
        ('结构力学', 'jiegou-lixue', '必修', 4.0, '静定结构、超静定结构、矩阵位移法、有限元基础'),
        ('环境工程原理', 'huanjing-gongcheng', '必修', 3.0, '水处理、大气污染控制、固废处理与资源化'),
    ],
    '水利水电学院': [
        ('水力学', 'shuilixue', '必修', 4.0, '水流运动基本规律、管流、明渠流、渗流'),
        ('工程水文学', 'gongcheng-shuiwen', '必修', 3.0, '水文循环、降雨径流、洪水计算、水资源评价'),
        ('水工建筑物', 'shuigong-jianzhuwu', '必修', 4.0, '大坝、溢洪道、水闸、水电站建筑物设计'),
    ],
    '商学院': [
        ('管理学原理', 'guanlixue-yuanli', '必修', 3.0, '管理思想演进、计划、组织、领导、控制'),
        ('会计学基础', 'kuaijixue-jichu', '必修', 3.0, '会计循环、财务报表、成本核算、审计基础'),
        ('市场营销', 'shichang-yingxiao', '选修', 3.0, 'STP战略、4P营销组合、品牌管理、数字营销'),
    ],
    '华西临床医学院（华西医院）': [
        ('人体解剖学', 'renti-jiepou', '必修', 5.0, '系统解剖学与局部解剖学，人体各系统结构与功能'),
        ('病理学', 'binglixue', '必修', 4.0, '疾病基本病理过程、各系统病理变化与临床联系'),
        ('药理学', 'yaolixue', '必修', 4.0, '药物作用机制、药代动力学、临床合理用药'),
        ('诊断学', 'zhenduanxue', '必修', 4.0, '问诊、体格检查、实验室检查、影像学诊断'),
    ],
    '华西口腔医学院': [
        ('口腔解剖生理学', 'kouqiang-jiepou', '必修', 3.0, '牙体解剖、牙列与咬合、口腔颌面部应用解剖'),
        ('口腔内科学', 'kouqiang-neike', '必修', 4.0, '龋病、牙髓病、根尖周病、牙周病的诊疗'),
        ('口腔修复学', 'kouqiang-xiufu', '必修', 3.0, '固定义齿、活动义齿、种植修复的理论与技术'),
    ],
    '华西药学院': [
        ('药物化学', 'yaowu-huaxue', '必修', 4.0, '药物分子设计、构效关系、合成路线与工艺'),
        ('药剂学', 'yaojixue', '必修', 4.0, '药物剂型设计、制剂工艺、生物药剂学'),
        ('药物分析', 'yaowu-fenxi', '必修', 3.0, '药品质量标准、色谱分析、光谱分析、生物样品分析'),
    ],
    '材料科学与工程学院': [
        ('材料科学基础', 'cailiao-kexue-jichu', '必修', 4.0, '晶体结构、相图、扩散、相变、材料力学性能'),
        ('金属材料学', 'jinshu-cailiao', '必修', 3.0, '钢铁材料、有色金属、高温合金、材料失效分析'),
    ],
    '机械工程学院': [
        ('机械设计基础', 'jixie-sheji', '必修', 4.0, '机械原理、机构学、机械零件设计与强度计算'),
        ('机械制造技术基础', 'jixie-zhizao', '必修', 3.0, '切削加工、数控技术、先进制造、精密与超精密加工'),
    ],
}

# ══════════════════════════════════════════════════════════════════════
# Material templates — 55 templates across 8 standard categories
# ══════════════════════════════════════════════════════════════════════

MATERIAL_TEMPLATES: list[dict] = [
    # ── 考试资料 (10) ──
    {'title': '{course} 历年期末考试真题合集', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期中测试题及解答', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末模拟试卷（3套）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 历年期中考试真题', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末考点预测', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 考研真题汇编', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 选择题专项训练（500题）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 名词解释汇总', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 论述题参考答案（完整版）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 计算题详解与技巧', 'category': '考试资料', 'format': 'pdf'},

    # ── 复习提纲 (10) ──
    {'title': '{course} 期末复习提纲（重点版）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 期末重点总结', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 思维导图（全章节）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 知识点背诵手册', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 公式速查手册', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 名词解释汇编', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 学长学姐经验谈', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 易错知识点汇总', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 章节概要速览', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 背诵口诀合集', 'category': '复习提纲', 'format': 'pdf'},

    # ── 课堂笔记 (9) ──
    {'title': '{course} 课堂笔记（完整版）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 学霸手写笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} iPad电子笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 案例分析集', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 随堂笔记（彩色标注版）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 读书笔记与感悟', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 学习心得笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 课堂实录笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 听课重点记录', 'category': '课堂笔记', 'format': 'pdf'},

    # ── 教材 (6) ──
    {'title': '{course} 教材电子版', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 经典参考书PDF', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 推荐教材合集', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 指定教材高清扫描版', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 原版教材影印本', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 辅助教材汇编', 'category': '教材', 'format': 'pdf'},

    # ── 习题集 (8) ──
    {'title': '{course} 课后习题答案', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 经典例题精讲', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 章节练习题集', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 配套习题解答（全）', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 易错题专项训练', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 小题狂练1000题', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 编程作业参考代码', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 综合练习题与答案', 'category': '习题集', 'format': 'pdf'},

    # ── 实验报告 (6) ──
    {'title': '{course} 实验报告模板', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 课程设计报告参考', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 实验操作指南', 'category': '实验报告', 'format': 'pdf'},
    {'title': '{course} 专题研究报告', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 上机实验指导书', 'category': '实验报告', 'format': 'pdf'},
    {'title': '{course} 实验数据处理与分析', 'category': '实验报告', 'format': 'xlsx'},

    # ── 历年真题 (3) ──
    {'title': '{course} 近十年考研真题汇编', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 历年期末真题回忆版', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 考研真题解析与技巧', 'category': '历年真题', 'format': 'pdf'},

    # ── 课件讲义 (3) ──
    {'title': '{course} PPT课件合集', 'category': '课件讲义', 'format': 'pptx'},
    {'title': '{course} 教学视频配套讲义', 'category': '课件讲义', 'format': 'pdf'},
    {'title': '{course} 教学大纲与进度表', 'category': '课件讲义', 'format': 'pdf'},
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
    {'phone': '13908000009', 'nickname': '医学生小华', 'role': 'student', 'trust_score': 93, 'display_name': '华西医学生'},
    {'phone': '13908000010', 'nickname': '建筑狮', 'role': 'student', 'trust_score': 84, 'display_name': '建筑系学长'},
    {'phone': '13908000011', 'nickname': '化学院小王', 'role': 'student', 'trust_score': 91, 'display_name': '化学实验员'},
    {'phone': '13908000012', 'nickname': '经济学人', 'role': 'student', 'trust_score': 88, 'display_name': '经院学子'},
]

MAINTAINER_PHONE = '13908000000'


MOCK_PASSWORD_HASH = bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode()


def _build_parts(tpl: dict, course_name: str) -> list[dict] | None:
    """Generate multi-file parts for a material based on its category and format."""
    category = tpl['category']
    fmt = tpl['format']

    # PPT slides are typically multi-file archives
    if category == '课件讲义' and fmt == 'pptx':
        return [
            {'filename': f'{course_name}_第1-4章.pptx', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_ch1-4.pptx', 'file_size': random.randint(2_000_000, 15_000_000), 'format': 'pptx'},
            {'filename': f'{course_name}_第5-8章.pptx', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_ch5-8.pptx', 'file_size': random.randint(2_000_000, 15_000_000), 'format': 'pptx'},
            {'filename': f'{course_name}_第9-12章.pptx', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_ch9-12.pptx', 'file_size': random.randint(1_000_000, 10_000_000), 'format': 'pptx'},
        ]

    # Lab reports often have data + report + code
    if category == '实验报告' and fmt in ('docx', 'pdf'):
        parts = [
            {'filename': f'{course_name}_实验报告.docx', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_report.docx', 'file_size': random.randint(500_000, 5_000_000), 'format': 'docx'},
            {'filename': f'{course_name}_实验数据.xlsx', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_data.xlsx', 'file_size': random.randint(50_000, 500_000), 'format': 'xlsx'},
        ]
        if random.random() > 0.5:
            parts.append({'filename': f'{course_name}_代码.zip', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_code.zip', 'file_size': random.randint(100_000, 2_000_000), 'format': 'zip'})
        return parts

    # Programming assignments often have code + report
    if category == '习题集' and '代码' in tpl.get('title', ''):
        return [
            {'filename': f'{course_name}_源码.zip', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_src.zip', 'file_size': random.randint(100_000, 5_000_000), 'format': 'zip'},
            {'filename': f'{course_name}_说明文档.pdf', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_readme.pdf', 'file_size': random.randint(50_000, 1_000_000), 'format': 'pdf'},
        ]

    # Textbooks might have split volumes
    if category == '教材':
        return [
            {'filename': f'{course_name}_上册.pdf', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_vol1.pdf', 'file_size': random.randint(20_000_000, 80_000_000), 'format': 'pdf'},
            {'filename': f'{course_name}_下册.pdf', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_vol2.pdf', 'file_size': random.randint(15_000_000, 60_000_000), 'format': 'pdf'},
        ]

    # Random parts for variety (30% chance)
    if random.random() < 0.3:
        return [
            {'filename': f'{course_name}_主文件.{fmt}', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_main.{fmt}', 'file_size': random.randint(500_000, 20_000_000), 'format': fmt},
            {'filename': f'{course_name}_附录.{fmt}', 'storage_key': f'mock/storage/{random.randint(10000,99999)}_appendix.{fmt}', 'file_size': random.randint(50_000, 2_000_000), 'format': fmt},
        ]

    return None


async def _ensure_badge(db, user_id, badge_type) -> int:
    """Create badge if it doesn't exist. Returns 1 if created, 0 if already existed."""
    from app.schemas.badge import BADGE_META
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_type == badge_type)
    )
    if result.scalar_one_or_none():
        return 0
    db.add(UserBadge(user_id=user_id, badge_type=badge_type))
    # Also create notification
    from app.models.notification import Notification
    meta = BADGE_META.get(badge_type, {})
    db.add(Notification(
        user_id=user_id,
        type='badge_awarded',
        title=f'恭喜获得【{meta.get("label", badge_type)}】徽章！',
        body=meta.get('description', ''),
        resource_type='badge',
        resource_id=badge_type,
    ))
    return 1


async def seed():
    async with async_session() as db:
        # ── 1. Get existing colleges & update metadata ──
        result = await db.execute(select(College))
        colleges = {c.name: c for c in result.scalars().all()}
        if not colleges:
            print('No colleges found. Run seed_colleges.py first.')
            return

        updated_colleges = 0
        for name, (desc, website) in COLLEGE_META.items():
            college = colleges.get(name)
            if college and (not college.description or not college.website):
                if not college.description:
                    college.description = desc
                if not college.website:
                    college.website = website
                updated_colleges += 1
        if updated_colleges:
            await db.flush()
            print(f'Updated metadata for {updated_colleges} colleges')

        # ── 2. Create mock users ──
        mock_users: dict[str, User] = {}
        for mu in MOCK_USERS:
            encrypted_phone = encrypt_pii(mu['phone'])
            # Try encrypted lookup first, then fallback to plaintext (legacy data)
            result = await db.execute(select(User).where(User.phone == encrypted_phone))
            user = result.scalar()
            if not user:
                result = await db.execute(select(User).where(User.phone == mu['phone']))
                user = result.scalar()
            if not user:
                user = User(
                    phone=encrypted_phone,
                    nickname=mu['nickname'],
                    role=mu['role'],
                    trust_score=mu['trust_score'],
                    public_display_name=mu['display_name'],
                    password_hash=MOCK_PASSWORD_HASH,
                )
                db.add(user)
                await db.flush()
            else:
                # Migrate legacy plain-text phone to encrypted
                if user.phone == mu['phone']:
                    user.phone = encrypted_phone
                if not user.password_hash:
                    user.password_hash = MOCK_PASSWORD_HASH
            mock_users[mu['phone']] = user

        encrypted_maintainer = encrypt_pii(MAINTAINER_PHONE)
        result = await db.execute(select(User).where(User.phone == encrypted_maintainer))
        maintainer = result.scalar()
        if not maintainer:
            result = await db.execute(select(User).where(User.phone == MAINTAINER_PHONE))
            maintainer = result.scalar()
        if not maintainer:
            maintainer = User(
                phone=encrypted_maintainer,
                nickname='管理员',
                role='maintainer',
                trust_score=100,
                public_display_name='川流课栈管理员',
                password_hash=MOCK_PASSWORD_HASH,
            )
            db.add(maintainer)
            await db.flush()
        else:
            if maintainer.phone == MAINTAINER_PHONE:
                maintainer.phone = encrypted_maintainer
            if not maintainer.password_hash:
                maintainer.password_hash = MOCK_PASSWORD_HASH

        print(f'Created/verified {len(mock_users)} mock users + 1 maintainer (password: 123456)')

        # ── 3. Create courses ──
        existing_courses = set((await db.execute(select(Course.name))).scalars().all())
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
                existing_courses.add(name)
        await db.flush()
        print(f'Created {len(new_courses)} courses')

        # ── 4. Create materials ──
        all_courses = (await db.execute(select(Course))).scalars().all()
        existing_titles = set(
            (await db.execute(select(Material.title))).scalars().all()
        )
        new_materials: list[Material] = []
        user_list = list(mock_users.values())
        total_parts_materials = 0

        for course in all_courses:
            n_templates = min(random.randint(12, 20), len(MATERIAL_TEMPLATES))
            templates = random.sample(MATERIAL_TEMPLATES, n_templates)
            for tpl in templates:
                title = tpl['title'].format(course=course.name[:15])
                if title in existing_titles:
                    continue
                days_ago = random.randint(1, 365)
                dl = random.randint(0, 800)
                rc = random.randint(0, dl + random.randint(0, 80))
                contributor = random.choice(user_list)
                parts = _build_parts(tpl, course.name[:15])

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
                    parts=parts,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                    updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_ago)),
                )
                db.add(m)
                new_materials.append(m)
                existing_titles.add(title)
                if parts:
                    total_parts_materials += 1

        await db.flush()
        print(f'Created {len(new_materials)} materials ({total_parts_materials} with multi-file parts)')

        # ── 5. Seed badges for mock users ──
        badge_count = 0
        for user in user_list:
            user_materials = [m for m in new_materials if m.contributor_id == user.id]
            if not user_materials:
                continue

            # First upload badge
            badge_count += await _ensure_badge(db, user.id, 'first_upload')

            # Prolific badges
            if len(user_materials) >= 10:
                badge_count += await _ensure_badge(db, user.id, 'prolific_10')
            if len(user_materials) >= 50:
                badge_count += await _ensure_badge(db, user.id, 'prolific_50')

            # Popular badges based on top download
            top_dl = max((m.download_count or 0) for m in user_materials)
            if top_dl >= 100:
                badge_count += await _ensure_badge(db, user.id, 'popular_100')

            # Give a few random badges for visual variety
            if random.random() < 0.3:
                badge_count += await _ensure_badge(db, user.id, 'selfless')
            if random.random() < 0.15:
                badge_count += await _ensure_badge(db, user.id, 'continuous_3')

        print(f'Created {badge_count} user badges')

        # ── 6. Create academic calendar ──
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
        bc = (await db.execute(select(func.count()).select_from(UserBadge))).scalar()
        colleges_with_data = len({c.college_id for c in all_courses})
        print(f'Done. DB now has: {len(colleges)} colleges ({colleges_with_data} with courses), {cc} courses, {mc} approved materials, {uc} users, {bc} badges, {evc} calendar events')


if __name__ == '__main__':
    asyncio.run(seed())
