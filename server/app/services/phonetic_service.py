"""音标学习 service（DJ 音标体系 48 个）"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AppUser, PhoneticLesson, PhoneticProgress, gen_id
from app.schemas import PhoneticLessonCreate, PhoneticLessonOut, PhoneticProgressOut
from app.timezone import now

# DJ 音标 48 个：20 元音 + 28 辅音
# unit_vowel=单元音(12) diphthong=双元音(8) consonant=辅音(28)
DJ_PHONETICS: list[dict] = [
    # === 单元音 12 个 ===
    {"symbol": "/iː/", "category": "unit_vowel", "description": "长元音，嘴唇微微张开，舌尖抵下齿，嘴角向两边张开", "mouth_shape": "嘴角向两边拉开，如同微笑", "tips": "类似中文「衣」的音，但更长更紧", "example_words": [{"word": "see", "meaning": "看见"}, {"word": "tree", "meaning": "树"}, {"word": "green", "meaning": "绿色的"}], "common_spellings": ["ee", "ea", "e", "ei"], "sort_order": 1},
    {"symbol": "/ɪ/", "category": "unit_vowel", "description": "短元音，嘴唇微张，舌尖抵下齿", "mouth_shape": "嘴角略松，比/iː/放松", "tips": "类似/iː/但短促放松", "example_words": [{"word": "sit", "meaning": "坐"}, {"word": "big", "meaning": "大的"}, {"word": "fish", "meaning": "鱼"}], "common_spellings": ["i", "y", "e"], "sort_order": 2},
    {"symbol": "/e/", "category": "unit_vowel", "description": "短元音，嘴唇微张，舌尖抵下齿", "mouth_shape": "口型中等，比/ɪ/稍大", "tips": "类似中文「诶」的短音", "example_words": [{"word": "bed", "meaning": "床"}, {"word": "red", "meaning": "红色"}, {"word": "pen", "meaning": "钢笔"}], "common_spellings": ["e", "ea"], "sort_order": 3},
    {"symbol": "/æ/", "category": "unit_vowel", "description": "短元音，嘴巴张大，舌尖抵下齿", "mouth_shape": "嘴巴张大，嘴角向两边", "tips": "介于/e/和/ɑː/之间，口型较大", "example_words": [{"word": "cat", "meaning": "猫"}, {"word": "map", "meaning": "地图"}, {"word": "bad", "meaning": "坏的"}], "common_spellings": ["a"], "sort_order": 4},
    {"symbol": "/ɜː/", "category": "unit_vowel", "description": "长元音，嘴唇微张，舌身平放", "mouth_shape": "嘴唇自然放松，口型中等", "tips": "类似中文「饿」的长音", "example_words": [{"word": "bird", "meaning": "鸟"}, {"word": "word", "meaning": "单词"}, {"word": "her", "meaning": "她的"}], "common_spellings": ["ir", "er", "ur", "ear"], "sort_order": 5},
    {"symbol": "/ə/", "category": "unit_vowel", "description": "短元音（schwa），最常见的英语元音", "mouth_shape": "嘴唇完全放松，口型最小", "tips": "所有元音弱化后都变成/ə/，极轻极短", "example_words": [{"word": "about", "meaning": "关于"}, {"word": "sofa", "meaning": "沙发"}, {"word": "teacher", "meaning": "老师"}], "common_spellings": ["a", "e", "o", "u"], "sort_order": 6},
    {"symbol": "/ʌ/", "category": "unit_vowel", "description": "短元音，嘴巴微张，舌身放松", "mouth_shape": "嘴巴微张，比/ə/稍大", "tips": "类似/ə/但更用力", "example_words": [{"word": "cup", "meaning": "杯子"}, {"word": "bus", "meaning": "公交"}, {"word": "love", "meaning": "爱"}], "common_spellings": ["u", "o", "ou"], "sort_order": 7},
    {"symbol": "/uː/", "category": "unit_vowel", "description": "长元音，嘴唇收圆突出", "mouth_shape": "嘴唇收圆突出，口型小", "tips": "类似中文「乌」但更长", "example_words": [{"word": "food", "meaning": "食物"}, {"word": "blue", "meaning": "蓝色"}, {"word": "moon", "meaning": "月亮"}], "common_spellings": ["oo", "u", "ue", "ew"], "sort_order": 8},
    {"symbol": "/ʊ/", "category": "unit_vowel", "description": "短元音，嘴唇微圆", "mouth_shape": "嘴唇微圆，比/uː/放松", "tips": "类似/uː/但短促放松", "example_words": [{"word": "book", "meaning": "书"}, {"word": "good", "meaning": "好的"}, {"word": "put", "meaning": "放"}], "common_spellings": ["oo", "u"], "sort_order": 9},
    {"symbol": "/ɔː/", "category": "unit_vowel", "description": "长元音，嘴唇收圆突出", "mouth_shape": "嘴唇收圆，口型比/uː/大", "tips": "类似中文「奥」的长音", "example_words": [{"word": "door", "meaning": "门"}, {"word": "four", "meaning": "四"}, {"word": "law", "meaning": "法律"}], "common_spellings": ["or", "aw", "au", "ar"], "sort_order": 10},
    {"symbol": "/ɒ/", "category": "unit_vowel", "description": "短元音，嘴巴张大圆唇", "mouth_shape": "嘴巴张大，嘴唇收圆", "tips": "类似/ɔː/但短促", "example_words": [{"word": "hot", "meaning": "热的"}, {"word": "box", "meaning": "盒子"}, {"word": "dog", "meaning": "狗"}], "common_spellings": ["o", "a"], "sort_order": 11},
    {"symbol": "/ɑː/", "category": "unit_vowel", "description": "长元音，嘴巴张大", "mouth_shape": "嘴巴张大，舌身放低", "tips": "类似中文「啊」的长音", "example_words": [{"word": "car", "meaning": "汽车"}, {"word": "far", "meaning": "远"}, {"word": "arm", "meaning": "手臂"}], "common_spellings": ["ar", "a", "al"], "sort_order": 12},
    # === 双元音 8 个 ===
    {"symbol": "/eɪ/", "category": "diphthong", "description": "由/e/滑向/ɪ/", "mouth_shape": "从半张嘴滑向微笑", "tips": "类似中文「诶」的音", "example_words": [{"word": "day", "meaning": "天"}, {"word": "name", "meaning": "名字"}, {"word": "cake", "meaning": "蛋糕"}], "common_spellings": ["a-e", "ay", "ai", "ei"], "sort_order": 13},
    {"symbol": "/aɪ/", "category": "diphthong", "description": "由/ɑː/滑向/ɪ/", "mouth_shape": "从大嘴滑向微笑", "tips": "类似中文「爱」的音", "example_words": [{"word": "my", "meaning": "我的"}, {"word": "time", "meaning": "时间"}, {"word": "bike", "meaning": "自行车"}], "common_spellings": ["i-e", "y", "igh", "ie"], "sort_order": 14},
    {"symbol": "/ɔɪ/", "category": "diphthong", "description": "由/ɒ/滑向/ɪ/", "mouth_shape": "从圆嘴滑向微笑", "tips": "类似中文「哦衣」的音", "example_words": [{"word": "boy", "meaning": "男孩"}, {"word": "toy", "meaning": "玩具"}, {"word": "enjoy", "meaning": "享受"}], "common_spellings": ["oy", "oi"], "sort_order": 15},
    {"symbol": "/aʊ/", "category": "diphthong", "description": "由/ɑː/滑向/ʊ/", "mouth_shape": "从大嘴滑向圆嘴", "tips": "类似中文「奥」的音", "example_words": [{"word": "now", "meaning": "现在"}, {"word": "house", "meaning": "房子"}, {"word": "cow", "meaning": "牛"}], "common_spellings": ["ou", "ow"], "sort_order": 16},
    {"symbol": "/əʊ/", "category": "diphthong", "description": "由/ə/滑向/ʊ/", "mouth_shape": "从放松嘴滑向圆嘴", "tips": "类似中文「欧」的音", "example_words": [{"word": "go", "meaning": "去"}, {"word": "home", "meaning": "家"}, {"word": "nose", "meaning": "鼻子"}], "common_spellings": ["o", "o-e", "oa", "ow"], "sort_order": 17},
    {"symbol": "/ɪə/", "category": "diphthong", "description": "由/ɪ/滑向/ə/", "mouth_shape": "从微笑滑向放松", "tips": "类似中文「衣饿」的音", "example_words": [{"word": "here", "meaning": "这里"}, {"word": "near", "meaning": "近"}, {"word": "ear", "meaning": "耳朵"}], "common_spellings": ["eer", "ere", "ear", "ier"], "sort_order": 18},
    {"symbol": "/eə/", "category": "diphthong", "description": "由/e/滑向/ə/", "mouth_shape": "从半张滑向放松", "tips": "类似中文「诶饿」的音", "example_words": [{"word": "air", "meaning": "空气"}, {"word": "care", "meaning": "关心"}, {"word": "hair", "meaning": "头发"}], "common_spellings": ["air", "are", "ear", "eir"], "sort_order": 19},
    {"symbol": "/ʊə/", "category": "diphthong", "description": "由/ʊ/滑向/ə/", "mouth_shape": "从圆嘴滑向放松", "tips": "类似中文「乌饿」的音", "example_words": [{"word": "tour", "meaning": "旅行"}, {"word": "pure", "meaning": "纯净"}, {"word": "sure", "meaning": "确定"}], "common_spellings": ["oor", "ure", "our"], "sort_order": 20},
    # === 辅音 28 个 ===
    {"symbol": "/p/", "category": "consonant", "description": "清辅音，双唇紧闭后突然打开", "mouth_shape": "双唇紧闭，气流冲开", "tips": "送气，类似中文「波」的声母", "example_words": [{"word": "pen", "meaning": "钢笔"}, {"word": "apple", "meaning": "苹果"}, {"word": "stop", "meaning": "停"}], "common_spellings": ["p", "pp"], "sort_order": 21},
    {"symbol": "/b/", "category": "consonant", "description": "浊辅音，双唇紧闭后突然打开", "mouth_shape": "双唇紧闭，气流冲开", "tips": "不送气，声带振动", "example_words": [{"word": "book", "meaning": "书"}, {"word": "table", "meaning": "桌子"}, {"word": "cab", "meaning": "出租车"}], "common_spellings": ["b", "bb"], "sort_order": 22},
    {"symbol": "/t/", "category": "consonant", "description": "清辅音，舌尖抵上齿龈后突然离开", "mouth_shape": "舌尖抵上齿龈", "tips": "送气，类似中文「得」的声母", "example_words": [{"word": "ten", "meaning": "十"}, {"word": "water", "meaning": "水"}, {"word": "cat", "meaning": "猫"}], "common_spellings": ["t", "tt"], "sort_order": 23},
    {"symbol": "/d/", "category": "consonant", "description": "浊辅音，舌尖抵上齿龈后突然离开", "mouth_shape": "舌尖抵上齿龈", "tips": "不送气，声带振动", "example_words": [{"word": "dog", "meaning": "狗"}, {"word": "bed", "meaning": "床"}, {"word": "day", "meaning": "天"}], "common_spellings": ["d", "dd"], "sort_order": 24},
    {"symbol": "/k/", "category": "consonant", "description": "清辅音，舌后部抵软腭后突然离开", "mouth_shape": "舌后部抵软腭", "tips": "送气，类似中文「克」的声母", "example_words": [{"word": "key", "meaning": "钥匙"}, {"word": "school", "meaning": "学校"}, {"word": "cake", "meaning": "蛋糕"}], "common_spellings": ["k", "c", "ck", "ch"], "sort_order": 25},
    {"symbol": "/ɡ/", "category": "consonant", "description": "浊辅音，舌后部抵软腭后突然离开", "mouth_shape": "舌后部抵软腭", "tips": "不送气，声带振动", "example_words": [{"word": "go", "meaning": "去"}, {"word": "big", "meaning": "大的"}, {"word": "girl", "meaning": "女孩"}], "common_spellings": ["g", "gg"], "sort_order": 26},
    {"symbol": "/f/", "category": "consonant", "description": "清辅音，上齿咬下唇", "mouth_shape": "上齿轻咬下唇", "tips": "气流从唇齿间摩擦", "example_words": [{"word": "fish", "meaning": "鱼"}, {"word": "five", "meaning": "五"}, {"word": "coffee", "meaning": "咖啡"}], "common_spellings": ["f", "ff", "ph", "gh"], "sort_order": 27},
    {"symbol": "/v/", "category": "consonant", "description": "浊辅音，上齿咬下唇", "mouth_shape": "上齿轻咬下唇", "tips": "气流摩擦，声带振动", "example_words": [{"word": "very", "meaning": "非常"}, {"word": "love", "meaning": "爱"}, {"word": "five", "meaning": "五"}], "common_spellings": ["v", "ve"], "sort_order": 28},
    {"symbol": "/θ/", "category": "consonant", "description": "清辅音，舌尖伸出上下齿之间", "mouth_shape": "舌尖伸出齿间", "tips": "咬舌音，气流从舌齿间摩擦", "example_words": [{"word": "think", "meaning": "思考"}, {"word": "three", "meaning": "三"}, {"word": "bath", "meaning": "洗澡"}], "common_spellings": ["th"], "sort_order": 29},
    {"symbol": "/ð/", "category": "consonant", "description": "浊辅音，舌尖伸出上下齿之间", "mouth_shape": "舌尖伸出齿间", "tips": "咬舌音，声带振动", "example_words": [{"word": "this", "meaning": "这个"}, {"word": "the", "meaning": "定冠词"}, {"word": "mother", "meaning": "母亲"}], "common_spellings": ["th"], "sort_order": 30},
    {"symbol": "/s/", "category": "consonant", "description": "清辅音，舌尖接近上齿龈", "mouth_shape": "舌近上齿龈，气流摩擦", "tips": "类似中文「斯」的音", "example_words": [{"word": "sun", "meaning": "太阳"}, {"word": "bus", "meaning": "公交"}, {"word": "city", "meaning": "城市"}], "common_spellings": ["s", "c", "ss", "ce"], "sort_order": 31},
    {"symbol": "/z/", "category": "consonant", "description": "浊辅音，舌尖接近上齿龈", "mouth_shape": "舌近上齿龈，气流摩擦", "tips": "声带振动", "example_words": [{"word": "zoo", "meaning": "动物园"}, {"word": "is", "meaning": "是"}, {"word": "nose", "meaning": "鼻子"}], "common_spellings": ["z", "s", "zz"], "sort_order": 32},
    {"symbol": "/ʃ/", "category": "consonant", "description": "清辅音，舌前部抬向硬腭", "mouth_shape": "嘴唇微突，舌抬向硬腭", "tips": "类似中文「嘘」的音", "example_words": [{"word": "she", "meaning": "她"}, {"word": "fish", "meaning": "鱼"}, {"word": "sugar", "meaning": "糖"}], "common_spellings": ["sh", "ti", "ci", "si"], "sort_order": 33},
    {"symbol": "/ʒ/", "category": "consonant", "description": "浊辅音，舌前部抬向硬腭", "mouth_shape": "嘴唇微突，舌抬向硬腭", "tips": "声带振动，较少见", "example_words": [{"word": "measure", "meaning": "测量"}, {"word": "vision", "meaning": "视力"}, {"word": "garage", "meaning": "车库"}], "common_spellings": ["si", "ge", "g"], "sort_order": 34},
    {"symbol": "/h/", "category": "consonant", "description": "清辅音，气流从声门摩擦而出", "mouth_shape": "口自然张开", "tips": "类似中文「喝」的轻音", "example_words": [{"word": "hat", "meaning": "帽子"}, {"word": "house", "meaning": "房子"}, {"word": "happy", "meaning": "快乐"}], "common_spellings": ["h"], "sort_order": 35},
    {"symbol": "/tʃ/", "category": "consonant", "description": "清辅音，/t/和/ʃ/的结合", "mouth_shape": "嘴唇微突", "tips": "类似中文「吃」的音", "example_words": [{"word": "chair", "meaning": "椅子"}, {"word": "watch", "meaning": "手表"}, {"word": "teacher", "meaning": "老师"}], "common_spellings": ["ch", "tch"], "sort_order": 36},
    {"symbol": "/dʒ/", "category": "consonant", "description": "浊辅音，/d/和/ʒ/的结合", "mouth_shape": "嘴唇微突", "tips": "声带振动，类似中文「知」的音", "example_words": [{"word": "jump", "meaning": "跳"}, {"word": "orange", "meaning": "橙子"}, {"word": "bridge", "meaning": "桥"}], "common_spellings": ["j", "g", "dge", "ge"], "sort_order": 37},
    {"symbol": "/m/", "category": "consonant", "description": "浊辅音，双唇紧闭", "mouth_shape": "双唇紧闭，气流从鼻腔出", "tips": "类似中文「摸」的声母", "example_words": [{"word": "man", "meaning": "男人"}, {"word": "time", "meaning": "时间"}, {"word": "name", "meaning": "名字"}], "common_spellings": ["m", "mm"], "sort_order": 38},
    {"symbol": "/n/", "category": "consonant", "description": "浊辅音，舌尖抵上齿龈", "mouth_shape": "舌尖抵上齿龈，气流从鼻腔出", "tips": "类似中文「呢」的声母", "example_words": [{"word": "no", "meaning": "不"}, {"word": "sun", "meaning": "太阳"}, {"word": "run", "meaning": "跑"}], "common_spellings": ["n", "nn", "kn"], "sort_order": 39},
    {"symbol": "/ŋ/", "category": "consonant", "description": "浊辅音，舌后部抵软腭", "mouth_shape": "舌后抵软腭，气流从鼻腔出", "tips": "类似中文「嗯」的鼻音", "example_words": [{"word": "sing", "meaning": "唱歌"}, {"word": "thing", "meaning": "事情"}, {"word": "long", "meaning": "长"}], "common_spellings": ["ng", "n"], "sort_order": 40},
    {"symbol": "/l/", "category": "consonant", "description": "浊辅音，舌尖抵上齿龈", "mouth_shape": "舌尖抵上齿龈，气流从舌两侧出", "tips": "类似中文「勒」的声母", "example_words": [{"word": "look", "meaning": "看"}, {"word": "play", "meaning": "玩"}, {"word": "tall", "meaning": "高"}], "common_spellings": ["l", "ll"], "sort_order": 41},
    {"symbol": "/r/", "category": "consonant", "description": "浊辅音，舌尖卷起不触及上腭", "mouth_shape": "舌尖卷起，嘴唇微突", "tips": "类似中文「日」但更轻", "example_words": [{"word": "red", "meaning": "红色"}, {"word": "very", "meaning": "非常"}, {"word": "right", "meaning": "对"}], "common_spellings": ["r", "rr", "wr"], "sort_order": 42},
    {"symbol": "/j/", "category": "consonant", "description": "浊辅音，舌前部抬向硬腭", "mouth_shape": "舌抬向硬腭，嘴角微展", "tips": "类似中文「耶」的音", "example_words": [{"word": "yes", "meaning": "是"}, {"word": "you", "meaning": "你"}, {"word": "yellow", "meaning": "黄色"}], "common_spellings": ["y", "i", "u"], "sort_order": 43},
    {"symbol": "/w/", "category": "consonant", "description": "浊辅音，双唇收圆", "mouth_shape": "双唇收圆突出", "tips": "类似中文「乌」的短音", "example_words": [{"word": "we", "meaning": "我们"}, {"word": "water", "meaning": "水"}, {"word": "window", "meaning": "窗户"}], "common_spellings": ["w", "wh"], "sort_order": 44},
    {"symbol": "/ts/", "category": "consonant", "description": "清辅音，/t/和/s/的结合", "mouth_shape": "舌尖抵上齿龈后滑开", "tips": "类似中文「次」的音", "example_words": [{"word": "cats", "meaning": "猫(复数)"}, {"word": "bits", "meaning": "碎片"}, {"word": "sports", "meaning": "运动"}], "common_spellings": ["ts"], "sort_order": 45},
    {"symbol": "/dz/", "category": "consonant", "description": "浊辅音，/d/和/z/的结合", "mouth_shape": "舌尖抵上齿龈后滑开", "tips": "类似中文「滋」的音", "example_words": [{"word": "beds", "meaning": "床(复数)"}, {"word": "words", "meaning": "单词(复数)"}, {"word": "friends", "meaning": "朋友(复数)"}], "common_spellings": ["ds"], "sort_order": 46},
    {"symbol": "/tr/", "category": "consonant", "description": "清辅音，/t/和/r/的结合", "mouth_shape": "舌尖抵上齿龈后卷起", "tips": "类似中文「戳」的音", "example_words": [{"word": "tree", "meaning": "树"}, {"word": "train", "meaning": "火车"}, {"word": "try", "meaning": "尝试"}], "common_spellings": ["tr"], "sort_order": 47},
    {"symbol": "/dr/", "category": "consonant", "description": "浊辅音，/d/和/r/的结合", "mouth_shape": "舌尖抵上齿龈后卷起", "tips": "类似中文「桌」的音", "example_words": [{"word": "drink", "meaning": "喝"}, {"word": "drive", "meaning": "驾驶"}, {"word": "dream", "meaning": "梦想"}], "common_spellings": ["dr"], "sort_order": 48},
]


def _safe_json(s: str | None, default: Any) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


def _lesson_to_out(p: PhoneticLesson) -> PhoneticLessonOut:
    return PhoneticLessonOut(
        id=p.id,
        symbol=p.symbol,
        category=p.category,
        description=p.description or "",
        mouthShape=p.mouth_shape or "",
        tips=p.tips or "",
        exampleWords=_safe_json(p.example_words, []),
        commonSpellings=_safe_json(p.common_spellings, []),
        sortOrder=p.sort_order,
        isPublished=bool(p.is_published),
    )


def seed_default_phonetics(db: Session) -> None:
    """首次启动时写入 48 个 DJ 音标"""
    exists = db.query(PhoneticLesson).first()
    if exists:
        return
    for item in DJ_PHONETICS:
        db.add(
            PhoneticLesson(
                id=gen_id("ph"),
                symbol=item["symbol"],
                category=item["category"],
                description=item["description"],
                mouth_shape=item["mouth_shape"],
                tips=item["tips"],
                example_words=json.dumps(item["example_words"], ensure_ascii=False),
                common_spellings=json.dumps(item["common_spellings"], ensure_ascii=False),
                sort_order=item["sort_order"],
                is_published=True,
            )
        )
    db.commit()


def list_phonetics(db: Session, category: str | None = None) -> list[PhoneticLessonOut]:
    q = db.query(PhoneticLesson).filter(PhoneticLesson.is_published.is_(True))
    if category:
        q = q.filter(PhoneticLesson.category == category)
    rows = q.order_by(PhoneticLesson.sort_order).all()
    return [_lesson_to_out(p) for p in rows]


def get_phonetic(db: Session, lesson_id: str) -> PhoneticLessonOut | None:
    p = db.get(PhoneticLesson, lesson_id)
    return _lesson_to_out(p) if p else None


def create_phonetic(db: Session, body: PhoneticLessonCreate) -> PhoneticLessonOut:
    p = PhoneticLesson(
        id=gen_id("ph"),
        symbol=body.symbol,
        category=body.category,
        description=body.description,
        mouth_shape=body.mouthShape,
        tips=body.tips,
        example_words=json.dumps(body.exampleWords, ensure_ascii=False),
        common_spellings=json.dumps(body.commonSpellings, ensure_ascii=False),
        sort_order=body.sortOrder,
        is_published=body.isPublished,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _lesson_to_out(p)


def update_phonetic(db: Session, lesson_id: str, body: dict) -> PhoneticLessonOut | None:
    p = db.get(PhoneticLesson, lesson_id)
    if not p:
        return None
    for k, v in body.items():
        key = {"mouthShape": "mouth_shape", "exampleWords": "example_words", "commonSpellings": "common_spellings", "sortOrder": "sort_order", "isPublished": "is_published"}.get(k, k)
        if key in ("example_words", "common_spellings"):
            setattr(p, key, json.dumps(v, ensure_ascii=False))
        else:
            setattr(p, key, v)
    db.commit()
    db.refresh(p)
    return _lesson_to_out(p)


def delete_phonetic(db: Session, lesson_id: str) -> bool:
    p = db.get(PhoneticLesson, lesson_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True


def get_phonetic_progress(db: Session, user: AppUser) -> dict:
    rows = db.query(PhoneticProgress).filter(PhoneticProgress.user_id == user.id).all()
    return {r.lesson_id: {"status": r.status, "practicedCount": r.practiced_count, "lastPracticeAt": r.last_practice_at} for r in rows}


def update_phonetic_progress(db: Session, user: AppUser, lesson_id: str, status: str) -> dict:
    r = (
        db.query(PhoneticProgress)
        .filter(PhoneticProgress.user_id == user.id, PhoneticProgress.lesson_id == lesson_id)
        .first()
    )
    if r:
        r.status = status
        r.practiced_count += 1
        r.last_practice_at = now().replace(tzinfo=None)
    else:
        r = PhoneticProgress(
            id=gen_id("php"),
            user_id=user.id,
            lesson_id=lesson_id,
            status=status,
            practiced_count=1,
            last_practice_at=now().replace(tzinfo=None),
        )
        db.add(r)
    db.commit()
    return {"lessonId": lesson_id, "status": status, "practicedCount": r.practiced_count}
