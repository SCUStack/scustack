"""Cover image matching simulation v2 — four-dimensional tag-weight matching.

Tag dimensions (with weights):
  Category ×3 — 考试资料/复习提纲/课堂笔记/教材/习题集/实验报告/历年真题/课件讲义
  Subject  ×2 — 数学/物理/化学/生物/计算机/经济/电子/医学/文学/...
  Format   ×1 — 手写/扫描/电子/打印/装订/影印/...
  Vibe     ×1 — 整洁/泛黄/彩色/简约/密集/温暖/学术/...

Scoring: weighted sum of tag intersections, then hash tie-break.
"""
import random
from collections import Counter, defaultdict


# ══════════════════════════════════════════════════════════════════════
# Tag weights
# ══════════════════════════════════════════════════════════════════════

W_CATEGORY = 3
W_SUBJECT = 2
W_FORMAT = 1
W_VIBE = 1


# ══════════════════════════════════════════════════════════════════════
# Cover pool — each entry: (filename, {dim: set_of_tags})
# Now covers can span multiple subjects within a category
# ══════════════════════════════════════════════════════════════════════

COVER_POOL: dict[str, list[tuple[str, dict[str, set[str]]]]] = {
    '考试资料': [
        ('exam_math',     {'cat': {'考试','试卷','真题','答题卡','答案','解析','计算'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'打印','整洁'}, 'vibe': {'学术','简约','整洁'}}),
        ('exam_physics',  {'cat': {'考试','试卷','真题','答题卡','计算'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'打印','整洁'}, 'vibe': {'学术','整洁'}}),
        ('exam_cs',       {'cat': {'考试','试卷','真题','答题卡','编程'}, 'sub': {'计算机','编程','代码','算法'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_chem',     {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'化学','有机','无机'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_bio',      {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
        ('exam_econ',     {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'打印'}, 'vibe': {'学术','简约'}}),
        ('exam_med',      {'cat': {'考试','试卷','真题','答题卡','名词解释'}, 'sub': {'医学','解剖','病理','药学','诊断'}, 'fmt': {'打印'}, 'vibe': {'学术','密集'}}),
        ('exam_lit',      {'cat': {'考试','试卷','真题','答题卡','论述','名词解释'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_ee',       {'cat': {'考试','试卷','真题','答题卡','计算','电路'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_generic1', {'cat': {'考试','试卷','真题','批改','红笔','纠错'}, 'sub': set(), 'fmt': {'手写','批改'}, 'vibe': {'泛黄','温暖','密集'}}),
        ('exam_generic2', {'cat': {'考试','准考证','考场','答题卡','填空','选择'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'密集','学术'}}),
        ('exam_generic3', {'cat': {'考试','成绩单','分数','解析','答案','详解'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'整洁','学术','简约'}}),
        ('exam_generic4', {'cat': {'考试','补考','样卷','小题','大题','模拟'}, 'sub': set(), 'fmt': {'影印'}, 'vibe': {'密集','泛黄'}}),
        ('exam_generic5', {'cat': {'考试','试卷','真题','答题卡'}, 'sub': set(), 'fmt': {'打印','装订'}, 'vibe': {'整洁','简约'}}),
        ('exam_generic6', {'cat': {'考试','复习','资料','试题','题库'}, 'sub': set(), 'fmt': {'电子','打印'}, 'vibe': {'简约','现代'}}),
        ('exam_traffic',  {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'交通','运输','道路'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_water',    {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_nuclear',  {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'核工程','核物理','核技术'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
        ('exam_aero',     {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('exam_arch',     {'cat': {'考试','试卷','真题','答题卡'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'打印'}, 'vibe': {'学术','简约'}}),
    ],
    '复习提纲': [
        ('review_math',    {'cat': {'复习','提纲','思维导图','公式','定理','框架'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'手写','彩色'}, 'vibe': {'整洁','彩色','温暖'}}),
        ('review_physics', {'cat': {'复习','提纲','框架','公式','定理'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'手写'}, 'vibe': {'整洁','学术'}}),
        ('review_cs',      {'cat': {'复习','提纲','思维导图','框架','专题'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'电子','彩色'}, 'vibe': {'彩色','简约','现代'}}),
        ('review_chem',    {'cat': {'复习','提纲','总结','归纳','重点'}, 'sub': {'化学','有机','无机'}, 'fmt': {'手写','彩色'}, 'vibe': {'彩色','整洁'}}),
        ('review_bio',     {'cat': {'复习','提纲','总结','重点','考点','高频'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'打印','彩色'}, 'vibe': {'整洁','学术'}}),
        ('review_econ',    {'cat': {'复习','提纲','框架','重点','考点'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'打印'}, 'vibe': {'简约','整洁'}}),
        ('review_med',     {'cat': {'复习','提纲','背诵','口诀','重点','考点'}, 'sub': {'医学','解剖','病理','药学','诊断'}, 'fmt': {'打印'}, 'vibe': {'密集','学术'}}),
        ('review_lit',     {'cat': {'复习','提纲','框架','重点','考点'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'打印','手写'}, 'vibe': {'整洁','温暖'}}),
        ('review_ee',      {'cat': {'复习','提纲','公式','框架','重点'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'打印','电子'}, 'vibe': {'学术','整洁'}}),
        ('review_generic1',{'cat': {'复习','提纲','总结','重点','荧光笔','标注'}, 'sub': set(), 'fmt': {'手写','彩色'}, 'vibe': {'彩色','温暖','整洁'}}),
        ('review_generic2',{'cat': {'复习','提纲','背诵','口诀','记忆','速记'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'密集','整洁'}}),
        ('review_generic3',{'cat': {'复习','错题','易错','纠错','总结','归纳'}, 'sub': set(), 'fmt': {'手写','扫描'}, 'vibe': {'泛黄','温暖'}}),
        ('review_generic4',{'cat': {'复习','提纲','速查','速记','概要','框架'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'简约','整洁','现代'}}),
        ('review_generic5',{'cat': {'复习','思维导图','框架','专题','整理'}, 'sub': set(), 'fmt': {'电子','彩色'}, 'vibe': {'彩色','现代'}}),
        ('review_generic6',{'cat': {'复习','提纲','总结','重点','归纳'}, 'sub': set(), 'fmt': {'手写','扫描'}, 'vibe': {'整洁','学术'}}),
        ('review_traffic',{'cat': {'复习','提纲','框架','总结'}, 'sub': {'交通','运输','道路'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('review_water',  {'cat': {'复习','提纲','总结','重点'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('review_aero',   {'cat': {'复习','提纲','框架','专题'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
        ('review_arch',   {'cat': {'复习','提纲','总结','重点'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'打印','电子'}, 'vibe': {'简约','整洁'}}),
    ],
    '课堂笔记': [
        ('notes_math',    {'cat': {'笔记','课堂','手写','标注','整理'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'手写','扫描'}, 'vibe': {'整洁','学术','温暖'}}),
        ('notes_physics', {'cat': {'笔记','课堂','手写','记录','听课'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'手写','扫描'}, 'vibe': {'整洁','学术'}}),
        ('notes_cs',      {'cat': {'笔记','课堂','电子','标注','代码'}, 'sub': {'计算机','编程','代码','算法'}, 'fmt': {'电子','彩色'}, 'vibe': {'彩色','简约','现代'}}),
        ('notes_chem',    {'cat': {'笔记','课堂','手写','标注','彩色'}, 'sub': {'化学','有机','无机'}, 'fmt': {'手写','彩色'}, 'vibe': {'彩色','整洁'}}),
        ('notes_bio',     {'cat': {'笔记','课堂','手写','标注'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'手写'}, 'vibe': {'整洁','学术'}}),
        ('notes_econ',    {'cat': {'笔记','课堂','打印','整理'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'打印'}, 'vibe': {'简约','整洁'}}),
        ('notes_med',     {'cat': {'笔记','课堂','手写','标注','记录'}, 'sub': {'医学','解剖','病理','药学','诊断'}, 'fmt': {'手写','打印'}, 'vibe': {'密集','学术'}}),
        ('notes_lit',     {'cat': {'笔记','课堂','手写','记录','标注'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'手写','打印'}, 'vibe': {'整洁','温暖'}}),
        ('notes_ee',      {'cat': {'笔记','课堂','手写','标注'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'手写','电子'}, 'vibe': {'学术','整洁'}}),
        ('notes_generic1',{'cat': {'笔记','课堂','手写','扫描','标注','整理'}, 'sub': set(), 'fmt': {'手写','扫描'}, 'vibe': {'泛黄','温暖','学术'}}),
        ('notes_generic2',{'cat': {'笔记','课堂','笔记本','标注','彩色'}, 'sub': set(), 'fmt': {'手写','彩色'}, 'vibe': {'彩色','整洁','温暖'}}),
        ('notes_generic3',{'cat': {'笔记','电子','iPad','平板','标注'}, 'sub': set(), 'fmt': {'电子','彩色'}, 'vibe': {'简约','彩色','现代'}}),
        ('notes_generic4',{'cat': {'笔记','便签','贴纸','彩色','标注'}, 'sub': set(), 'fmt': {'手写'}, 'vibe': {'彩色','温暖'}}),
        ('notes_generic5',{'cat': {'笔记','课堂','随堂','记录','听课'}, 'sub': set(), 'fmt': {'手写','扫描'}, 'vibe': {'整洁','学术'}}),
        ('notes_generic6',{'cat': {'笔记','电子','打印','整理'}, 'sub': set(), 'fmt': {'打印','电子'}, 'vibe': {'简约','整洁','现代'}}),
    ],
    '教材': [
        ('text_math',    {'cat': {'教材','课本','参考书','经典','合集'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'装订'}, 'vibe': {'学术','整洁','经典'}}),
        ('text_physics', {'cat': {'教材','课本','参考书','经典'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_cs',      {'cat': {'教材','课本','参考书','编程','经典'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'装订'}, 'vibe': {'学术','简约','现代'}}),
        ('text_chem',    {'cat': {'教材','课本','参考书'}, 'sub': {'化学','有机','无机'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_bio',     {'cat': {'教材','课本','参考书'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_econ',    {'cat': {'教材','课本','参考书'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'装订'}, 'vibe': {'学术','简约'}}),
        ('text_med',     {'cat': {'教材','课本','参考书','经典'}, 'sub': {'医学','解剖','病理','药学','诊断'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_lit',     {'cat': {'教材','课本','参考书','经典'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'装订'}, 'vibe': {'学术','经典','温暖'}}),
        ('text_ee',      {'cat': {'教材','课本','参考书'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_generic1',{'cat': {'教材','课本','书架','图书馆','合集','经典'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'温暖','学术','经典'}}),
        ('text_generic2',{'cat': {'教材','旧书','泛黄','经典','原版','影印'}, 'sub': set(), 'fmt': {'装订','影印'}, 'vibe': {'泛黄','温暖','经典'}}),
        ('text_generic3',{'cat': {'教材','翻页','阅读','学习','整理'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'温暖','整洁'}}),
        ('text_generic4',{'cat': {'教材','书桌','学习','整理'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'整洁','简约','现代'}}),
        ('text_generic5',{'cat': {'教材','堆积','参考书','推荐','合集'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'密集','学术'}}),
        ('text_generic6',{'cat': {'教材','电子','PDF','电子版'}, 'sub': set(), 'fmt': {'电子'}, 'vibe': {'现代','简约'}}),
        ('text_traffic',{'cat': {'教材','课本','参考书'}, 'sub': {'交通','运输','道路'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_water',  {'cat': {'教材','课本','参考书'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_aero',   {'cat': {'教材','课本','参考书','经典'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'装订'}, 'vibe': {'学术','经典'}}),
        ('text_arch',   {'cat': {'教材','课本','参考书','经典'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'装订'}, 'vibe': {'学术','简约'}}),
    ],
    '习题集': [
        ('prob_math',    {'cat': {'习题','作业','演算','计算','专项','证明'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'手写','草稿'}, 'vibe': {'密集','学术','泛黄'}}),
        ('prob_physics', {'cat': {'习题','作业','计算','公式','推导'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'手写','草稿'}, 'vibe': {'密集','学术'}}),
        ('prob_cs',      {'cat': {'习题','编程','代码','算法','上机'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'电子'}, 'vibe': {'简约','整洁','现代'}}),
        ('prob_chem',    {'cat': {'习题','作业','计算','专项','课后'}, 'sub': {'化学','有机','无机'}, 'fmt': {'手写'}, 'vibe': {'密集','学术'}}),
        ('prob_bio',     {'cat': {'习题','作业','习题','课后','练习'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'打印'}, 'vibe': {'整洁','学术'}}),
        ('prob_econ',    {'cat': {'习题','计算','应用','专项','课后'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'打印'}, 'vibe': {'简约','整洁'}}),
        ('prob_med',     {'cat': {'习题','作业','习题','练习','课后'}, 'sub': {'医学','解剖','病理','药学','诊断'}, 'fmt': {'打印'}, 'vibe': {'密集','学术'}}),
        ('prob_lit',     {'cat': {'习题','作业','习题','练习'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'打印'}, 'vibe': {'整洁','学术'}}),
        ('prob_ee',      {'cat': {'习题','作业','计算','电路','课后'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'手写','打印'}, 'vibe': {'密集','学术'}}),
        ('prob_generic1',{'cat': {'习题','草稿','演算','计算','推导'}, 'sub': set(), 'fmt': {'手写','草稿'}, 'vibe': {'密集','泛黄','温暖'}}),
        ('prob_generic2',{'cat': {'习题','小题','填空','题库','选择'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'密集','整洁','学术'}}),
        ('prob_generic3',{'cat': {'习题','计算器','公式','数学','计算'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('prob_generic4',{'cat': {'习题','作业本','练习','课后','作业'}, 'sub': set(), 'fmt': {'手写'}, 'vibe': {'温暖','整洁'}}),
        ('prob_generic5',{'cat': {'习题','编程','代码','上机','综合'}, 'sub': set(), 'fmt': {'电子'}, 'vibe': {'简约','现代'}}),
        ('prob_generic6',{'cat': {'习题','题库','专项','训练','综合'}, 'sub': set(), 'fmt': {'打印','装订'}, 'vibe': {'密集','学术'}}),
        ('prob_traffic',{'cat': {'习题','作业','计算','课后'}, 'sub': {'交通','运输','道路'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('prob_water',  {'cat': {'习题','作业','计算','课后'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('prob_aero',   {'cat': {'习题','计算','推导','专项'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
        ('prob_arch',   {'cat': {'习题','作业','设计','课后'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'打印','电子'}, 'vibe': {'简约','整洁'}}),
    ],
    '实验报告': [
        ('lab_physics', {'cat': {'实验','数据','图表','分析','报告','记录'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_chem',    {'cat': {'实验','操作','规范','步骤','报告','记录'}, 'sub': {'化学','有机','无机'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_bio',     {'cat': {'实验','观察','数据','分析','报告','显微镜'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_cs',      {'cat': {'实验','编程','代码','数据','报告','上机'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'电子'}, 'vibe': {'简约','现代'}}),
        ('lab_med',     {'cat': {'实验','观察','数据','报告','记录'}, 'sub': {'医学','解剖','病理','诊断'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_ee',      {'cat': {'实验','数据','操作','报告','电路'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_generic1',{'cat': {'实验','显微镜','观察','报告','记录'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_generic2',{'cat': {'实验','器材','设备','操作','步骤'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'整洁','学术'}}),
        ('lab_generic3',{'cat': {'实验','数据','图表','分析','报告','记录'}, 'sub': set(), 'fmt': {'打印','彩色'}, 'vibe': {'学术','简约','现代'}}),
        ('lab_generic4',{'cat': {'实验','报告','模板','记录'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'简约','整洁'}}),
        ('lab_generic5',{'cat': {'实验','化学','试管','操作'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'整洁'}}),
        ('lab_generic6',{'cat': {'实验','数据','处理','分析','图表','报告'}, 'sub': set(), 'fmt': {'电子','打印'}, 'vibe': {'学术','现代'}}),
        ('lab_water',   {'cat': {'实验','数据','报告','记录'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'打印'}, 'vibe': {'学术','整洁'}}),
        ('lab_nuclear', {'cat': {'实验','操作','数据','报告'}, 'sub': {'核工程','核物理','核技术'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
        ('lab_aero',    {'cat': {'实验','数据','报告','记录'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'打印'}, 'vibe': {'学术'}}),
    ],
    '历年真题': [
        ('past_math',    {'cat': {'真题','历年','试卷','考研','解析','答案'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术','经典'}}),
        ('past_physics', {'cat': {'真题','历年','试卷','考研','解析'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_cs',      {'cat': {'真题','历年','试卷','考研','解析'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_chem',    {'cat': {'真题','历年','试卷','考研'}, 'sub': {'化学','有机','无机'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_bio',     {'cat': {'真题','历年','试卷','考研'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_econ',    {'cat': {'真题','历年','试卷','考研'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_med',     {'cat': {'真题','历年','试卷','考研','解析'}, 'sub': {'医学','解剖','病理','诊断'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_lit',     {'cat': {'真题','历年','试卷','考研'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术','温暖'}}),
        ('past_ee',      {'cat': {'真题','历年','试卷','考研'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_generic1',{'cat': {'真题','历年','旧试卷','档案','回忆','合集'}, 'sub': set(), 'fmt': {'影印'}, 'vibe': {'泛黄','温暖','经典'}}),
        ('past_generic2',{'cat': {'真题','泛黄','档案','历年','回忆','合集'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'泛黄','温暖','经典'}}),
        ('past_generic3',{'cat': {'真题','装订','成套','合集','十年','汇编'}, 'sub': set(), 'fmt': {'装订'}, 'vibe': {'泛黄','学术','经典'}}),
        ('past_generic4',{'cat': {'真题','答案','解析','详解'}, 'sub': set(), 'fmt': {'影印','打印'}, 'vibe': {'密集','整洁'}}),
        ('past_generic5',{'cat': {'真题','历年','汇编','回忆','合集'}, 'sub': set(), 'fmt': {'打印','装订'}, 'vibe': {'整洁','学术'}}),
        ('past_generic6',{'cat': {'真题','试卷','影印','复印'}, 'sub': set(), 'fmt': {'影印','装订'}, 'vibe': {'泛黄','学术'}}),
        ('past_traffic',{'cat': {'真题','历年','试卷','考研'}, 'sub': {'交通','运输','道路'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_water',  {'cat': {'真题','历年','试卷','考研'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_aero',   {'cat': {'真题','历年','试卷','考研'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
        ('past_arch',   {'cat': {'真题','历年','试卷','考研'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'装订','影印'}, 'vibe': {'泛黄','学术'}}),
    ],
    '课件讲义': [
        ('slides_math',   {'cat': {'课件','讲义','PPT','幻灯片','板书','教学'}, 'sub': {'数学','代数','几何','统计'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_physics',{'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'物理','力学','电磁'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_cs',     {'cat': {'课件','讲义','PPT','代码','教学'}, 'sub': {'计算机','编程','算法','代码'}, 'fmt': {'电子'}, 'vibe': {'简约','整洁','现代'}}),
        ('slides_chem',   {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'化学','有机','无机'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_bio',    {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'生物','遗传','细胞','分子'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_econ',   {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'经济','管理','会计','金融'}, 'fmt': {'电子'}, 'vibe': {'简约','整洁'}}),
        ('slides_med',    {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'医学','解剖','病理','诊断'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_lit',    {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'文学','汉语','语言','历史'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_ee',     {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'电子','电路','信号','通信'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_generic1',{'cat': {'课件','黑板','板书','教学','讲义','课堂'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'学术','整洁','经典'}}),
        ('slides_generic2',{'cat': {'课件','幻灯片','PPT','投影','演示'}, 'sub': set(), 'fmt': {'电子'}, 'vibe': {'简约','现代'}}),
        ('slides_generic3',{'cat': {'课件','讲台','教室','课堂','教学'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'温暖','学术'}}),
        ('slides_generic4',{'cat': {'课件','讲义','打印','完整','整理'}, 'sub': set(), 'fmt': {'打印'}, 'vibe': {'整洁','简约'}}),
        ('slides_generic5',{'cat': {'课件','PDF','电子','讲义'}, 'sub': set(), 'fmt': {'电子','打印'}, 'vibe': {'现代','简约'}}),
        ('slides_generic6',{'cat': {'课件','PPT','幻灯片','演示','教学'}, 'sub': set(), 'fmt': {'电子'}, 'vibe': {'学术','现代'}}),
        ('slides_traffic',{'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'交通','运输','道路'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_water',  {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'水利','水文','水资源'}, 'fmt': {'电子'}, 'vibe': {'学术','整洁'}}),
        ('slides_nuclear',{'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'核工程','核物理','核技术'}, 'fmt': {'电子'}, 'vibe': {'学术'}}),
        ('slides_aero',   {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'航空航天','飞行器','航天'}, 'fmt': {'电子'}, 'vibe': {'学术'}}),
        ('slides_arch',   {'cat': {'课件','讲义','PPT','幻灯片','教学'}, 'sub': {'建筑','设计','规划'}, 'fmt': {'电子'}, 'vibe': {'简约','现代'}}),
    ],
}


# ══════════════════════════════════════════════════════════════════════
# Expanded keyword/token extraction — Chinese academic vocabulary
# ══════════════════════════════════════════════════════════════════════

# Full subject name → short aliases for matching
# ══════════════════════════════════════════════════════════════════════
# Comprehensive subject alias map — sourced from MOE 2024 catalog (816 majors
# across 93 categories), engineering accreditation standards, and 30+ university
# curriculum plans. Covers all 12 discipline categories.
# ══════════════════════════════════════════════════════════════════════

from subject_aliases import SUBJECT_ALIASES

# Dimension-specific keywords
CATEGORY_KW = {
    '考试', '期末', '期中', '真题', '试卷', '答案', '解析', '试题', '答题',
    '模考', '补考', '样卷', '小题', '大题', '论述', '问答', '辨析', '判断',
    '单选', '多选', '名词解释', '完形', '阅读', '专项训练', '模拟题',
}
REVIEW_KW = {
    '复习', '提纲', '总结', '归纳', '重点', '考点', '高频', '思维导图',
    '易错', '错题', '框架', '概要', '速查', '背诵', '口诀', '对比表',
    '速记', '突击', '汇总', '整理', '专题',
}
NOTES_KW = {
    '笔记', '课堂', '手写', '扫描', '标注', '电子', '随堂', '听课',
    '心得', '记录', '彩色', '标注', '整理', 'iPad', '平板',
}
TEXTBOOK_KW = {
    '教材', '课本', '参考书', '经典', '原版', '影印', '译本', '合集',
    '电子版', '指定', '辅助', '推荐',
}
PROBLEM_KW = {
    '习题', '作业', '编程', '代码', '算法', '课后', '上机', '课程设计',
    '专项', '题库', '综合', '证明', '计算', '应用', '训练', '小题狂练',
    '练习', '解答', '参考答案',
}
LAB_KW = {
    '实验', '数据', '报告', '指导书', '操作', '规范', '模板', '现象',
    '处理', '步骤', '分析', '记录',
}
PAST_KW = {
    '历年', '考研', '汇编', '回忆', '真题', '十年', '合集',
}
SLIDES_KW = {
    '课件', '讲义', 'PPT', '黑板', '板书', '教学大纲', '幻灯片',
    '演示', '投影',
}
FORMAT_KW = {
    '手写', '扫描', '电子', '打印', '装订', '影印', '复印', '高清',
    '彩色', '黑白', '平板', 'iPad', '手机', '草稿', 'PDF',
    '扫描版', '电子版', '打印版', '影印本', '原卷', '套装',
    'A4', '活页', '装订成册',
}
VIBE_KW = {
    '泛黄', '旧', '整洁', '密集', '简约', '经典', '最新', '回忆',
    '完整', '整理', '详细', '简单', '精美', '清晰', '高清',
    '手绘', '原创', '自整理', '独家',
}

CATEGORY_KW_MAP = {
    '考试资料': CATEGORY_KW,
    '复习提纲': REVIEW_KW,
    '课堂笔记': NOTES_KW,
    '教材': TEXTBOOK_KW,
    '习题集': PROBLEM_KW,
    '实验报告': LAB_KW,
    '历年真题': PAST_KW,
    '课件讲义': SLIDES_KW,
}


def tokenize_multi_dim(text: str, known_category: str) -> dict[str, set[str]]:
    """Extract keywords across four dimensions from a material title.

    Returns: {'cat': set, 'sub': set, 'fmt': set, 'vibe': set}
    """
    tokens: dict[str, set[str]] = {
        'cat': set(), 'sub': set(), 'fmt': set(), 'vibe': set(),
    }

    # Category tokens from category-specific keyword sets
    cat_kw = CATEGORY_KW_MAP.get(known_category, set())
    for kw in cat_kw:
        if kw in text:
            tokens['cat'].add(kw)

    # Also check all category keyword pools (a title might say "真题笔记" for 考试资料)
    for kw in CATEGORY_KW | REVIEW_KW | NOTES_KW | TEXTBOOK_KW | PROBLEM_KW | LAB_KW | PAST_KW | SLIDES_KW:
        if kw in text:
            tokens['cat'].add(kw)

    # Subject tokens — match full course names first, then aliases
    for course, alias in SUBJECT_ALIASES.items():
        if course in text:
            tokens['sub'].add(alias)
    # Direct subject keyword match
    for kw in {'数学', '代数', '几何', '概率', '统计', '物理', '力学', '电磁',
               '化学', '有机', '无机', '生物', '遗传', '细胞', '分子',
               '计算机', '编程', '代码', '算法', '程序', '软件', '网络',
               '数据库', '电子', '电路', '信号', '通信', '管理', '经济',
               '会计', '金融', '医学', '解剖', '病理', '药学', '诊断',
               '文学', '汉语', '语言', '英语', '历史'}:
        if kw in text:
            tokens['sub'].add(kw)

    # Format tokens
    for kw in FORMAT_KW:
        if kw in text:
            tokens['fmt'].add(kw)

    # Vibe tokens
    for kw in VIBE_KW:
        if kw in text:
            tokens['vibe'].add(kw)

    return tokens


# ══════════════════════════════════════════════════════════════════════
# Weighted matching algorithm
# ══════════════════════════════════════════════════════════════════════

def match_cover(
    material: dict,
    pool: dict,
    rng: random.Random,
    w_subject: int = W_SUBJECT,
) -> tuple[str, float, str, dict]:
    """Match material to best cover using weighted multi-dim tag intersection.

    Score = W_CAT × |cat_tags ∩ cover_cat_tags|
          + W_SUB × |sub_tags ∩ cover_sub_tags|
          + W_FMT × |fmt_tags ∩ cover_fmt_tags|
          + W_VIBE × |vibe_tags ∩ cover_vibe_tags|
    """
    cat = material['category']
    candidates = pool.get(cat, [])
    if not candidates:
        candidates = [item for items in pool.values() for item in items]

    mat_tokens = material['tokens']

    scored = []
    for filename, cover_tags in candidates:
        score = (
            W_CATEGORY * len(mat_tokens['cat'] & cover_tags['cat'])
            + w_subject * len(mat_tokens['sub'] & cover_tags['sub'])
            + W_FORMAT * len(mat_tokens['fmt'] & cover_tags['fmt'])
            + W_VIBE * len(mat_tokens['vibe'] & cover_tags['vibe'])
        )
        scored.append((filename, score))

    max_score = max(s for _, s in scored)

    if max_score == 0:
        idx = abs(hash(material['title'])) % len(candidates)
        return candidates[idx][0], 0.0, 'random_fallback', {}

    top = [(f, s) for f, s in scored if s == max_score]
    idx = abs(hash(material['title'])) % len(top)

    # Build detail of which dimensions matched
    detail: dict[str, int] = {}
    best_cover_tags = next(ct for fn, ct in pool[cat] if fn == top[idx][0])
    detail['cat_hits'] = len(mat_tokens['cat'] & best_cover_tags['cat'])
    detail['sub_hits'] = len(mat_tokens['sub'] & best_cover_tags['sub'])
    detail['fmt_hits'] = len(mat_tokens['fmt'] & best_cover_tags['fmt'])
    detail['vibe_hits'] = len(mat_tokens['vibe'] & best_cover_tags['vibe'])

    return top[idx][0], float(max_score), f'tag_match(score={max_score})', detail


# ══════════════════════════════════════════════════════════════════════
# Material generation — realistic titles with explicit subjects
# ══════════════════════════════════════════════════════════════════════

def generate_materials(rng: random.Random) -> list[dict]:
    """Generate 250+ realistic material titles across subjects and categories."""

    # Subject × Category matrix
    courses_by_subject = {
        '数学': ['高等数学', '线性代数', '概率论与数理统计', '离散数学', '数学分析', '复变函数', '数值分析'],
        '物理': ['大学物理', '量子力学', '电磁学', '热力学与统计物理', '理论力学', '固体物理', '光学'],
        '计算机': ['C语言程序设计', '数据结构', '操作系统', '计算机网络', '数据库原理', '编译原理', '软件工程', '计算机组成原理', '人工智能导论', '机器学习'],
        '电子': ['数字电路', '模拟电子技术', '信号与系统', '通信原理', '电磁场与电磁波', '集成电路设计'],
        '化学': ['有机化学', '无机化学', '分析化学', '物理化学', '生物化学', '高分子化学', '化工原理'],
        '生物': ['细胞生物学', '分子生物学', '遗传学', '微生物学', '生理学', '免疫学'],
        '经济': ['微观经济学', '宏观经济学', '金融学', '计量经济学'],
        '管理': ['管理学原理', '会计学基础', '市场营销', '财务管理', '人力资源管理'],
        '医学': ['医学影像学', '人体解剖学', '病理学', '药理学', '诊断学', '内科学'],
        '文学': ['中国古代文学史', '现代汉语', '语言学概论', '外国文学史', '比较文学'],
    }

    templates_by_category = {
        '考试资料': [
            '{course}期末真题及答案解析',
            '{course}期中考试试卷',
            '{course}模拟试题集',
            '{course}历年真题汇编',
            '{course}补考真题',
            '{course}期末重点题型总结',
            '{course}选择题专项训练',
            '{course}论述题参考答案',
            '{course}计算题详解',
            '{course}名词解释汇总',
            '{course}期末考试A/B卷',
            '{course}小题狂练',
            '{course}综合测试题',
            '{course}答题技巧与真题精讲',
            '{course}辨析题专项突破',
        ],
        '复习提纲': [
            '{course}复习提纲',
            '{course}重点知识总结',
            '{course}思维导图',
            '{course}考点归纳整理',
            '{course}知识框架图',
            '{course}背诵口诀合集',
            '{course}易错点汇总',
            '{course}期末突击复习笔记',
            '{course}章节概要',
            '{course}公式定理速查表',
            '{course}知识点对比表',
            '{course}高频考点汇总',
            '{course}专题复习笔记',
        ],
        '课堂笔记': [
            '{course}课堂笔记',
            '{course}手写笔记扫描版',
            '{course}听课记录整理',
            '{course}随堂笔记',
            '{course}电子笔记',
            '{course}iPad手写笔记',
            '{course}详细标注版笔记',
            '{course}彩色笔记整理',
            '{course}学习心得笔记',
            '{course}打印版笔记',
        ],
        '教材': [
            '{course}教材电子版',
            '{course}参考书推荐清单',
            '{course}经典教材合集',
            '{course}指定教材PDF',
            '{course}原版教材影印本',
            '{course}教材习题解答',
            '{course}教材配套PPT',
            '{course}中文译本教材',
            '{course}辅助教材推荐',
        ],
        '习题集': [
            '{course}习题集',
            '{course}课后习题解答',
            '{course}作业参考答案',
            '{course}小题狂练',
            '{course}编程作业合集',
            '{course}上机实验题',
            '{course}课程设计题目',
            '{course}应用题专项练习',
            '{course}证明题选讲',
            '{course}选择题题库',
            '{course}填空题汇编',
            '{course}综合练习题集',
            '{course}计算题专项训练',
        ],
        '实验报告': [
            '{course}实验报告',
            '{course}实验指导书',
            '{course}实验数据处理',
            '{course}实验操作规范',
            '{course}实验报告模板',
            '{course}实验现象分析',
            '{course}实验步骤详解',
            '{course}实验记录整理',
        ],
        '历年真题': [
            '{course}历年真题合集',
            '{course}考研真题汇编',
            '{course}十年真题整理',
            '{course}真题答案与解析',
            '{course}真题分题型整理',
            '{course}最新真题回忆版',
            '{course}真题高频考点统计',
            '{course}真题原卷影印',
        ],
        '课件讲义': [
            '{course}课件PPT',
            '{course}完整版讲义',
            '{course}教学大纲',
            '{course}课堂板书整理',
            '{course}课程讲义PDF',
            '{course}幻灯片合集',
            '{course}教案讲义',
        ],
    }

    materials = []
    for subject, courses in courses_by_subject.items():
        for course in courses:
            for cat, tmpls in templates_by_category.items():
                # Not every course has every category — sample ~60%
                if rng.random() < 0.6:
                    tmpl = rng.choice(tmpls)
                    materials.append({
                        'title': tmpl.format(course=course),
                        'category': cat,
                        'subject': subject,
                    })

    rng.shuffle(materials)
    return materials


# ══════════════════════════════════════════════════════════════════════
# Evaluation metrics
# ══════════════════════════════════════════════════════════════════════

def evaluate(materials: list[dict], pool: dict, rng: random.Random, w_subject: int = W_SUBJECT) -> dict:
    results = []
    for m in materials:
        m['tokens'] = tokenize_multi_dim(m['title'], m['category'])
        filename, score, reason, detail = match_cover(m, pool, rng, w_subject=w_subject)
        results.append({**m, 'cover': filename, 'score': score, 'reason': reason, 'detail': detail})

    total = len(results)
    scored = [r for r in results if r['score'] > 0]
    zero_score = [r for r in results if r['score'] == 0]

    # Overall stats
    score_dist = Counter(int(r['score']) for r in results)
    avg_detail = {}
    if scored:
        avg_detail['cat_hits'] = sum(r['detail'].get('cat_hits', 0) for r in scored) / len(scored)
        avg_detail['sub_hits'] = sum(r['detail'].get('sub_hits', 0) for r in scored) / len(scored)
        avg_detail['fmt_hits'] = sum(r['detail'].get('fmt_hits', 0) for r in scored) / len(scored)
        avg_detail['vibe_hits'] = sum(r['detail'].get('vibe_hits', 0) for r in scored) / len(scored)

    # Per-category
    cat_stats = {}
    for cat in pool:
        cat_mats = [r for r in results if r['category'] == cat]
        cat_hits = [r for r in cat_mats if r['score'] > 0]
        # Subject differentiation: how many unique covers are used within this category?
        covers_used = Counter(r['cover'] for r in cat_mats)
        cat_stats[cat] = {
            'total': len(cat_mats),
            'hit': len(cat_hits),
            'rate': len(cat_hits) / len(cat_mats) if cat_mats else 0,
            'avg_score': sum(r['score'] for r in cat_mats) / len(cat_mats) if cat_mats else 0,
            'unique_covers': len(covers_used),
            'cover_distribution': dict(covers_used.most_common(5)),
        }

    # Per-subject
    sub_stats = {}
    subjects_in_data = set(m['subject'] for m in materials)
    for sub in sorted(subjects_in_data):
        sub_mats = [r for r in results if r.get('subject') == sub]
        sub_hits = [r for r in sub_mats if r['score'] > 0]
        # Check if subject-specific covers (has sub tags) are being selected
        subject_cover_hits = sum(
            1 for r in sub_hits
            if r['detail'].get('sub_hits', 0) > 0
        )
        sub_stats[sub] = {
            'total': len(sub_mats),
            'hit': len(sub_hits),
            'rate': len(sub_hits) / len(sub_mats) if sub_mats else 0,
            'avg_score': sum(r['score'] for r in sub_mats) / len(sub_mats) if sub_mats else 0,
            'subject_specific_cover': subject_cover_hits,
            'subject_specific_rate': subject_cover_hits / len(sub_hits) if sub_hits else 0,
        }

    # Subject differentiation within same category
    # For each category, check if materials from different subjects get DIFFERENT covers
    subject_diff = {}
    for cat in pool:
        cat_mats = [r for r in results if r['category'] == cat]
        subject_cover_map = defaultdict(set)
        for r in cat_mats:
            subj = r.get('subject', 'unknown')
            subject_cover_map[subj].add(r['cover'])
        # Differentiation score: how many subjects have at least 1 unique cover
        total_subjects = len(subject_cover_map)
        if total_subjects <= 1:
            subject_diff[cat] = {'score': 1.0, 'detail': 'only one subject'}
            continue
        all_covers = set()
        for covers in subject_cover_map.values():
            all_covers.update(covers)
        # Fraction of subject-pairs that don't share ALL covers
        diff_score = 0
        subjects_list = list(subject_cover_map.keys())
        pairs = 0
        for i in range(len(subjects_list)):
            for j in range(i+1, len(subjects_list)):
                pairs += 1
                if subject_cover_map[subjects_list[i]] != subject_cover_map[subjects_list[j]]:
                    diff_score += 1
        subject_diff[cat] = {
            'score': diff_score / pairs if pairs > 0 else 1.0,
            'subjects': len(subjects_list),
            'pairs': pairs,
        }

    return {
        'total': total,
        'match_rate': len(scored) / total if total else 0,
        'zero_score_count': len(zero_score),
        'avg_score': sum(r['score'] for r in results) / total if total else 0,
        'avg_weighted_score': sum(r['score'] for r in results) / total if total else 0,
        'max_score': max(r['score'] for r in results),
        'score_distribution': dict(sorted(score_dist.items())),
        'avg_detail': avg_detail,
        'per_category': cat_stats,
        'per_subject': sub_stats,
        'subject_differentiation': subject_diff,
        'zero_score_samples': [(r['title'], r['category'], r['subject']) for r in zero_score[:12]],
        'top_score_samples': [(r['title'], r['cover'], r['score'], r['detail']) for r in results if r['score'] >= 7][:10],
    }


POOL_CATEGORIES = list(COVER_POOL.keys())


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    rng = random.Random(42)
    materials = generate_materials(rng)

    # Count covers
    total_covers = sum(len(v) for v in COVER_POOL.values())
    subject_covers = sum(1 for items in COVER_POOL.values() for fn, tags in items if tags['sub'])
    generic_covers = total_covers - subject_covers

    print(f"{'='*76}")
    print(f"COVER MATCHING SIMULATION V2 — Four-dimension weighted tag matching")
    print(f"{'='*76}")
    print(f"Materials: {len(materials)}")
    print(f"Covers: {total_covers} ({subject_covers} subject-specific, {generic_covers} generic)")
    print(f"Weights: Category×{W_CATEGORY}  Subject×{W_SUBJECT}  Format×{W_FORMAT}  Vibe×{W_VIBE}")
    print()

    stats = evaluate(materials, COVER_POOL, rng)

    # ── Overall ────────────────────────────────────────────────────
    print(f"OVERALL MATCH QUALITY")
    print('-' * 76)
    print(f"  Match rate:   {stats['match_rate']:.1%} ({stats['total'] - stats['zero_score_count']}/{stats['total']} matched)")
    print(f"  Avg score:    {stats['avg_score']:.2f}  (max {stats['max_score']})")
    print(f"  Score dist:   {stats['score_distribution']}")
    if stats['avg_detail']:
        d = stats['avg_detail']
        print(f"  Avg hits:     cat={d['cat_hits']:.1f}  sub={d['sub_hits']:.1f}  fmt={d['fmt_hits']:.1f}  vibe={d['vibe_hits']:.1f}")

    # ── Per-category ───────────────────────────────────────────────
    print(f"\nPER-CATEGORY BREAKDOWN")
    print('-' * 76)
    header = f"{'Category':<10} {'Total':>5} {'Hit':>5} {'Rate':>7} {'AvgSc':>6} {'Covers':>6}  Top covers"
    print(header)
    print('-' * 76)
    for cat in stats['per_category']:
        cs = stats['per_category'][cat]
        top = ', '.join(f'{fn}({n})' for fn, n in cs['cover_distribution'].items())
        print(f"{cat:<10} {cs['total']:>5} {cs['hit']:>5} {cs['rate']:>6.0%} {cs['avg_score']:>6.1f} {cs['unique_covers']:>6}  {top}")

    # ── Subject differentiation ────────────────────────────────────
    print(f"\nSUBJECT DIFFERENTIATION (within same category)")
    print('-' * 76)
    header = f"{'Category':<10} {'Subjects':>8} {'Pairs':>6} {'DiffScore':>10}  Interpretation"
    print(header)
    print('-' * 76)
    for cat in stats['subject_differentiation']:
        sd = stats['subject_differentiation'][cat]
        bar = '█' * int(sd['score'] * 10) + '░' * (10 - int(sd['score'] * 10))
        print(f"{cat:<10} {sd['subjects']:>8} {sd['pairs']:>6} {sd['score']:>9.1%}  {bar}")
    print(f"  (1.0 = every subject gets unique cover, 0.0 = all subjects share same covers)")

    # ── Per-subject hit rate ───────────────────────────────────────
    print(f"\nPER-SUBJECT COVERAGE")
    print('-' * 76)
    header = f"{'Subject':<8} {'Mats':>5} {'Hit':>5} {'Rate':>7} {'AvgSc':>6} {'SubCover':>9} {'SubRate':>8}"
    print(header)
    print('-' * 76)
    for sub in stats['per_subject']:
        ss = stats['per_subject'][sub]
        marker = '✓' if ss['subject_specific_rate'] > 0.3 else '△' if ss['subject_specific_rate'] > 0 else '✗'
        print(f"{sub:<8} {ss['total']:>5} {ss['hit']:>5} {ss['rate']:>6.0%} {ss['avg_score']:>6.1f} {ss['subject_specific_cover']:>5}/{ss['hit']:>4} {ss['subject_specific_rate']:>7.0%}  {marker}")

    # ── Zero-score samples ─────────────────────────────────────────
    print(f"\nZERO-SCORE SAMPLES (random fallback):")
    for title, cat, subj in stats['zero_score_samples']:
        print(f"  ✗ [{subj}/{cat}] {title}")

    # ── Top matches ────────────────────────────────────────────────
    print(f"\nTOP MATCHES (score ≥ 7):")
    for title, cover, score, detail in stats['top_score_samples']:
        d = detail
        print(f"  ✓ [{score:.0f}] {title}")
        print(f"       → {cover}  (cat:{d['cat_hits']} sub:{d['sub_hits']} fmt:{d['fmt_hits']} vibe:{d['vibe_hits']})")

    # ── Determinism check ──────────────────────────────────────────
    print(f"\n{'='*76}")
    print(f"DETERMINISM CHECK")
    print(f"{'='*76}")
    test_mats = [
        {'title': materials[0]['title'], 'category': materials[0]['category']},
        {'title': materials[50]['title'], 'category': materials[50]['category']},
        {'title': materials[100]['title'], 'category': materials[100]['category']},
    ]
    for m in test_mats:
        m['tokens'] = tokenize_multi_dim(m['title'], m['category'])
        covers = set()
        for _ in range(100):
            f, _, _, _ = match_cover(m, COVER_POOL, rng)
            covers.add(f)
        det = 'DETERMINISTIC ✓' if len(covers) == 1 else f'NON-DETERMINISTIC ({len(covers)} covers) ✗'
        print(f"  '{m['title']}' → {det}")

    # ── Weight sensitivity ─────────────────────────────────────────
    print(f"\n{'='*76}")
    print(f"WEIGHT SENSITIVITY: Subject weight impact on differentiation")
    print(f"{'='*76}")
    print(f"{'Config':<30} {'MatchRate':>10} {'AvgScore':>10} {'SubDiff':>10}")
    print('-' * 76)

    for w_sub in [0, 1, 2, 3, 4]:
        s = evaluate(materials, COVER_POOL, rng, w_subject=w_sub)
        avg_sub_diff = sum(sd['score'] for sd in s['subject_differentiation'].values()) / len(s['subject_differentiation'])
        print(f"  Sub×{w_sub} (Cat×3, Fmt×1, Vibe×1)  {s['match_rate']:>9.1%} {s['avg_score']:>10.1f} {avg_sub_diff:>10.1%}")


if __name__ == '__main__':
    main()
