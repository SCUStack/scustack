"""Seed Sichuan University colleges into the database.

Usage: python -m scripts.seed_colleges
"""
import asyncio
from app.core.database import async_session
from app.models.college import College

COLLEGES = [
    ("经济学院", "jingji-xueyuan", 1),
    ("法学院", "fayuan", 2),
    ("文学与新闻学院", "wenxue-xinwen", 3),
    ("外国语学院", "waiguoyu", 4),
    ("艺术学院", "yishu", 5),
    ("历史文化学院（旅游学院）", "lishi-wenhua", 6),
    ("哲学系", "zhexue", 7),
    ("马克思主义学院", "makesizhuyi", 8),
    ("体育学院", "tiyu", 9),
    ("公共管理学院", "gonggong-guanli", 10),
    ("商学院", "shangxueyuan", 11),
    ("数学学院", "shuxue", 12),
    ("物理学院", "wuli", 13),
    ("化学学院", "huaxue", 14),
    ("生命科学学院", "shengming-kexue", 15),
    ("电子信息学院", "dianzi-xinxi", 16),
    ("材料科学与工程学院", "cailiao-kexue", 17),
    ("机械工程学院", "jixie", 18),
    ("电气工程学院", "dianqi", 19),
    ("计算机学院", "jisuanji", 20),
    ("建筑与环境学院", "jianzhu-huanjing", 21),
    ("水利水电学院", "shuili-shuidian", 22),
    ("化学工程学院", "huagong", 23),
    ("轻工科学与工程学院", "qinggong-kexue", 24),
    ("高分子科学与工程学院", "gaofenzi-kexue", 25),
    ("空天科学与工程学院", "kongtian-kexue", 26),
    ("网络空间安全学院", "wangluo-anquan", 27),
    ("生物医学工程学院", "shengwu-yixue-gongcheng", 28),
    ("碳中和未来技术学院", "tan-zhonghe", 29),
    ("华西基础医学与法医学院", "huaxi-jichu-yixue", 30),
    ("华西临床医学院（华西医院）", "huaxi-linchuang", 31),
    ("华西口腔医学院", "huaxi-kouqiang", 32),
    ("华西公共卫生学院", "huaxi-gonggong-weisheng", 33),
    ("华西药学院", "huaxi-yaoxue", 34),
    ("国际关系学院", "guoji-guanxi", 35),
    ("匹兹堡学院", "pizibao", 36),
    ("灾后重建与管理学院", "zaihou-chongjian", 37),
    ("海外教育学院", "haiwai-jiaoyu", 38),
    ("成人继续教育学院", "chengren-jixu", 39),
]


async def seed():
    async with async_session() as db:
        for name, slug, order in COLLEGES:
            db.add(College(name=name, slug=slug, sort_order=order))
        await db.commit()
    print(f"Seeded {len(COLLEGES)} colleges")


if __name__ == '__main__':
    asyncio.run(seed())
