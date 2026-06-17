"""Seed mock data: users, courses, materials, ratings, collections, comments, bookmarks, wishes, badges, calendar.
Makes the database feel like a real, active platform with 3-4x the previous data volume.
Usage: python -m scripts.seed_mock_data
"""
import asyncio
import random
from datetime import date, datetime, timedelta, timezone

import bcrypt
from sqlalchemy import func, select, text as sa_text

from app.core.database import async_session
from app.core.security import encrypt_pii
from app.models.user import User
from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.models.calendar import AcademicCalendar
from app.models.user_badge import UserBadge
from app.models.notification import Notification
from app.models.collection import Collection, CollectionItem
from app.models.comment import Comment
from app.models.bookmark import Bookmark

MAINTAINER_PHONE = '13908000000'
MOCK_PASSWORD_HASH = bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode()

# ════════════════════════════════════════════════════════════════════════════
# 1. College metadata
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# 2. Users — expanded to 40 with college affiliations and realistic names
# ════════════════════════════════════════════════════════════════════════════

MOCK_USERS = [
    # ── Original 12 ──
    {'phone': '13908000001', 'nickname': '川大课小栈', 'role': 'student', 'trust_score': 95, 'display_name': '课栈小助手', 'college': '计算机学院'},
    {'phone': '13908000002', 'nickname': '学霸小明', 'role': 'student', 'trust_score': 88, 'display_name': '小明同学', 'college': '数学学院'},
    {'phone': '13908000003', 'nickname': '考研达人', 'role': 'student', 'trust_score': 92, 'display_name': '考研学长', 'college': '电子信息学院'},
    {'phone': '13908000004', 'nickname': '笔记侠', 'role': 'student', 'trust_score': 85, 'display_name': '笔记达人', 'college': '文学与新闻学院'},
    {'phone': '13908000005', 'nickname': '实验小能手', 'role': 'student', 'trust_score': 90, 'display_name': '实验达人', 'college': '化学学院'},
    {'phone': '13908000006', 'nickname': '编程高手', 'role': 'student', 'trust_score': 87, 'display_name': '代码小哥', 'college': '计算机学院'},
    {'phone': '13908000007', 'nickname': '英语达人', 'role': 'student', 'trust_score': 86, 'display_name': '英语学霸', 'college': '外国语学院'},
    {'phone': '13908000008', 'nickname': '复习小王子', 'role': 'student', 'trust_score': 89, 'display_name': '复习助手', 'college': '生命科学学院'},
    {'phone': '13908000009', 'nickname': '医学生小华', 'role': 'student', 'trust_score': 93, 'display_name': '华西医学生', 'college': '华西临床医学院（华西医院）'},
    {'phone': '13908000010', 'nickname': '建筑狮', 'role': 'student', 'trust_score': 84, 'display_name': '建筑系学长', 'college': '建筑与环境学院'},
    {'phone': '13908000011', 'nickname': '化学院小王', 'role': 'student', 'trust_score': 91, 'display_name': '化学实验员', 'college': '化学学院'},
    {'phone': '13908000012', 'nickname': '经济学人', 'role': 'student', 'trust_score': 88, 'display_name': '经院学子', 'college': '经济学院'},
    # ── New 28 ──
    {'phone': '13908000013', 'nickname': '法学小张', 'role': 'student', 'trust_score': 82, 'display_name': '法学生小张', 'college': '法学院'},
    {'phone': '13908000014', 'nickname': '物理爱好者', 'role': 'student', 'trust_score': 90, 'display_name': '物理系同学', 'college': '物理学院'},
    {'phone': '13908000015', 'nickname': '口腔医学生', 'role': 'student', 'trust_score': 94, 'display_name': '华西口腔学长', 'college': '华西口腔医学院'},
    {'phone': '13908000016', 'nickname': '药学小助手', 'role': 'student', 'trust_score': 87, 'display_name': '药院同学', 'college': '华西药学院'},
    {'phone': '13908000017', 'nickname': '电气工程师', 'role': 'student', 'trust_score': 83, 'display_name': '电气学长', 'college': '电气工程学院'},
    {'phone': '13908000018', 'nickname': '公管学子', 'role': 'student', 'trust_score': 80, 'display_name': '公管人', 'college': '公共管理学院'},
    {'phone': '13908000019', 'nickname': '历史爱好者', 'role': 'student', 'trust_score': 85, 'display_name': '文旅同学', 'college': '历史文化学院（旅游学院）'},
    {'phone': '13908000020', 'nickname': '机械攻城狮', 'role': 'student', 'trust_score': 81, 'display_name': '机械系', 'college': '机械工程学院'},
    {'phone': '13908000021', 'nickname': '材料小王子', 'role': 'student', 'trust_score': 86, 'display_name': '材院同学', 'college': '材料科学与工程学院'},
    {'phone': '13908000022', 'nickname': '商科精英', 'role': 'student', 'trust_score': 84, 'display_name': '商学院学子', 'college': '商学院'},
    {'phone': '13908000023', 'nickname': '水利水电人', 'role': 'student', 'trust_score': 82, 'display_name': '水利系', 'college': '水利水电学院'},
    {'phone': '13908000024', 'nickname': '马克思信徒', 'role': 'student', 'trust_score': 91, 'display_name': '马院同学', 'college': '马克思主义学院'},
    {'phone': '13908000025', 'nickname': '公卫先锋', 'role': 'student', 'trust_score': 88, 'display_name': '公卫人', 'college': '华西公共卫生学院'},
    {'phone': '13908000026', 'nickname': '基法学院人', 'role': 'student', 'trust_score': 87, 'display_name': '基法同学', 'college': '华西基础医学与法医学院'},
    {'phone': '13908000027', 'nickname': '艺术细胞', 'role': 'student', 'trust_score': 79, 'display_name': '艺术学院', 'college': '艺术学院'},
    {'phone': '13908000028', 'nickname': 'CS大牛', 'role': 'contributor', 'trust_score': 96, 'display_name': '计院大佬', 'college': '计算机学院'},
    {'phone': '13908000029', 'nickname': '数学天才', 'role': 'contributor', 'trust_score': 97, 'display_name': '数院学霸', 'college': '数学学院'},
    {'phone': '13908000030', 'nickname': '临五学霸', 'role': 'contributor', 'trust_score': 95, 'display_name': '临床五年', 'college': '华西临床医学院（华西医院）'},
    {'phone': '13908000031', 'nickname': '算法爱好者', 'role': 'student', 'trust_score': 89, 'display_name': '算法小哥', 'college': '计算机学院'},
    {'phone': '13908000032', 'nickname': '金融小王子', 'role': 'student', 'trust_score': 86, 'display_name': '金融系', 'college': '经济学院'},
    {'phone': '13908000033', 'nickname': '新闻学子', 'role': 'student', 'trust_score': 83, 'display_name': '新传人', 'college': '文学与新闻学院'},
    {'phone': '13908000034', 'nickname': '生科达人', 'role': 'student', 'trust_score': 88, 'display_name': '生科院', 'college': '生命科学学院'},
    {'phone': '13908000035', 'nickname': '大数据玩家', 'role': 'student', 'trust_score': 90, 'display_name': '数据科学', 'college': '计算机学院'},
    {'phone': '13908000036', 'nickname': '日语小能手', 'role': 'student', 'trust_score': 84, 'display_name': '日语同学', 'college': '外国语学院'},
    {'phone': '13908000037', 'nickname': '环境卫士', 'role': 'student', 'trust_score': 82, 'display_name': '环工同学', 'college': '建筑与环境学院'},
    {'phone': '13908000038', 'nickname': '病理学达人', 'role': 'student', 'trust_score': 91, 'display_name': '病理同学', 'college': '华西临床医学院（华西医院）'},
    {'phone': '13908000039', 'nickname': '考研政治王', 'role': 'student', 'trust_score': 93, 'display_name': '政治高分', 'college': '马克思主义学院'},
    {'phone': '13908000040', 'nickname': '数据库专家', 'role': 'contributor', 'trust_score': 94, 'display_name': 'DBA大佬', 'college': '计算机学院'},
]

# ════════════════════════════════════════════════════════════════════════════
# 3. Courses — expanded to 5-8 per college, ~140 total
# ════════════════════════════════════════════════════════════════════════════

COURSE_DATA: dict[str, list[tuple[str, str, str, float, str]]] = {
    '计算机学院': [
        ('数据结构与算法', 'shuju-jiegou', '必修', 4.0, '线性表、树、图、排序算法、查找算法、算法复杂度分析'),
        ('操作系统', 'caozuo-xitong', '必修', 4.0, '进程管理、内存管理、文件系统、I/O系统、死锁与并发'),
        ('计算机网络', 'jisuanji-wangluo', '必修', 3.5, 'TCP/IP协议栈、应用层、传输层、网络层、链路层、网络安全'),
        ('数据库系统概论', 'shujuku-xitong', '必修', 3.0, '关系模型、SQL、事务管理、并发控制、数据库设计与优化'),
        ('编译原理', 'bianyi-yuanli', '必修', 3.0, '词法分析、语法分析、语义分析、中间代码生成、代码优化'),
        ('人工智能导论', 'rengong-zhineng', '选修', 3.0, '搜索策略、知识表示、机器学习基础、神经网络、NLP入门'),
        ('软件工程导论', 'ruanjian-gongcheng', '必修', 2.5, '软件生命周期、需求分析、系统设计、测试、项目管理'),
        ('离散数学', 'lisan-shuxue', '必修', 3.0, '命题逻辑、集合论、图论、代数系统、组合数学'),
    ],
    '数学学院': [
        ('高等数学A（上）', 'gaoshu-a1', '必修', 5.0, '极限与连续、导数与微分、不定积分、定积分、微分方程'),
        ('高等数学A（下）', 'gaoshu-a2', '必修', 5.0, '多元函数微积分、曲线积分、曲面积分、无穷级数'),
        ('线性代数', 'xianxing-daishu', '必修', 3.0, '矩阵与行列式、向量空间、线性变换、特征值、二次型'),
        ('概率论与数理统计', 'gailvlun', '必修', 3.0, '随机事件与概率、随机变量、参数估计、假设检验、回归分析'),
        ('数学分析', 'shuxue-fenxi', '必修', 5.0, '实数理论、极限论、连续函数、微积分学、级数理论'),
        ('数值计算方法', 'shuzhi-jisuan', '选修', 2.5, '插值与逼近、数值积分、线性方程组求解、常微分方程数值解'),
    ],
    '物理学院': [
        ('大学物理（上）', 'daxue-wuli1', '必修', 4.0, '质点力学、刚体力学、热力学基础、静电场、稳恒磁场'),
        ('大学物理（下）', 'daxue-wuli2', '必修', 4.0, '电磁感应、光学、狭义相对论、量子物理基础'),
        ('量子力学', 'liangzi-lixue', '必修', 4.0, '波函数与薛定谔方程、算符理论、微扰论、自旋与全同粒子'),
        ('固体物理', 'guti-wuli', '选修', 3.0, '晶体结构、晶格振动、能带理论、电子输运、半导体物理'),
        ('电动力学', 'diandong-lixue', '必修', 3.5, '静电场边值问题、电磁波传播与辐射、狭义相对论电动力学'),
    ],
    '化学学院': [
        ('有机化学', 'youji-huaxue', '必修', 4.0, '烃类、醇酚醚、醛酮醌、羧酸衍生物、含氮化合物、杂环'),
        ('无机化学', 'wuji-huaxue', '必修', 4.0, '元素周期律、化学键理论、配位化合物、酸碱理论、氧化还原'),
        ('分析化学', 'fenxi-huaxue', '必修', 3.0, '定量分析误差、滴定分析、色谱技术、光谱分析、电化学分析'),
        ('物理化学', 'wuli-huaxue', '必修', 4.0, '化学热力学、化学动力学、电化学、表面化学、胶体化学'),
        ('高分子化学', 'gaofenzi-huaxue', '选修', 2.5, '自由基聚合、离子聚合、缩聚反应、高分子结构与性能'),
    ],
    '生命科学学院': [
        ('生物化学', 'shengwu-huaxue', '必修', 4.0, '蛋白质结构与功能、酶学、核酸化学、代谢途径与调控'),
        ('分子生物学', 'fenzi-shengwuxue', '必修', 3.0, 'DNA复制、转录、翻译、基因表达调控、基因组编辑'),
        ('遗传学', 'yichuanxue', '必修', 3.0, '孟德尔遗传、连锁交换、群体遗传学、分子遗传学'),
        ('细胞生物学', 'xibao-shengwuxue', '必修', 3.0, '细胞膜与物质运输、信号转导、细胞周期、凋亡与癌变'),
        ('微生物学', 'weishengwu-xue', '必修', 3.0, '微生物分类、代谢多样性、遗传变异、免疫学基础'),
    ],
    '电子信息学院': [
        ('信号与系统', 'xinhao-xitong', '必修', 4.0, '连续与离散信号分析、傅里叶变换、拉普拉斯变换、Z变换'),
        ('数字电路', 'shuzi-dianlu', '必修', 3.0, '逻辑代数、组合逻辑电路、时序逻辑电路、PLD与FPGA设计'),
        ('通信原理', 'tongxin-yuanli', '必修', 4.0, '模拟调制、数字调制、信道编码、同步技术、多址技术'),
        ('电磁场与电磁波', 'diancichang', '必修', 3.0, '静电场、恒定磁场、时变电磁场、平面电磁波、传输线'),
        ('嵌入式系统', 'qianrushi-xitong', '选修', 3.0, 'ARM架构、RTOS、外设驱动、嵌入式Linux、物联网应用'),
    ],
    '电气工程学院': [
        ('电路原理', 'dianlu-yuanli', '必修', 4.0, '电路基本定律、网络定理、一阶/二阶电路、正弦稳态分析'),
        ('电机学', 'dianji-xue', '必修', 3.0, '变压器、直流电机、异步电机、同步电机、特种电机'),
        ('电力系统分析', 'dianli-xitong', '必修', 4.0, '潮流计算、短路分析、电力系统稳定、继电保护基础'),
        ('高电压技术', 'gaodianya-jishu', '选修', 2.5, '气体放电、液体/固体绝缘、过电压防护、绝缘配合'),
    ],
    '外国语学院': [
        ('大学英语（综合）1', 'daying1', '必修', 2.0, '综合英语听说读写训练，基础级，涵盖日常会话与基础写作'),
        ('大学英语（综合）2', 'daying2', '必修', 2.0, '综合英语听说读写训练，进阶级，学术英语初步'),
        ('大学英语（综合）3', 'daying3', '必修', 2.0, '综合英语听说读写训练，提高级，学术论文阅读与写作'),
        ('基础日语', 'jichu-riyu', '选修', 3.0, '五十音图、基础语法、日常会话、日本文化入门'),
        ('英语口语', 'yingyu-kouyu', '选修', 2.0, '情景对话、即兴演讲、辩论技巧、英语角实战'),
    ],
    '经济学院': [
        ('微观经济学', 'weiguan-jingji', '必修', 3.0, '供求理论、消费者行为、厂商理论、市场结构与博弈论'),
        ('宏观经济学', 'hongguan-jingji', '必修', 3.0, '国民收入核算、IS-LM模型、AD-AS模型、经济增长与波动'),
        ('计量经济学', 'jiliang-jingji', '必修', 3.0, '一元/多元回归、异方差、自相关、时间序列分析、面板数据'),
        ('金融学', 'jinrongxue', '必修', 3.0, '货币与信用、金融市场、资产定价、风险管理、金融监管'),
        ('国际经济学', 'guoji-jingji', '选修', 2.5, '比较优势、关税与非关税壁垒、汇率决定、国际收支调整'),
    ],
    '法学院': [
        ('宪法学', 'xianfa-xue', '必修', 3.0, '宪法基本理论、国家制度与机构、公民基本权利与义务'),
        ('民法学', 'minfa-xue', '必修', 4.0, '民法总则、物权法、合同法、侵权责任法、婚姻家庭法'),
        ('刑法学', 'xingfa-xue', '必修', 4.0, '犯罪论、刑罚论、刑法分则重点罪名、案例分析'),
        ('行政法与行政诉讼法', 'xingzhengfa', '必修', 3.0, '行政行为、行政许可、行政处罚、行政诉讼程序'),
        ('法理学', 'falixue', '必修', 2.5, '法的概念与本质、法律渊源、法律解释与推理、法治理论'),
    ],
    '文学与新闻学院': [
        ('中国古代文学', 'gudai-wenxue', '必修', 3.0, '先秦至近代文学发展脉络、经典作家与作品赏析'),
        ('现代汉语', 'xiandai-hanyu', '必修', 2.0, '语音系统、词汇构成、语法规则、修辞手法'),
        ('新闻学概论', 'xinwenxue-gailun', '必修', 3.0, '新闻传播原理、媒介伦理与法规、新闻采访与写作基础'),
        ('传播学概论', 'chuanboxue-gailun', '必修', 2.5, '传播模式与效果理论、受众分析、新媒体传播特征'),
    ],
    '建筑与环境学院': [
        ('建筑设计基础', 'jianzhu-sheji', '必修', 4.0, '建筑设计原理、空间构成、建筑表达技法、小型建筑方案'),
        ('结构力学', 'jiegou-lixue', '必修', 4.0, '静定结构分析、超静定结构、矩阵位移法、有限元法基础'),
        ('环境工程原理', 'huanjing-gongcheng', '必修', 3.0, '水污染控制、大气污染控制、固体废物处理与资源化'),
        ('工程制图', 'gongcheng-zhitu', '必修', 2.5, '投影理论、三视图、剖面图、AutoCAD基础、BIM入门'),
    ],
    '水利水电学院': [
        ('水力学', 'shuilixue', '必修', 4.0, '水流运动基本规律、管流与明渠流、渗流、水工模型试验'),
        ('工程水文学', 'gongcheng-shuiwen', '必修', 3.0, '水文循环、降雨径流关系、设计洪水计算、水资源评价'),
        ('水工建筑物', 'shuigong-jianzhuwu', '必修', 4.0, '混凝土坝、土石坝、溢洪道、水闸、水电站建筑物'),
        ('水电站', 'shuidianzhan', '选修', 3.0, '水轮机选型、水力机组调节、水电站厂房布置设计'),
    ],
    '商学院': [
        ('管理学原理', 'guanlixue-yuanli', '必修', 3.0, '管理思想演进、计划与决策、组织设计、领导与激励、控制'),
        ('会计学基础', 'kuaijixue-jichu', '必修', 3.0, '会计循环、复式记账、财务报表编制、成本核算基础'),
        ('市场营销', 'shichang-yingxiao', '选修', 3.0, 'STP战略、4P营销组合、品牌管理、数字营销与消费者行为'),
        ('人力资源管理', 'renli-ziyuan', '必修', 2.5, '人力资源规划、招聘与甄选、培训开发、绩效与薪酬管理'),
    ],
    '华西临床医学院（华西医院）': [
        ('人体解剖学', 'renti-jiepou', '必修', 5.0, '系统解剖学与局部解剖学，人体各系统器官形态结构'),
        ('病理学', 'binglixue', '必修', 4.0, '细胞组织损伤、炎症、肿瘤、心血管/呼吸/消化系统病理'),
        ('药理学', 'yaolixue', '必修', 4.0, '药物作用机制、药代动力学、传出/中枢/心血管系统药物'),
        ('诊断学', 'zhenduanxue', '必修', 4.0, '问诊技巧、体格检查、心电图判读、影像学诊断基础'),
        ('内科学', 'neikexue', '必修', 5.0, '呼吸/循环/消化/泌尿/血液系统疾病诊疗原则'),
        ('外科学', 'waikexue', '必修', 5.0, '无菌术、水电解质平衡、外科感染、创伤与烧伤、各系统外科'),
    ],
    '华西口腔医学院': [
        ('口腔解剖生理学', 'kouqiang-jiepou', '必修', 3.0, '牙体解剖形态、牙列与咬合、口腔颌面部系统解剖'),
        ('口腔内科学', 'kouqiang-neike', '必修', 4.0, '龋病学、牙髓病学、根尖周病学、牙周病学'),
        ('口腔修复学', 'kouqiang-xiufu', '必修', 3.0, '固定义齿、可摘局部义齿、全口义齿、种植修复'),
        ('口腔颌面外科学', 'kouqiang-waike', '必修', 3.5, '牙槽外科、颌面部感染与创伤、口腔颌面部肿瘤'),
    ],
    '华西药学院': [
        ('药物化学', 'yaowu-huaxue', '必修', 4.0, '药物分子设计原理、构效关系、合成路线设计、先导化合物优化'),
        ('药剂学', 'yaojixue', '必修', 4.0, '药物剂型设计理论、制剂工艺、生物药剂学与药动学'),
        ('药物分析', 'yaowu-fenxi', '必修', 3.0, '药品质量标准、色谱分析、光谱分析、生物样品前处理'),
        ('临床药学', 'linchuang-yaoxue', '选修', 2.5, '治疗药物监测、药物相互作用、个体化给药方案设计'),
    ],
    '材料科学与工程学院': [
        ('材料科学基础', 'cailiao-kexue-jichu', '必修', 4.0, '晶体学基础、相图与相变、扩散、材料的力学与物理性能'),
        ('金属材料学', 'jinshu-cailiao', '必修', 3.0, '钢铁材料、有色金属与合金、高温合金、材料失效分析'),
        ('高分子材料', 'gaofenzi-cailiao', '选修', 2.5, '高分子合成、结构与性能关系、功能高分子、复合材料'),
    ],
    '机械工程学院': [
        ('机械设计基础', 'jixie-sheji', '必修', 4.0, '机械原理与机构学、机械零件设计、强度计算与校核'),
        ('机械制造技术基础', 'jixie-zhizao', '必修', 3.0, '切削原理、机床与刀具、数控加工、先进制造技术'),
        ('工程力学', 'gongcheng-lixue', '必修', 3.5, '静力学、材料力学、运动学与动力学基础'),
    ],
    '马克思主义学院': [
        ('马克思主义基本原理', 'makesi-jiben-yuanli', '必修', 3.0, '马克思主义哲学、政治经济学、科学社会主义基本理论'),
        ('毛泽东思想和中国特色社会主义理论体系概论', 'maozhonggai', '必修', 3.0, '马克思主义中国化历史进程与理论成果'),
        ('思想道德与法治', 'sixiang-daode', '必修', 2.0, '人生观、价值观、道德观、法治素养教育'),
    ],
    '历史文化学院（旅游学院）': [
        ('中国古代史', 'zhongguo-gudaishi', '必修', 3.0, '先秦至明清历史脉络、重大事件与制度变迁'),
        ('世界近现代史', 'shijie-jindaishi', '必修', 3.0, '文艺复兴至当代的世界历史进程与国际关系演变'),
        ('考古学概论', 'kaoguxue-gailun', '选修', 2.5, '考古学理论与方法、田野考古、科技考古、文化遗产保护'),
    ],
    '公共管理学院': [
        ('行政管理学', 'xingzheng-guanlixue', '必修', 3.0, '行政组织理论、公共政策分析、政府绩效管理、电子政务'),
        ('社会保障概论', 'shehui-baozhang', '必修', 2.5, '社会保险、社会救助、社会福利制度比较与改革'),
    ],
    '华西基础医学与法医学院': [
        ('病理生理学', 'bingli-shenglixue', '必修', 3.5, '疾病发生发展机制、水电解质紊乱、酸碱平衡、休克与DIC'),
        ('法医学', 'fayixue', '必修', 3.0, '死亡与尸体现象、机械性损伤、中毒、DNA鉴定'),
    ],
    '华西公共卫生学院': [
        ('流行病学', 'liuxingbingxue', '必修', 3.5, '疾病分布、病因推断、流行病学研究方法、筛检与监测'),
        ('卫生统计学', 'weisheng-tongjixue', '必修', 3.0, '统计描述与推断、方差分析、回归分析、生存分析'),
    ],
    '艺术学院': [
        ('设计基础', 'sheji-jichu', '必修', 3.0, '平面构成、色彩构成、立体构成、设计美学入门'),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# 4. Material templates — expanded from 55 to 85
# ════════════════════════════════════════════════════════════════════════════

MATERIAL_TEMPLATES: list[dict] = [
    # ── 考试资料 (14) ──
    {'title': '{course} 历年期末考试真题合集', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期中测试题及详细解答', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末模拟试卷（3套含答案）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 历年期中考试真题汇编', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末考点预测与重点标注', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 考研真题汇编（近5年）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 选择题专项训练（500题带解析）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 名词解释汇总（完整版）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 论述题参考答案（高分版）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 计算题详解与解题技巧', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 期末考试A卷（含评分标准）', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 补考试卷及参考答案', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 考研复试笔试真题回忆', 'category': '考试资料', 'format': 'pdf'},
    {'title': '{course} 章节综合测试题（全册）', 'category': '考试资料', 'format': 'pdf'},

    # ── 复习提纲 (14) ──
    {'title': '{course} 期末复习提纲（重点标注版）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 期末重点知识总结', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 全章节思维导图', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 知识点背诵手册（口袋版）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 公式速查手册（考试必备）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 名词解释速记汇编', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 学长学姐备考经验谈', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 高频易错知识点汇总', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 章节概要速览（一页纸）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 记忆口诀合集', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 考前冲刺必背清单', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 历年考点频率分布统计', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 知识框架图（A3打印版）', 'category': '复习提纲', 'format': 'pdf'},
    {'title': '{course} 难点专题突破', 'category': '复习提纲', 'format': 'pdf'},

    # ── 课堂笔记 (12) ──
    {'title': '{course} 课堂笔记（完整版含图示）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 学霸手写笔记（扫描版）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} iPad电子笔记（彩色标注）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 案例分析集锦', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 随堂笔记（图文并茂）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 读书笔记与文献综述', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 学期学习心得笔记', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 课堂逐字实录（整理版）', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 章节重点听课记录', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 教授答疑记录整理', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 小组讨论纪要', 'category': '课堂笔记', 'format': 'pdf'},
    {'title': '{course} 期末串讲笔记', 'category': '课堂笔记', 'format': 'pdf'},

    # ── 教材 (8) ──
    {'title': '{course} 指定教材电子版', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 经典参考书PDF（中文版）', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 推荐教材合集（3本）', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 指定教材高清扫描版', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 原版英文教材影印本', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 辅助教材与学习指导', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 考研指定参考书目合集', 'category': '教材', 'format': 'pdf'},
    {'title': '{course} 经典著作选读', 'category': '教材', 'format': 'pdf'},

    # ── 习题集 (12) ──
    {'title': '{course} 课后习题详细答案', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 经典例题精讲与拓展', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 章节同步练习题集', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 配套习题全解（官方）', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 易错题专项训练集', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 小题狂练1000题', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 编程作业参考代码', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 综合练习题库与答案', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 考研专业课习题精编', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 实验上机题汇编', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 真题题型分类训练', 'category': '习题集', 'format': 'pdf'},
    {'title': '{course} 教材习题参考答案（手写版）', 'category': '习题集', 'format': 'pdf'},

    # ── 实验报告 (8) ──
    {'title': '{course} 实验报告标准模板', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 课程设计报告参考范例', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 实验操作详细指南', 'category': '实验报告', 'format': 'pdf'},
    {'title': '{course} 专题研究报告精选', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 上机实验指导书', 'category': '实验报告', 'format': 'pdf'},
    {'title': '{course} 实验数据处理与分析模板', 'category': '实验报告', 'format': 'xlsx'},
    {'title': '{course} 综合实验设计与报告', 'category': '实验报告', 'format': 'docx'},
    {'title': '{course} 虚拟仿真实验指导', 'category': '实验报告', 'format': 'pdf'},

    # ── 历年真题 (6) ──
    {'title': '{course} 近十年考研真题汇编（完整）', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 历年期末真题回忆整理', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 考研真题深度解析', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 专业课统考真题合集', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 复试面试真题整理', 'category': '历年真题', 'format': 'pdf'},
    {'title': '{course} 历年考题知识点分布分析', 'category': '历年真题', 'format': 'pdf'},

    # ── 课件讲义 (6) ──
    {'title': '{course} PPT课件完整合集', 'category': '课件讲义', 'format': 'pptx'},
    {'title': '{course} 教学视频配套讲义', 'category': '课件讲义', 'format': 'pdf'},
    {'title': '{course} 课程教学大纲与进度表', 'category': '课件讲义', 'format': 'pdf'},
    {'title': '{course} 教师授课讲稿整理', 'category': '课件讲义', 'format': 'pdf'},
    {'title': '{course} 全套教学课件（修订版）', 'category': '课件讲义', 'format': 'pptx'},
    {'title': '{course} 公开课MOOC配套资料', 'category': '课件讲义', 'format': 'pdf'},

    # ── NEW: 考研专区 (5) ──
    {'title': '{course} 考研全程复习规划', 'category': '考研专区', 'format': 'pdf'},
    {'title': '{course} 考研专业课笔记精编', 'category': '考研专区', 'format': 'pdf'},
    {'title': '{course} 考研复试经验合集', 'category': '考研专区', 'format': 'pdf'},
    {'title': '{course} 导师研究方向与论文导读', 'category': '考研专区', 'format': 'pdf'},
    {'title': '{course} 考研调剂信息与攻略', 'category': '考研专区', 'format': 'pdf'},
]

SEMESTERS = [
    '2023-2024-1', '2023-2024-2',
    '2024-2025-1', '2024-2025-2',
    '2025-2026-1', '2025-2026-2',
]

TEACHERS = [
    '张教授', '李教授', '王教授', '刘教授', '陈教授',
    '赵老师', '周老师', '孙老师', '黄教授', '吴教授',
    '郑教授', '杨教授', '朱教授', '马老师', '胡老师',
    '林老师', '何老师', '郭老师', '谢教授', '韩教授',
    '唐老师', '冯老师', '曹老师', '许老师', '宋老师',
    '邓老师', '徐教授', '梁教授', '彭教授', '蒋教授',
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

# ════════════════════════════════════════════════════════════════════════════
# 5. Comment templates — for realistic-looking comment text
# ════════════════════════════════════════════════════════════════════════════

COMMENT_TEMPLATES = [
    '太有用了！感谢分享',
    '请问有最新的版本吗？',
    '这个资料帮了大忙，期末复习就靠它了',
    '质量很高，推荐给学弟学妹',
    '有没有配套的视频教程？',
    '请问有XX章节的资料吗？',
    '已经下载了，非常清晰',
    '这个资源真的不错，考试利器',
    '感谢楼主，好人一生平安',
    '有没有人分享一下实验报告模板？',
    '这个总结太到位了，比自己整理的好',
    '跪求2025年的真题',
    '请问有答案吗？',
    '太棒了，一直在找这个',
    '这个资料不全，缺了最后两章',
    '请问pdf版清晰度怎么样？',
    '非常有条理，比老师讲的还清楚',
    '有没有期末考试重点？',
    '谢谢学长/学姐！',
    '这个笔记记得真好，自己能分享吗？',
    '已经推荐给室友了',
    '有没有英文版的？',
    '求一份参考答案',
    '这个格式打不开，能传pdf吗？',
    '感谢分享，论文有救了',
]


def _build_parts(tpl: dict, course_name: str) -> list[dict] | None:
    """Generate multi-file parts based on category and format."""
    category = tpl['category']
    fmt = tpl['format']

    if category == '课件讲义' and fmt == 'pptx':
        n = random.randint(2, 4)
        return [
            {'filename': f'{course_name}_第{i*4-3}-{min(i*4, 16)}章.pptx',
             'storage_key': f'mock/storage/{random.randint(10000, 99999)}_ch{i*4-3}-{min(i*4,16)}.pptx',
             'file_size': random.randint(2_000_000, 15_000_000), 'format': 'pptx'}
            for i in range(1, n + 1)
        ]

    if category == '实验报告' and fmt in ('docx', 'pdf'):
        parts = [
            {'filename': f'{course_name}_实验报告.{fmt}', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_report.{fmt}', 'file_size': random.randint(500_000, 5_000_000), 'format': fmt},
            {'filename': f'{course_name}_实验数据.xlsx', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_data.xlsx', 'file_size': random.randint(50_000, 500_000), 'format': 'xlsx'},
        ]
        if random.random() > 0.4:
            parts.append({'filename': f'{course_name}_源码.zip', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_code.zip', 'file_size': random.randint(100_000, 3_000_000), 'format': 'zip'})
        return parts

    if category == '习题集' and '代码' in tpl.get('title', ''):
        return [
            {'filename': f'{course_name}_源码.zip', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_src.zip', 'file_size': random.randint(100_000, 5_000_000), 'format': 'zip'},
            {'filename': f'{course_name}_说明文档.pdf', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_readme.pdf', 'file_size': random.randint(50_000, 1_000_000), 'format': 'pdf'},
        ]

    if category == '教材':
        return [
            {'filename': f'{course_name}_上册.pdf', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_vol1.pdf', 'file_size': random.randint(20_000_000, 80_000_000), 'format': 'pdf'},
            {'filename': f'{course_name}_下册.pdf', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_vol2.pdf', 'file_size': random.randint(15_000_000, 60_000_000), 'format': 'pdf'},
        ]

    if random.random() < 0.25:
        return [
            {'filename': f'{course_name}_主文件.{fmt}', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_main.{fmt}', 'file_size': random.randint(500_000, 20_000_000), 'format': fmt},
            {'filename': f'{course_name}_附录.{fmt}', 'storage_key': f'mock/storage/{random.randint(10000, 99999)}_appendix.{fmt}', 'file_size': random.randint(50_000, 2_000_000), 'format': fmt},
        ]

    return None


async def _ensure_badge(db, user_id, badge_type, label='', description='') -> int:
    """Create badge if it doesn't exist. Returns 1 if created."""
    result = await db.execute(select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_type == badge_type))
    if result.scalar_one_or_none():
        return 0
    db.add(UserBadge(user_id=user_id, badge_type=badge_type))
    db.add(Notification(
        user_id=user_id, type='badge_awarded',
        title=f'🎖 恭喜获得【{label or badge_type}】徽章！',
        body=description or '感谢你对川流课栈的贡献',
        resource_type='badge', resource_id=badge_type,
    ))
    return 1


async def seed():
    async with async_session() as db:
        # ── 1. Update college metadata ──
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

        # ── 2. Create users ──
        mock_users: dict[str, User] = {}
        for mu in MOCK_USERS:
            encrypted_phone = encrypt_pii(mu['phone'])
            result = await db.execute(select(User).where(User.phone == encrypted_phone))
            user = result.scalar()
            if not user:
                result = await db.execute(select(User).where(User.phone == mu['phone']))
                user = result.scalar()
            if not user:
                user = User(
                    phone=encrypted_phone, nickname=mu['nickname'],
                    role=mu['role'], trust_score=mu['trust_score'],
                    public_display_name=mu['display_name'],
                    password_hash=MOCK_PASSWORD_HASH,
                )
                db.add(user)
                await db.flush()
            else:
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
                phone=encrypted_maintainer, nickname='管理员', role='maintainer',
                trust_score=100, public_display_name='川流课栈管理员',
                password_hash=MOCK_PASSWORD_HASH,
            )
            db.add(maintainer)
            await db.flush()
        else:
            if maintainer.phone == MAINTAINER_PHONE:
                maintainer.phone = encrypted_maintainer
            if not maintainer.password_hash:
                maintainer.password_hash = MOCK_PASSWORD_HASH

        user_list = list(mock_users.values())
        valid_contributors = [u for u in user_list if u.trust_score >= 75]
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
                    college_id=college.id, name=name, slug=slug,
                    category=cat, credit=credit, description=desc, aliases=[],
                )
                db.add(course)
                new_courses.append(course)
                existing_courses.add(name)
        await db.flush()
        print(f'Created {len(new_courses)} new courses')

        # ── 4. Create materials — 30-45 per course for data richness ──
        all_courses = (await db.execute(select(Course))).scalars().all()
        existing_titles = set((await db.execute(select(Material.title))).scalars().all())
        new_materials: list[Material] = []
        total_parts = 0
        # Assign "power users" to courses they belong to (college-matched) for realistic distribution
        college_users: dict[str, list[User]] = {}
        for mu in MOCK_USERS:
            college_users.setdefault(mu['college'], []).append(mock_users[mu['phone']])

        for course in all_courses:
            college_name = next((cn for cn, cl in colleges.items() if cl.id == course.college_id), None)
            pool = college_users.get(college_name, valid_contributors) or valid_contributors
            n_templates = random.randint(25, 40)
            templates = random.sample(MATERIAL_TEMPLATES, min(n_templates, len(MATERIAL_TEMPLATES)))
            for tpl in templates:
                title = tpl['title'].format(course=course.name[:15])
                if title in existing_titles:
                    continue
                days_ago = random.randint(1, 730)
                dl = random.randint(0, 2000)
                rc = random.randint(0, dl + random.randint(0, 120))
                contributor = random.choice(pool)
                parts = _build_parts(tpl, course.name[:15])
                trust_status = random.choices(
                    ['community_verified', 'maintainer_picked', 'unverified'],
                    weights=[40, 15, 45],
                )[0]

                m = Material(
                    course_id=course.id, title=title,
                    description=f'{course.name} — {tpl["category"]}，由同学整理上传。包含完整内容，适合复习备考使用。',
                    category=tpl['category'], semester=random.choice(SEMESTERS),
                    teacher=random.choice(TEACHERS),
                    source_type='hosted', format=tpl['format'],
                    file_size=random.randint(200_000, 80_000_000),
                    file_hash=f'sha256_{random.randint(100000, 999999)}_{random.randint(100000, 999999)}',
                    trust_status=trust_status,
                    review_status='approved',
                    average_rating=round(random.uniform(2.0, 5.0), 2),
                    rating_count=rc, download_count=dl,
                    contributor_id=contributor.id, parts=parts,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                    updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_ago)),
                )
                db.add(m)
                new_materials.append(m)
                existing_titles.add(title)
                if parts:
                    total_parts += 1

        await db.flush()
        print(f'Created {len(new_materials)} materials ({total_parts} with multi-file parts)')

        # ── 5. Seed ratings ──
        result = await db.execute(
            select(Material.id, Material.average_rating, Material.rating_count)
            .where(Material.review_status == 'approved')
        )
        all_materials = [(r[0], float(r[1] or 0), r[2]) for r in result.fetchall()]
        rating_seeded = 0
        for mid, _avg, rc in all_materials:
            existing = await db.scalar(sa_text("SELECT COUNT(*) FROM ratings WHERE material_id = :mid").bindparams(mid=mid))
            if existing:
                continue
            n = min(rc, 30)
            for _ in range(n):
                score = max(1, min(5, random.choices([1, 2, 3, 4, 5], weights=[
                    3, 8, 20, 35, 34
                ])[0]))
                await db.execute(sa_text(
                    "INSERT INTO ratings (material_id, user_id, score, created_at) "
                    "VALUES (:mid, (SELECT id FROM users ORDER BY RANDOM() LIMIT 1), :score, "
                    "NOW() - (:days || ' days')::interval) "
                    "ON CONFLICT (material_id, user_id) DO NOTHING"
                ).bindparams(mid=mid, score=score, days=str(random.randint(0, 180))))
                rating_seeded += 1
        await db.commit()
        print(f'Seeded {rating_seeded} individual ratings across {len(all_materials)} materials')

        # ── 6. Seed collections ──
        top_materials = sorted(new_materials, key=lambda m: m.download_count or 0, reverse=True)[:80]
        collection_count = 0
        for user in random.sample(user_list, 12):
            if len(top_materials) < 3:
                continue
            coll_names = ['期末复习必备', '考研资料合集', '高分笔记精选', '历年真题汇总', '专业课宝典']
            for cname in random.sample(coll_names, min(2, len(coll_names))):
                coll = Collection(
                    user_id=user.id, title=cname,
                    description=f'{user.nickname} 整理的{cname}',
                    is_public=random.random() > 0.3,
                )
                db.add(coll)
                await db.flush()
                picked = random.sample(top_materials, random.randint(3, 12))
                for i, m in enumerate(picked):
                    db.add(CollectionItem(collection_id=coll.id, material_id=m.id, sort_order=i))
                collection_count += 1
        await db.flush()
        print(f'Created {collection_count} collections')

        # ── 7. Seed comments ──
        comment_count = 0
        for m in random.sample(new_materials, len(new_materials) // 4):
            n_comments = random.randint(0, 6)
            commenters = random.sample(user_list, min(n_comments, len(user_list)))
            parent_id = None
            for cuser in commenters:
                text = random.choice(COMMENT_TEMPLATES)
                days_ago = random.randint(1, 365)
                comment = Comment(
                    material_id=m.id, user_id=cuser.id,
                    content=text, parent_id=parent_id,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                )
                db.add(comment)
                comment_count += 1
                # ~30% chance next comment is a reply
                if random.random() < 0.3:
                    parent_id = comment.id if parent_id is None else parent_id
                else:
                    parent_id = None
        await db.flush()
        print(f'Created {comment_count} comments')

        # ── 8. Seed bookmarks ──
        bookmark_count = 0
        for user in random.sample(user_list, 20):
            bookmarked_materials = random.sample(new_materials, random.randint(2, 15))
            for m in bookmarked_materials:
                existing = await db.execute(
                    sa_text("SELECT 1 FROM bookmarks WHERE user_id = :uid AND material_id = :mid")
                    .bindparams(uid=user.id, mid=m.id)
                )
                if existing.fetchone():
                    continue
                db.add(Bookmark(user_id=user.id, material_id=m.id))
                bookmark_count += 1
            # Also bookmark some courses
            bookmarked_courses = random.sample(all_courses, random.randint(1, 5))
            for c in bookmarked_courses:
                existing = await db.execute(
                    sa_text("SELECT 1 FROM bookmarks WHERE user_id = :uid AND course_id = :cid")
                    .bindparams(uid=user.id, cid=c.id)
                )
                if existing.fetchone():
                    continue
                db.add(Bookmark(user_id=user.id, course_id=c.id))
                bookmark_count += 1
        await db.flush()
        print(f'Created {bookmark_count} bookmarks')

        # ── 9. Seed wishes ──
        wish_count = 0
        wish_texts = [
            '求{course}的期末真题', '希望有人上传{course}的笔记', '需要{course}的课后习题答案',
            '跪求{course}的PPT课件', '有没有{course}的考研资料？', '急需{course}的实验报告模板',
        ]
        for user in random.sample(user_list, 10):
            target_courses = random.sample(all_courses, random.randint(1, 4))
            for course in target_courses:
                text = random.choice(wish_texts).format(course=course.name)
                db.execute(
                    sa_text(
                        "INSERT INTO wishes (user_id, course_id, description, vote_count, created_at) "
                        "VALUES (:uid, :cid, :desc, :vc, NOW() - (:days || ' days')::interval) "
                        "ON CONFLICT DO NOTHING"
                    ).bindparams(
                        uid=user.id, cid=course.id, desc=text,
                        vc=random.randint(0, 25),
                        days=str(random.randint(1, 180)),
                    )
                )
                wish_count += 1
        await db.commit()
        print(f'Created {wish_count} wishes')

        # ── 10. Seed badges ──
        badge_count = 0
        for user in user_list:
            user_materials = [m for m in new_materials if m.contributor_id == user.id]
            if user_materials:
                badge_count += await _ensure_badge(db, user.id, 'first_upload', '首次上传', '第一次上传资料')
            if len(user_materials) >= 10:
                badge_count += await _ensure_badge(db, user.id, 'prolific_10', '高产作者·铜', '累计上传10份资料')
            if len(user_materials) >= 50:
                badge_count += await _ensure_badge(db, user.id, 'prolific_50', '高产作者·银', '累计上传50份资料')
            top_dl = max((m.download_count or 0) for m in user_materials) if user_materials else 0
            if top_dl >= 100:
                badge_count += await _ensure_badge(db, user.id, 'popular_100', '人气之星', f'资料最高下载量 {top_dl}')
            if top_dl >= 1000:
                badge_count += await _ensure_badge(db, user.id, 'popular_1000', '人气之星·银', f'资料最高下载量 {top_dl}')
            if random.random() < 0.3:
                badge_count += await _ensure_badge(db, user.id, 'selfless', '无私奉献', '上传资料后持续维护')
            if random.random() < 0.15:
                badge_count += await _ensure_badge(db, user.id, 'continuous_3', '持之以恒', '连续3个学期贡献资料')
        print(f'Created {badge_count} user badges')

        # ── 11. Calendar ──
        result = await db.execute(select(AcademicCalendar.event_name))
        existing_events = set(result.scalars().all())
        new_events = 0
        for semester, name, tag, start, end in CALENDAR_EVENTS:
            if name in existing_events:
                continue
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
            db.add(AcademicCalendar(
                year=start_date.year, semester=semester,
                event_name=name, event_tag=tag,
                start_date=start_date, end_date=end_date,
            ))
            new_events += 1
        await db.commit()
        print(f'Created {new_events} calendar events')

        # ── 12. Redis hot search keywords ──
        try:
            from app.core.redis import redis
            hot_keywords = {
                '高等数学': 278, '线性代数': 245, 'C语言程序设计': 203, '大学物理': 189,
                '概率论与数理统计': 176, '数据结构与算法': 165, '大学英语四级': 154, '马克思主义基本原理': 142,
                '操作系统': 138, '计算机网络': 132, '数据库系统概论': 125, '软件工程导论': 118,
                '编译原理': 112, '离散数学': 108, 'Java程序设计': 98, 'Python基础': 92,
                '电路分析基础': 87, '微积分': 83, '毛概': 79, '计算机组成原理': 74,
                '有机化学': 68, '微观经济学': 65, '人体解剖学': 62, '信号与系统': 58,
                '机械设计基础': 55, '材料科学基础': 51, '刑法学': 48, '民法学': 45,
                '管理学原理': 42, '流行病学': 39, '口腔修复学': 36, '药物化学': 33,
            }
            for kw, score in hot_keywords.items():
                await redis.zadd('search:hot:weekly', {kw: score})
            await redis.expire('search:hot:weekly', 604800)
            print(f'Seeded {len(hot_keywords)} Redis hot search keywords')
        except Exception as e:
            print(f'Redis hot search seed skipped: {e}')

        # ── Summary ──
        cc = (await db.execute(select(func.count()).select_from(Course))).scalar()
        mc = (await db.execute(select(func.count()).select_from(Material).where(Material.review_status == 'approved'))).scalar()
        uc = (await db.execute(select(func.count()).select_from(User))).scalar()
        evc = (await db.execute(select(func.count()).select_from(AcademicCalendar))).scalar()
        bc = (await db.execute(select(func.count()).select_from(UserBadge))).scalar()
        collc = (await db.execute(select(func.count()).select_from(Collection))).scalar()
        comc = (await db.execute(select(func.count()).select_from(Comment))).scalar()
        bmc = (await db.execute(select(func.count()).select_from(Bookmark))).scalar()
        colleges_with_data = len({c.college_id for c in all_courses})
        print(f'Done. DB: {len(colleges)} colleges ({colleges_with_data} with courses), {cc} courses, '
              f'{mc} approved materials, {uc} users, {bc} badges, {collc} collections, '
              f'{comc} comments, {bmc} bookmarks, {evc} calendar events')


if __name__ == '__main__':
    asyncio.run(seed())
