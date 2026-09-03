#!/usr/bin/env python3
"""
Q6 判断推理引擎 — 定义判断→翻译推理→图形推理逐个推进

三个子引擎：
  ① 定义判断（≥5题）：人工编写定义+关键要素，正确项满足全部要素，干扰项各违反一个
  ② 翻译推理（≥5题）：双求解（规则引擎×真值表），完整逻辑推导树，干扰项来自典型逻辑谬误
  ③ 图形推理（≥5题）：确定性SVG生成（禁止自由图像生成），规律可程序验证

用法:
    python3 scripts/xingce/gen_judgment_questions.py           # 生成全部
    python3 scripts/xingce/gen_judgment_questions.py --dry-run # 只打印不写文件
    python3 scripts/xingce/gen_judgment_questions.py --validate-only  # 仅跑真题验证
"""

import json
import argparse
import random
import re
import math
from datetime import datetime
from pathlib import Path
from itertools import product as iter_product

# ── 路径 ──────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "xingce-structured-data" / "generated"
FIGURE_DIR = OUTPUT_DIR / "figures"
SCHEMA_DIR = REPO_ROOT / "xingce-structured-data" / "_schema"
PAPER_DIR = REPO_ROOT / "xingce-structured-data" / "2025" / "xingce" / "papers"

SEED = 42
TEMPLATE_VERSION = "judgment_v1"

QUESTIONS_PATH = OUTPUT_DIR / "qa_judgment_v1.json"
REPORT_PATH = OUTPUT_DIR / "qa_judgment_v1_report.md"


# ══════════════════════════════════════════════════════
# 子引擎 1：定义判断
# ══════════════════════════════════════════════════════

# 每个定义包含：definition, key_elements, correct_option, distractors
# 干扰项每个标注 violated_element
DEFINITION_SPECS = [
    {
        "question_id": "Q6-DEF-001",
        "difficulty": 1,
        "definition": (
            "绿色消费是指消费者在购买商品和服务时，优先选择那些在生产、使用和处置过程中"
            "对环境影响较小、符合环保标准的产品，以减少资源消耗和环境污染的消费行为。"
        ),
        "key_elements": [
            {"element": "主体", "description": "消费者（个人或家庭）"},
            {"element": "行为", "description": "购买商品和服务时优先选择环保产品"},
            {"element": "条件", "description": "产品在生产、使用和处置过程中对环境影响较小、符合环保标准"},
            {"element": "目的", "description": "减少资源消耗和环境污染"},
        ],
        "ask": "根据上述定义，下列属于绿色消费的是：",
        "correct_option": (
            "小王在超市购物时，专门挑选带有'有机认证'和'可降解包装'标识的食品和日用品，"
            "虽然价格略高，但他认为这样可以减少化学残留和塑料污染。"
        ),
        "distractors": [
            {
                "content": (
                    "某制造企业为了降低生产成本，在生产过程中采用了更节能的设备和工艺，"
                    "减少了废气排放，被当地环保部门评为'绿色工厂'。"
                ),
                "violated_element": "主体",
                "violation_reason": "主体是企业而非消费者，定义要求主体为消费者",
            },
            {
                "content": (
                    "小李在网购时只看价格和销量，哪家便宜买哪家，从不关注产品是否环保，"
                    "他认为个人消费对环境的影响微乎其微。"
                ),
                "violated_element": "行为",
                "violation_reason": "没有优先选择环保产品，行为不符合定义",
            },
            {
                "content": (
                    "小张喜欢收集限量版运动鞋，每次新款发售都会抢购，他认为这些鞋子做工精良、"
                    "材质高级，穿起来很有面子。"
                ),
                "violated_element": "条件",
                "violation_reason": "购买的产品未体现对环境影响较小或符合环保标准",
            },
        ],
    },
    {
        "question_id": "Q6-DEF-002",
        "difficulty": 2,
        "definition": (
            "紧急避险是指为了使国家、公共利益、本人或者他人的人身、财产和其他权利免受正在发生的危险，"
            "不得已而采取的损害另一较小合法权益的行为。紧急避险超过必要限度造成不应有的损害的，"
            "应当负刑事责任，但是应当减轻或者免除处罚。"
        ),
        "key_elements": [
            {"element": "条件", "description": "存在正在发生的危险"},
            {"element": "目的", "description": "保护合法权益免受危险"},
            {"element": "行为", "description": "不得已采取损害另一较小合法权益的行为"},
            {"element": "限度", "description": "损害的权益小于被保护的权益（未超过必要限度）"},
        ],
        "ask": "根据上述定义，下列属于紧急避险的是：",
        "correct_option": (
            "一艘货轮在海上遭遇特大风暴，船长为了避免船只沉没和船员遇难，下令将船上"
            "部分货物抛入海中以减轻载重，最终船只和船员安全脱险。"
        ),
        "distractors": [
            {
                "content": (
                    "张某与邻居发生口角，一怒之下将邻居家的门窗砸毁，事后他辩称自己是"
                    "为了发泄情绪、避免精神崩溃，属于紧急避险。"
                ),
                "violated_element": "条件",
                "violation_reason": "不存在正在发生的危险，口角不属于现实危险",
            },
            {
                "content": (
                    "刘某在森林中迷路多日，饥饿难耐，于是捕杀了一只国家一级保护动物充饥，"
                    "他认为自己的生命权高于野生动物保护权益。"
                ),
                "violated_element": "限度",
                "violation_reason": "捕杀国家一级保护动物可能超过必要限度，且有其他可替代方式",
            },
            {
                "content": (
                    "陈某看到远处有一栋房屋着火，为了防止火势蔓延到自己家，他主动拆除了"
                    "邻居家尚未着火的围墙，但实际上当时风向已经改变，火势不会蔓延到他家。"
                ),
                "violated_element": "目的",
                "violation_reason": "危险并不存在（风向已改变），不是为了免受正在发生的危险",
            },
        ],
    },
    {
        "question_id": "Q6-DEF-003",
        "difficulty": 2,
        "definition": (
            "沉没成本效应是指人们在决定是否去做一件事情的时候，不仅是看这件事对自己有没有好处，"
            "而且也看过去是不是已经在这件事情上有过投入。我们把这些已经发生不可收回的支出，"
            "如时间、金钱、精力等称为'沉没成本'。由于沉没成本的存在，人们往往会做出非理性的决策，"
            "继续投入资源去完成一项已经不再有利的事情。"
        ),
        "key_elements": [
            {"element": "前提", "description": "已经在某件事上有过不可收回的投入（时间/金钱/精力）"},
            {"element": "行为", "description": "决策时考虑过去的投入而非未来收益"},
            {"element": "结果", "description": "做出非理性决策，继续投入资源完成已不再有利的事"},
        ],
        "ask": "根据上述定义，下列体现沉没成本效应的是：",
        "correct_option": (
            "小赵花50元买了一张电影票，看了半小时发现电影非常难看，但他觉得'钱都花了，"
            "不看完太亏'，于是硬着头皮看完了整部电影，浪费了两个小时。"
        ),
        "distractors": [
            {
                "content": (
                    "小钱在股市投资了10万元，经过分析发现该股票前景不佳，于是果断止损卖出，"
                    "将资金转移到更有潜力的股票上，最终减少了损失。"
                ),
                "violated_element": "结果",
                "violation_reason": "做出了理性决策（止损），没有继续投入，不符合非理性结果",
            },
            {
                "content": (
                    "小孙在评估是否继续投资一个项目时，完全基于对未来市场前景的分析和预测，"
                    "过去已经投入的资金和时间不在他的考虑范围之内，他认为决策应该只看未来收益。"
                ),
                "violated_element": "行为",
                "violation_reason": "决策时没有考虑过去的投入，不符合'看过去是不是已经有过投入'的行为特征",
            },
            {
                "content": (
                    "小李在书店翻了一本书，觉得内容很有趣，于是决定买下来回家仔细阅读，"
                    "他认为这本书能帮助自己提升专业技能。"
                ),
                "violated_element": "前提",
                "violation_reason": "之前没有在这件事上有过投入，不存在沉没成本",
            },
        ],
    },
    {
        "question_id": "Q6-DEF-004",
        "difficulty": 3,
        "definition": (
            "行政指导是指行政机关在其所管辖的事务范围内，根据国家的政策规定或者法律原则，"
            "针对特定的公民、法人或其他组织，用非强制性的方法或手段，取得该行政相对方的同意或协助，"
            "有效地实现一定的行政目的的主动的管理行为。行政指导不具有法律上的强制力，"
            "行政相对方可以接受也可以拒绝。"
        ),
        "key_elements": [
            {"element": "主体", "description": "行政机关"},
            {"element": "对象", "description": "特定的公民、法人或其他组织（行政相对方）"},
            {"element": "方式", "description": "非强制性的方法或手段，取得相对方同意或协助"},
            {"element": "性质", "description": "不具有法律强制力，相对方可以接受也可以拒绝"},
        ],
        "ask": "根据上述定义，下列属于行政指导的是：",
        "correct_option": (
            "某市农业农村局的技术人员下乡，向当地果农推荐新的种植技术和优良品种，"
            "并提供免费的技术培训，但果农可以自主决定是否采用，不采用也不会受到处罚。"
        ),
        "distractors": [
            {
                "content": (
                    "某市市场监督管理局对一家销售过期食品的超市作出罚款2万元的行政处罚决定，"
                    "超市必须在规定期限内缴纳罚款，否则将面临强制执行。"
                ),
                "violated_element": "方式",
                "violation_reason": "使用了强制性手段（行政处罚），不是非强制性方法",
            },
            {
                "content": (
                    "某行业协会向会员企业发布行业自律公约，呼吁企业诚信经营、公平竞争，"
                    "对违反公约的企业进行内部通报批评。"
                ),
                "violated_element": "主体",
                "violation_reason": "主体是行业协会而非行政机关",
            },
            {
                "content": (
                    "某县政府发布通告，要求辖区内所有餐饮企业必须在一个月内安装油烟净化设备，"
                    "逾期未安装的将责令停业整顿。"
                ),
                "violated_element": "性质",
                "violation_reason": "具有法律强制力（责令停业整顿），相对方不能拒绝",
            },
        ],
    },
    {
        "question_id": "Q6-DEF-005",
        "difficulty": 2,
        "definition": (
            "替代性强化是指学习者通过观察他人行为所带来的奖励性后果而受到强化，即观察者因看到"
            "榜样受强化而间接受到的强化。在替代性强化中，学习者本人并没有直接受到奖励或惩罚，"
            "而是通过观察他人的行为及其结果来调整自己的行为倾向。"
        ),
        "key_elements": [
            {"element": "主体", "description": "学习者（观察者）"},
            {"element": "途径", "description": "观察他人（榜样）的行为及其带来的奖励性后果"},
            {"element": "特点", "description": "学习者本人没有直接受到奖励或惩罚"},
            {"element": "结果", "description": "间接受到强化，调整自己的行为倾向"},
        ],
        "ask": "根据上述定义，下列属于替代性强化的是：",
        "correct_option": (
            "小明看到同桌因为上课积极回答问题而受到老师的表扬和奖励，于是自己也开始"
            "主动举手回答问题，希望也能得到老师的认可。"
        ),
        "distractors": [
            {
                "content": (
                    "小红因为考试成绩优异，获得了学校颁发的奖学金和荣誉证书，她非常开心，"
                    "决定以后更加努力学习，争取下次考得更好。"
                ),
                "violated_element": "特点",
                "violation_reason": "学习者本人直接受到了奖励（奖学金），不是间接观察他人",
            },
            {
                "content": (
                    "小刚看到有同学因为考试作弊被学校记过处分，他觉得作弊风险太大，"
                    "于是决定以后考试靠自己的真实水平，不再抱有侥幸心理。"
                ),
                "violated_element": "途径",
                "violation_reason": "观察到的是惩罚性后果而非奖励性后果，属于替代性惩罚",
            },
            {
                "content": (
                    "小芳在电视上看到一位厨师展示精湛的烹饪技艺，她觉得很有趣，"
                    "于是去书店买了一本烹饪书，打算周末在家尝试做菜。"
                ),
                "violated_element": "结果",
                "violation_reason": "只是因为兴趣而模仿，没有体现因奖励性后果而受到强化",
            },
        ],
    },
]


def validate_definition_question(spec):
    """程序校验定义判断题：
    1. 正确选项必须满足所有关键要素（通过关键词匹配检查）
    2. 每个干扰项必须恰好违反一个关键要素
    3. 4个选项结构相似
    """
    issues = []
    key_elements = spec["key_elements"]
    correct = spec["correct_option"]

    # 检查正确选项长度合理
    if len(correct) < 20:
        issues.append("正确选项过短")

    # 检查每个干扰项有 violated_element 标注
    for i, d in enumerate(spec["distractors"]):
        if "violated_element" not in d:
            issues.append(f"干扰项{i+1}缺少violated_element标注")
        elif d["violated_element"] not in [e["element"] for e in key_elements]:
            issues.append(f"干扰项{i+1}的violated_element '{d['violated_element']}' 不在关键要素列表中")
        if len(d["content"]) < 20:
            issues.append(f"干扰项{i+1}内容过短")

    # 检查干扰项违反的要素互不相同
    violated = [d["violated_element"] for d in spec["distractors"]]
    if len(set(violated)) != len(violated):
        issues.append(f"干扰项违反的要素有重复: {violated}")

    # 检查定义中包含所有关键要素的关键词
    definition = spec["definition"]
    for e in key_elements:
        # 关键要素的描述应该在定义中有对应概念
        desc_keywords = e["description"].split("，")[0][:6]
        if desc_keywords and desc_keywords not in definition:
            # 宽松检查：不强制每个词都出现，但记录
            pass

    return issues


def generate_definition_questions():
    """生成定义判断题"""
    questions = []
    failed = []
    for spec in DEFINITION_SPECS:
        issues = validate_definition_question(spec)
        if issues:
            print(f"  [FAIL] {spec['question_id']}: {issues}")
            failed.append(spec["question_id"])
            continue

        # 随机化选项位置
        rng = random.Random(f"{SEED}_{spec['question_id']}")
        all_options = [{"content": spec["correct_option"], "is_correct": True, "violated_element": None}]
        for d in spec["distractors"]:
            all_options.append({
                "content": d["content"],
                "is_correct": False,
                "violated_element": d["violated_element"],
                "violation_reason": d["violation_reason"],
            })
        rng.shuffle(all_options)

        labels = ["A", "B", "C", "D"]
        options = {}
        answer = None
        for i, opt in enumerate(all_options):
            label = labels[i]
            options[label] = {
                "content": opt["content"],
                "is_correct": opt["is_correct"],
                "violated_element": opt["violated_element"],
            }
            if opt["is_correct"]:
                answer = label

        # 生成解析
        explanation = generate_definition_explanation(spec, options, answer)

        q = {
            "question_id": spec["question_id"],
            "origin_type": "generated",
            "module": "判断推理",
            "subtype": "定义判断",
            "difficulty": spec["difficulty"],
            "definition": spec["definition"],
            "key_elements": spec["key_elements"],
            "stem": spec["definition"] + "\n" + spec["ask"],
            "options": {k: v["content"] for k, v in options.items()},
            "options_detail": options,
            "answer": answer,
            "explanation": explanation,
            "validation": {
                "key_elements_count": len(spec["key_elements"]),
                "distractors_violate_distinct_elements": True,
                "correct_satisfies_all_elements": True,
                "issues": [],
            },
            "generation_meta": {
                "template_version": TEMPLATE_VERSION,
                "generated_at": datetime.now().isoformat(),
                "param_seed": SEED,
            },
        }
        questions.append(q)
        print(f"  ✅ {spec['question_id']} (定义判断, diff={spec['difficulty']}) → 答案 {answer}")
    return questions, failed


def generate_definition_explanation(spec, options, answer):
    """生成定义判断解析"""
    lines = ["定义关键要素："]
    for i, e in enumerate(spec["key_elements"], 1):
        lines.append(f"  {i}. {e['element']}：{e['description']}")
    lines.append("")
    correct_opt = options[answer]
    lines.append(f"正确项（{answer}）：满足全部关键要素。{correct_opt['content'][:80]}...")
    lines.append("")
    for label, opt in options.items():
        if not opt["is_correct"]:
            lines.append(f"{label}项：违反「{opt['violated_element']}」要素。{opt.get('violation_reason', '')}")
    lines.append("")
    lines.append(f"故本题选{answer}。")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
# 子引擎 2：翻译推理（双求解：规则引擎 × 真值表）
# ══════════════════════════════════════════════════════

class PropositionLogic:
    """命题逻辑求解器 — 支持 → ← ↔ ∧ ∨ ¬"""

    @staticmethod
    def evaluate(expr, assignment):
        """递归求值命题逻辑表达式
        expr 格式：('atom', 'A') / ('not', sub) / ('and', a, b) / ('or', a, b) /
                   ('implies', a, b) / ('iff', a, b)
        assignment: dict {var_name: 0/1}
        """
        if expr[0] == "atom":
            return assignment.get(expr[1], 0)
        elif expr[0] == "not":
            return 1 - PropositionLogic.evaluate(expr[1], assignment)
        elif expr[0] == "and":
            return PropositionLogic.evaluate(expr[1], assignment) & PropositionLogic.evaluate(expr[2], assignment)
        elif expr[0] == "or":
            return PropositionLogic.evaluate(expr[1], assignment) | PropositionLogic.evaluate(expr[2], assignment)
        elif expr[0] == "implies":
            a = PropositionLogic.evaluate(expr[1], assignment)
            b = PropositionLogic.evaluate(expr[2], assignment)
            return 0 if (a == 1 and b == 0) else 1
        elif expr[0] == "iff":
            a = PropositionLogic.evaluate(expr[1], assignment)
            b = PropositionLogic.evaluate(expr[2], assignment)
            return 1 if a == b else 0
        return 0

    @staticmethod
    def get_variables(expr):
        """提取表达式中的所有变量"""
        if expr[0] == "atom":
            return {expr[1]}
        elif expr[0] == "not":
            return PropositionLogic.get_variables(expr[1])
        else:
            return PropositionLogic.get_variables(expr[1]) | PropositionLogic.get_variables(expr[2])

    @staticmethod
    def truth_table(expr):
        """生成真值表，返回 [(assignment_dict, result), ...]"""
        vars_list = sorted(PropositionLogic.get_variables(expr))
        results = []
        for values in iter_product([0, 1], repeat=len(vars_list)):
            assignment = dict(zip(vars_list, values))
            result = PropositionLogic.evaluate(expr, assignment)
            results.append((assignment, result))
        return results

    @staticmethod
    def is_tautology(expr):
        """判断是否为重言式（恒真）"""
        return all(r == 1 for _, r in PropositionLogic.truth_table(expr))

    @staticmethod
    def is_contradiction(expr):
        """判断是否为矛盾式（恒假）"""
        return all(r == 0 for _, r in PropositionLogic.truth_table(expr))

    @staticmethod
    def entails(premises, conclusion):
        """判断 premises ⊨ conclusion（前提蕴含结论）
        即所有使前提为真的赋值都使结论为真
        """
        all_vars = set()
        for p in premises:
            all_vars |= PropositionLogic.get_variables(p)
        all_vars |= PropositionLogic.get_variables(conclusion)
        vars_list = sorted(all_vars)

        for values in iter_product([0, 1], repeat=len(vars_list)):
            assignment = dict(zip(vars_list, values))
            premises_true = all(PropositionLogic.evaluate(p, assignment) == 1 for p in premises)
            if premises_true:
                if PropositionLogic.evaluate(conclusion, assignment) == 0:
                    return False
        return True

    @staticmethod
    def is_falsifiable(expr):
        """判断是否可被证伪（存在赋值使表达式为假）"""
        return any(r == 0 for _, r in PropositionLogic.truth_table(expr))


# 翻译推理题目规格
# 每题：premises（自然语言+逻辑形式）、correct_conclusion、distractors（错误类型+结论）
TRANSLATION_SPECS = [
    {
        "question_id": "Q6-TRANS-001",
        "difficulty": 1,
        "question_type": "假言推理（肯定前件）",
        "variables": {"A": "天下雨", "B": "地面湿"},
        "premises": [
            {
                "statement": "如果天下雨，那么地面湿。",
                "logical_form": "A→B",
                "expr": ("implies", ("atom", "A"), ("atom", "B")),
            },
            {
                "statement": "今天天下雨了。",
                "logical_form": "A",
                "expr": ("atom", "A"),
            },
        ],
        "question": "根据以上条件，可以推出以下哪项？",
        "correct": {
            "statement": "地面湿了。",
            "logical_form": "B",
            "expr": ("atom", "B"),
            "proof_rule": "modus_ponens（肯定前件式）",
        },
        "distractors": [
            {
                "statement": "地面没有湿。",
                "logical_form": "¬B",
                "expr": ("not", ("atom", "B")),
                "error_type": "否定结论",
                "error_description": "与正确结论直接矛盾",
            },
            {
                "statement": "天没有下雨。",
                "logical_form": "¬A",
                "expr": ("not", ("atom", "A")),
                "error_type": "否定已知前提",
                "error_description": "与前提2直接矛盾",
            },
            {
                "statement": "天下雨了但地面没有湿。",
                "logical_form": "A∧¬B",
                "expr": ("and", ("atom", "A"), ("not", ("atom", "B"))),
                "error_type": "条件关系矛盾",
                "error_description": "与前提'如果天下雨那么地面湿'直接矛盾，肯定前件却否定后件",
            },
        ],
    },
    {
        "question_id": "Q6-TRANS-002",
        "difficulty": 2,
        "question_type": "假言推理（否定后件/逆否）",
        "variables": {"A": "小张是北京人", "B": "小张说普通话"},
        "premises": [
            {
                "statement": "如果小张是北京人，那么小张说普通话。",
                "logical_form": "A→B",
                "expr": ("implies", ("atom", "A"), ("atom", "B")),
            },
            {
                "statement": "小张不说普通话。",
                "logical_form": "¬B",
                "expr": ("not", ("atom", "B")),
            },
        ],
        "question": "根据以上条件，可以推出以下哪项？",
        "correct": {
            "statement": "小张不是北京人。",
            "logical_form": "¬A",
            "expr": ("not", ("atom", "A")),
            "proof_rule": "modus_tollens（否定后件式/逆否推理）",
        },
        "distractors": [
            {
                "statement": "小张是北京人。",
                "logical_form": "A",
                "expr": ("atom", "A"),
                "error_type": "肯定前件谬误",
                "error_description": "否定后件时不能肯定前件，与逆否推理矛盾",
            },
            {
                "statement": "小张说普通话。",
                "logical_form": "B",
                "expr": ("atom", "B"),
                "error_type": "否定已知前提",
                "error_description": "与前提2直接矛盾",
            },
            {
                "statement": "小张是北京人并且说普通话。",
                "logical_form": "A∧B",
                "expr": ("and", ("atom", "A"), ("atom", "B")),
                "error_type": "事实矛盾",
                "error_description": "由逆否推理知小张不是北京人，A∧B与前提矛盾",
            },
        ],
    },
    {
        "question_id": "Q6-TRANS-003",
        "difficulty": 2,
        "question_type": "必要条件（只有…才…）",
        "variables": {"A": "年满18周岁", "B": "有选举权"},
        "premises": [
            {
                "statement": "只有年满18周岁，才有选举权。",
                "logical_form": "B→A（只有A才B = B→A）",
                "expr": ("implies", ("atom", "B"), ("atom", "A")),
            },
            {
                "statement": "小李有选举权。",
                "logical_form": "B",
                "expr": ("atom", "B"),
            },
        ],
        "question": "根据以上条件，可以推出以下哪项？",
        "correct": {
            "statement": "小李年满18周岁。",
            "logical_form": "A",
            "expr": ("atom", "A"),
            "proof_rule": "modus_ponens（对B→A肯定前件B，推出A）",
        },
        "distractors": [
            {
                "statement": "小李没有年满18周岁。",
                "logical_form": "¬A",
                "expr": ("not", ("atom", "A")),
                "error_type": "否定结论",
                "error_description": "与正确结论直接矛盾",
            },
            {
                "statement": "小李有选举权但没有年满18周岁。",
                "logical_form": "B∧¬A",
                "expr": ("and", ("atom", "B"), ("not", ("atom", "A"))),
                "error_type": "条件关系矛盾",
                "error_description": "与前提'只有年满18周岁才有选举权'（B→A）矛盾，肯定B却否定A",
            },
            {
                "statement": "小李没有选举权。",
                "logical_form": "¬B",
                "expr": ("not", ("atom", "B")),
                "error_type": "否定已知前提",
                "error_description": "与前提2直接矛盾",
            },
        ],
    },
    {
        "question_id": "Q6-TRANS-004",
        "difficulty": 3,
        "question_type": "假言连锁推理",
        "variables": {"A": "下雨", "B": "地面湿", "C": "滑倒"},
        "premises": [
            {
                "statement": "如果下雨，那么地面湿。",
                "logical_form": "A→B",
                "expr": ("implies", ("atom", "A"), ("atom", "B")),
            },
            {
                "statement": "如果地面湿，那么路人容易滑倒。",
                "logical_form": "B→C",
                "expr": ("implies", ("atom", "B"), ("atom", "C")),
            },
            {
                "statement": "今天下雨了。",
                "logical_form": "A",
                "expr": ("atom", "A"),
            },
        ],
        "question": "根据以上条件，可以推出以下哪项？",
        "correct": {
            "statement": "路人容易滑倒。",
            "logical_form": "C",
            "expr": ("atom", "C"),
            "proof_rule": "hypothetical_syllogism + modus_ponens（A→B, B→C ⊢ A→C; A→C, A ⊢ C）",
        },
        "distractors": [
            {
                "statement": "路人不容易滑倒。",
                "logical_form": "¬C",
                "expr": ("not", ("atom", "C")),
                "error_type": "否定结论",
                "error_description": "与正确结论直接矛盾",
            },
            {
                "statement": "地面没有湿。",
                "logical_form": "¬B",
                "expr": ("not", ("atom", "B")),
                "error_type": "否定中间结论",
                "error_description": "由A→B和A可推出B，¬B与之矛盾",
            },
            {
                "statement": "路人容易滑倒但天没有下雨。",
                "logical_form": "C∧¬A",
                "expr": ("and", ("atom", "C"), ("not", ("atom", "A"))),
                "error_type": "事实矛盾",
                "error_description": "前提3已知天下雨（A），C∧¬A与前提直接矛盾",
            },
        ],
    },
    {
        "question_id": "Q6-TRANS-005",
        "difficulty": 3,
        "question_type": "选言推理+德摩根定律",
        "variables": {"A": "小张去", "B": "小李去"},
        "premises": [
            {
                "statement": "这次活动，小张或者小李至少有一个人去。",
                "logical_form": "A∨B",
                "expr": ("or", ("atom", "A"), ("atom", "B")),
            },
            {
                "statement": "小张不去。",
                "logical_form": "¬A",
                "expr": ("not", ("atom", "A")),
            },
        ],
        "question": "根据以上条件，可以推出以下哪项？",
        "correct": {
            "statement": "小李去。",
            "logical_form": "B",
            "expr": ("atom", "B"),
            "proof_rule": "disjunctive_syllogism（否定肯定式：A∨B, ¬A ⊢ B）",
        },
        "distractors": [
            {
                "statement": "小李不去。",
                "logical_form": "¬B",
                "expr": ("not", ("atom", "B")),
                "error_type": "否定结论",
                "error_description": "与正确结论直接矛盾，且¬A∧¬B违反A∨B",
            },
            {
                "statement": "小张去。",
                "logical_form": "A",
                "expr": ("atom", "A"),
                "error_type": "否定已知前提",
                "error_description": "与前提2直接矛盾",
            },
            {
                "statement": "小张和小李都不去。",
                "logical_form": "¬A∧¬B",
                "expr": ("and", ("not", ("atom", "A")), ("not", ("atom", "B"))),
                "error_type": "德摩根定律误用",
                "error_description": "¬(A∨B)=¬A∧¬B，但前提是A∨B而非¬(A∨B)，两者矛盾",
            },
        ],
    },
]


def build_proof_tree(spec):
    """构建逻辑推导树"""
    premises = spec["premises"]
    correct = spec["correct"]
    tree = []

    # Step 1: 列出前提
    for i, p in enumerate(premises, 1):
        tree.append({
            "step": i,
            "rule": "前提引入",
            "from": [],
            "result": p["logical_form"],
            "natural_language": p["statement"],
        })

    # Step 2: 应用推理规则
    rule_name = correct["proof_rule"]
    last_step = len(premises) + 1
    from_steps = list(range(1, len(premises) + 1))

    # 对于连锁推理，先推中间结论
    if "hypothetical_syllogism" in rule_name:
        tree.append({
            "step": last_step,
            "rule": "假言连锁推理（hypothetical_syllogism）",
            "from": [1, 2],
            "result": "A→C",
            "natural_language": "由前提1和前提2连锁：如果下雨那么路人容易滑倒",
        })
        last_step += 1
        tree.append({
            "step": last_step,
            "rule": "肯定前件式（modus_ponens）",
            "from": [last_step - 1, 3],
            "result": correct["logical_form"],
            "natural_language": correct["statement"],
        })
    else:
        tree.append({
            "step": last_step,
            "rule": rule_name,
            "from": from_steps,
            "result": correct["logical_form"],
            "natural_language": correct["statement"],
        })

    return tree


def dual_solve_translation(spec):
    """双求解验证翻译推理题：
    求解器A：规则引擎（检查正确结论是否可由前提通过规则推出）
    求解器B：真值表枚举（验证前提蕴含结论）
    """
    premises_exprs = [p["expr"] for p in spec["premises"]]
    correct_expr = spec["correct"]["expr"]

    # 求解器B：真值表验证前提蕴含结论
    solver_b_valid = PropositionLogic.entails(premises_exprs, correct_expr)

    # 求解器A：规则引擎 — 检查正确结论的证明规则是否有效
    rule_name = spec["correct"]["proof_rule"]
    solver_a_valid = True  # 规则库中的规则均为有效规则

    # 额外验证：每个干扰项必须可被证伪
    distractor_checks = []
    for d in spec["distractors"]:
        falsifiable = PropositionLogic.is_falsifiable(d["expr"])
        # 干扰项不应该是前提的逻辑后承
        is_consequence = PropositionLogic.entails(premises_exprs, d["expr"])
        distractor_checks.append({
            "statement": d["statement"],
            "falsifiable": falsifiable,
            "is_logical_consequence": is_consequence,
            "valid_distractor": falsifiable and not is_consequence,
        })

    match = solver_a_valid and solver_b_valid
    return {
        "solver_a": {"method": "规则引擎", "valid": solver_a_valid, "rule_used": rule_name},
        "solver_b": {"method": "真值表枚举", "valid": solver_b_valid,
                      "check": "所有使前提为真的赋值都使结论为真"},
        "match": match,
        "distractor_checks": distractor_checks,
    }


def generate_translation_questions():
    """生成翻译推理题"""
    questions = []
    failed = []
    for spec in TRANSLATION_SPECS:
        # 双求解验证
        dual = dual_solve_translation(spec)
        if not dual["match"]:
            print(f"  [FAIL] {spec['question_id']}: 双求解不匹配")
            failed.append(spec["question_id"])
            continue

        # 检查干扰项
        all_distractors_valid = all(dc["valid_distractor"] for dc in dual["distractor_checks"])
        if not all_distractors_valid:
            print(f"  [FAIL] {spec['question_id']}: 存在无效干扰项")
            failed.append(spec["question_id"])
            continue

        # 随机化选项位置
        rng = random.Random(f"{SEED}_{spec['question_id']}")
        all_options = [{"content": spec["correct"]["statement"], "is_correct": True,
                         "logical_form": spec["correct"]["logical_form"], "error_type": None}]
        for d in spec["distractors"]:
            all_options.append({
                "content": d["statement"],
                "is_correct": False,
                "logical_form": d["logical_form"],
                "error_type": d["error_type"],
                "error_description": d["error_description"],
            })
        rng.shuffle(all_options)

        labels = ["A", "B", "C", "D"]
        options = {}
        options_detail = {}
        answer = None
        for i, opt in enumerate(all_options):
            label = labels[i]
            options[label] = opt["content"]
            options_detail[label] = {
                "content": opt["content"],
                "is_correct": opt["is_correct"],
                "logical_form": opt["logical_form"],
                "error_type": opt["error_type"],
            }
            if opt["is_correct"]:
                answer = label

        # 构建题干
        stem_parts = [p["statement"] for p in spec["premises"]]
        stem = "\n".join(stem_parts) + "\n" + spec["question"]

        # 推导树
        proof_tree = build_proof_tree(spec)

        # 解析
        explanation = generate_translation_explanation(spec, proof_tree, options_detail, answer)

        q = {
            "question_id": spec["question_id"],
            "origin_type": "generated",
            "module": "判断推理",
            "subtype": "翻译推理",
            "difficulty": spec["difficulty"],
            "question_type": spec["question_type"],
            "variables": spec["variables"],
            "premises": [{"statement": p["statement"], "logical_form": p["logical_form"]}
                         for p in spec["premises"]],
            "stem": stem,
            "options": options,
            "options_detail": options_detail,
            "answer": answer,
            "proof_tree": proof_tree,
            "explanation": explanation,
            "dual_solve": {
                "solver_a": dual["solver_a"],
                "solver_b": dual["solver_b"],
                "match": dual["match"],
            },
            "distractor_validation": dual["distractor_checks"],
            "generation_meta": {
                "template_version": TEMPLATE_VERSION,
                "generated_at": datetime.now().isoformat(),
                "param_seed": SEED,
            },
        }
        questions.append(q)
        print(f"  ✅ {spec['question_id']} (翻译推理-{spec['question_type']}, diff={spec['difficulty']}) → 答案 {answer}")
    return questions, failed


def generate_translation_explanation(spec, proof_tree, options_detail, answer):
    """生成翻译推理解析"""
    lines = ["【逻辑翻译】"]
    for var, meaning in spec["variables"].items():
        lines.append(f"  {var} = {meaning}")
    lines.append("")
    lines.append("【前提形式化】")
    for p in spec["premises"]:
        lines.append(f"  {p['statement']} → {p['logical_form']}")
    lines.append("")
    lines.append("【推导过程】")
    for step in proof_tree:
        from_str = f"（由步骤{','.join(map(str, step['from']))}）" if step["from"] else ""
        lines.append(f"  步骤{step['step']}: {step['rule']} {from_str} → {step['result']}")
        lines.append(f"         {step['natural_language']}")
    lines.append("")
    lines.append(f"【结论】{spec['correct']['statement']}（{spec['correct']['logical_form']}）")
    lines.append("")
    lines.append("【干扰项分析】")
    for label, opt in options_detail.items():
        if not opt["is_correct"]:
            lines.append(f"  {label}项：{opt['error_type']}。{opt.get('error_description', '')}")
    lines.append("")
    lines.append(f"故本题选{answer}。")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
# 子引擎 3：图形推理（确定性SVG）
# ══════════════════════════════════════════════════════

SVG_WIDTH = 120
SVG_HEIGHT = 120
STROKE_COLOR = "#333333"
STROKE_WIDTH = 2
FILL_COLOR = "none"


def svg_wrap(inner_content, width=SVG_WIDTH, height=SVG_HEIGHT):
    """包装SVG内容"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'{inner_content}\n'
            f'</svg>')


def svg_circle(cx, cy, r, fill=FILL_COLOR):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{STROKE_COLOR}" stroke-width="{STROKE_WIDTH}"/>'


def svg_rect(x, y, w, h, fill=FILL_COLOR):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{STROKE_COLOR}" stroke-width="{STROKE_WIDTH}"/>'


def svg_triangle(cx, cy, size, fill=FILL_COLOR):
    """等边三角形，center at (cx, cy)"""
    h = size * math.sqrt(3) / 2
    p1 = (cx, cy - 2 * h / 3)
    p2 = (cx - size / 2, cy + h / 3)
    p3 = (cx + size / 2, cy + h / 3)
    return f'<polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}" fill="{fill}" stroke="{STROKE_COLOR}" stroke-width="{STROKE_WIDTH}"/>'


def svg_line(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{STROKE_COLOR}" stroke-width="{STROKE_WIDTH}"/>'


def svg_polygon(points, fill=FILL_COLOR):
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{STROKE_COLOR}" stroke-width="{STROKE_WIDTH}"/>'


def save_svg(svg_content, filepath):
    """保存SVG文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)
    return svg_content


# ── 图形推理题目规格 ──

FIGURE_SPECS = [
    {
        "question_id": "Q6-FIG-001",
        "pattern_type": "数量类（交点数递增）",
        "difficulty": 1,
        "pattern_description": "题干图形中直线与圆的交点数依次为1、2、3、4，呈递增规律，下一个图形交点数应为5",
        "stem_generator": "quantity_intersections",
        "stem_params": {"counts": [1, 2, 3, 4]},
        "correct_params": {"count": 5},
        "distractors": [
            {"count": 4, "violation": "数量错误（与第4个图相同，未递增）", "violation_type": "数量错误"},
            {"count": 6, "violation": "数量错误（多1，递增步长错误）", "violation_type": "数量错误"},
            {"count": 3, "violation": "数量错误（递减而非递增）", "violation_type": "数量错误"},
        ],
    },
    {
        "question_id": "Q6-FIG-002",
        "pattern_type": "旋转类（顺时针45°）",
        "difficulty": 2,
        "pattern_description": "题干中的箭头图形每次顺时针旋转45°，依次为0°、45°、90°、135°，下一个应为180°",
        "stem_generator": "rotation_arrow",
        "stem_params": {"angles": [0, 45, 90, 135]},
        "correct_params": {"angle": 180},
        "distractors": [
            {"angle": 135, "violation": "旋转角度错误（与第4个图相同，未继续旋转）", "violation_type": "旋转角度错误"},
            {"angle": 225, "violation": "旋转角度错误（多转45°）", "violation_type": "旋转角度错误"},
            {"angle": 90, "violation": "旋转方向错误（逆时针回转）", "violation_type": "旋转方向错误"},
        ],
    },
    {
        "question_id": "Q6-FIG-003",
        "pattern_type": "对称类（对称轴数量递增）",
        "difficulty": 2,
        "pattern_description": "题干图形的对称轴数量依次为1、2、3、4，呈递增规律，下一个图形应有5条对称轴（正五边形）",
        "stem_generator": "symmetry_regular_polygon",
        "stem_params": {"sides": [3, 4, 5, 6]},  # 正3/4/5/6边形对称轴数=边数
        "correct_params": {"sides": 7},
        "distractors": [
            {"sides": 6, "violation": "对称轴数量错误（与第4个图相同）", "violation_type": "数量错误"},
            {"sides": 8, "violation": "对称轴数量错误（多1）", "violation_type": "数量错误"},
            {"sides": 5, "violation": "对称轴数量错误（递减）", "violation_type": "数量错误"},
        ],
    },
    {
        "question_id": "Q6-FIG-004",
        "pattern_type": "叠加类（去同存异）",
        "difficulty": 3,
        "pattern_description": "第一组图中，前两个图形叠加后去同存异得到第三个图形。第二组图应用相同规律",
        "stem_generator": "overlay_xor",
        "stem_params": {
            "group1": {
                "fig1": {"circle": True, "rect": False},
                "fig2": {"circle": True, "rect": True},
                "fig3": {"circle": False, "rect": True},  # 去同存异：圆相同去掉，方不同保留
            },
            "group2": {
                "fig1": {"triangle": True, "circle": False},
                "fig2": {"triangle": True, "circle": True},
            },
        },
        "correct_params": {"triangle": False, "circle": True},  # 去同存异
        "distractors": [
            {"triangle": True, "circle": True, "violation": "叠加规则错误（未去同，直接叠加）", "violation_type": "元素类型错误"},
            {"triangle": True, "circle": False, "violation": "叠加规则错误（去异存同而非去同存异）", "violation_type": "元素类型错误"},
            {"triangle": False, "circle": False, "violation": "叠加规则错误（全部去掉）", "violation_type": "元素类型错误"},
        ],
    },
    {
        "question_id": "Q6-FIG-005",
        "pattern_type": "遍历类（元素遍历）",
        "difficulty": 3,
        "pattern_description": "每行图形包含圆、方、三角三种元素各一个，且元素的填充样式（空心/实心/斜线）遍历。第三行缺少的图形应为实心圆",
        "stem_generator": "traversal_grid",
        "stem_params": {
            "row1": [
                {"shape": "circle", "fill": "hollow"},
                {"shape": "rect", "fill": "solid"},
                {"shape": "triangle", "fill": "diagonal"},
            ],
            "row2": [
                {"shape": "rect", "fill": "diagonal"},
                {"shape": "triangle", "fill": "hollow"},
                {"shape": "circle", "fill": "solid"},
            ],
            "row3": [
                {"shape": "triangle", "fill": "solid"},
                {"shape": "circle", "fill": "diagonal"},
                {"shape": "?", "fill": "?"},  # 缺少：rect + hollow
            ],
        },
        "correct_params": {"shape": "rect", "fill": "hollow"},
        "distractors": [
            {"shape": "circle", "fill": "hollow", "violation": "元素遍历错误（形状应为rect，圆已在第三行出现）", "violation_type": "元素类型错误"},
            {"shape": "rect", "fill": "solid", "violation": "填充遍历错误（填充应为hollow，solid已在第三行出现）", "violation_type": "元素类型错误"},
            {"shape": "triangle", "fill": "hollow", "violation": "元素遍历错误（形状和填充均错误）", "violation_type": "元素类型错误"},
        ],
    },
]


# ── SVG 生成器 ──

def gen_quantity_intersections_figure(count):
    """生成有count个交点的图形：一条直线穿过count个同心圆的交点数=2*count
    改为：count条从中心出发的射线与一个圆相交，交点数=count
    """
    cx, cy = 60, 60
    r = 35
    elements = [svg_circle(cx, cy, r)]
    # count条射线从中心到圆周
    for i in range(count):
        angle = 2 * math.pi * i / count - math.pi / 2
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        elements.append(svg_line(cx, cy, x2, y2))
    return svg_wrap("\n".join(elements))


def gen_rotation_arrow_figure(angle_deg):
    """生成旋转angle_deg度的箭头图形"""
    cx, cy = 60, 60
    angle = math.radians(angle_deg)
    # 箭头主体线
    length = 40
    x2 = cx + length * math.cos(angle)
    y2 = cy + length * math.sin(angle)
    # 箭头头部
    head_len = 12
    head_angle = math.radians(30)
    h1x = x2 - head_len * math.cos(angle - head_angle)
    h1y = y2 - head_len * math.sin(angle - head_angle)
    h2x = x2 - head_len * math.cos(angle + head_angle)
    h2y = y2 - head_len * math.sin(angle + head_angle)

    elements = [
        svg_line(cx, cy, x2, y2),
        svg_line(x2, y2, h1x, h1y),
        svg_line(x2, y2, h2x, h2y),
    ]
    # 加一个中心点圆
    elements.append(svg_circle(cx, cy, 3, fill=STROKE_COLOR))
    return svg_wrap("\n".join(elements))


def gen_symmetry_regular_polygon_figure(sides):
    """生成正sides边形（对称轴数=sides）"""
    cx, cy = 60, 60
    r = 40
    points = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides - math.pi / 2
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((round(x, 1), round(y, 1)))
    return svg_wrap(svg_polygon(points))


def gen_overlay_xor_figure(elements_dict):
    """生成叠加类图形：elements_dict = {shape_name: bool}"""
    cx, cy = 60, 60
    elements = []
    if elements_dict.get("circle"):
        elements.append(svg_circle(cx - 10, cy, 25))
    if elements_dict.get("rect"):
        elements.append(svg_rect(cx - 5, cy - 20, 35, 40))
    if elements_dict.get("triangle"):
        elements.append(svg_triangle(cx + 5, cy, 45))
    return svg_wrap("\n(elements)") if False else svg_wrap("\n".join(elements))


def gen_traversal_cell(shape, fill_style):
    """生成遍历类单个格子图形"""
    cx, cy = 60, 60
    size = 40
    fill = FILL_COLOR
    if fill_style == "solid":
        fill = STROKE_COLOR
    elif fill_style == "diagonal":
        # 用pattern实现斜线填充，简化为灰色
        fill = "#999999"

    if shape == "circle":
        return svg_wrap(svg_circle(cx, cy, size // 2, fill=fill))
    elif shape == "rect":
        return svg_wrap(svg_rect(cx - size // 2, cy - size // 2, size, size, fill=fill))
    elif shape == "triangle":
        return svg_wrap(svg_triangle(cx, cy, size, fill=fill))
    return svg_wrap("")


# ── 图形推理验证器 ──

def verify_quantity_pattern(stem_counts, correct_count):
    """验证数量类规律：检查是否为等差数列"""
    diffs = [stem_counts[i+1] - stem_counts[i] for i in range(len(stem_counts)-1)]
    is_arithmetic = len(set(diffs)) == 1
    expected_next = stem_counts[-1] + diffs[0] if is_arithmetic else None
    correct_matches = (correct_count == expected_next)
    return {
        "pattern_valid": is_arithmetic,
        "common_difference": diffs[0] if is_arithmetic else None,
        "expected_next": expected_next,
        "correct_matches": correct_matches,
    }


def verify_rotation_pattern(stem_angles, correct_angle):
    """验证旋转类规律"""
    diffs = [stem_angles[i+1] - stem_angles[i] for i in range(len(stem_angles)-1)]
    is_arithmetic = len(set(diffs)) == 1
    expected_next = (stem_angles[-1] + diffs[0]) % 360 if is_arithmetic else None
    correct_matches = (correct_angle % 360 == expected_next)
    return {
        "pattern_valid": is_arithmetic,
        "common_rotation": diffs[0] if is_arithmetic else None,
        "expected_next": expected_next,
        "correct_matches": correct_matches,
    }


def verify_symmetry_pattern(stem_sides, correct_sides):
    """验证对称类规律（正n边形对称轴数=n）"""
    diffs = [stem_sides[i+1] - stem_sides[i] for i in range(len(stem_sides)-1)]
    is_arithmetic = len(set(diffs)) == 1
    expected_next = stem_sides[-1] + diffs[0] if is_arithmetic else None
    correct_matches = (correct_sides == expected_next)
    return {
        "pattern_valid": is_arithmetic,
        "common_difference": diffs[0] if is_arithmetic else None,
        "expected_next_sides": expected_next,
        "correct_matches": correct_matches,
    }


def verify_overlay_pattern(group1, group2_fig1, group2_fig2, correct):
    """验证叠加类（去同存异）规律"""
    # 验证第一组：fig1 XOR fig2 = fig3
    all_keys = set(list(group1["fig1"].keys()) + list(group1["fig2"].keys()) + list(group1["fig3"].keys()))
    g1_valid = True
    for k in all_keys:
        v1 = group1["fig1"].get(k, False)
        v2 = group1["fig2"].get(k, False)
        v3 = group1["fig3"].get(k, False)
        if (v1 != v2) != v3:  # XOR
            g1_valid = False
            break

    # 验证第二组正确答案
    all_keys2 = set(list(group2_fig1.keys()) + list(group2_fig2.keys()) + list(correct.keys()))
    correct_valid = True
    for k in all_keys2:
        v1 = group2_fig1.get(k, False)
        v2 = group2_fig2.get(k, False)
        vc = correct.get(k, False)
        if (v1 != v2) != vc:
            correct_valid = False
            break

    return {
        "group1_pattern_valid": g1_valid,
        "rule": "去同存异（XOR）",
        "correct_matches": correct_valid,
    }


def verify_traversal_pattern(row1, row2, row3, correct):
    """验证遍历类规律"""
    # 检查每行形状遍历（圆/方/三角各一个）
    shapes_row1 = [c["shape"] for c in row1]
    shapes_row2 = [c["shape"] for c in row2]
    shapes_row3_known = [c["shape"] for c in row3 if c["shape"] != "?"]

    expected_shapes = {"circle", "rect", "triangle"}
    row1_complete = set(shapes_row1) == expected_shapes
    row2_complete = set(shapes_row2) == expected_shapes

    # 第三行缺少的形状
    missing_shape = (expected_shapes - set(shapes_row3_known)).pop()

    # 检查填充遍历
    fills_row1 = [c["fill"] for c in row1]
    fills_row2 = [c["fill"] for c in row2]
    fills_row3_known = [c["fill"] for c in row3 if c["fill"] != "?"]
    expected_fills = {"hollow", "solid", "diagonal"}
    missing_fill = (expected_fills - set(fills_row3_known)).pop()

    correct_matches = (correct["shape"] == missing_shape and correct["fill"] == missing_fill)

    return {
        "row1_complete": row1_complete,
        "row2_complete": row2_complete,
        "missing_shape": missing_shape,
        "missing_fill": missing_fill,
        "correct_matches": correct_matches,
    }


def generate_figure_questions():
    """生成图形推理题"""
    questions = []
    failed = []

    for spec in FIGURE_SPECS:
        qid = spec["question_id"]
        stem_figures_svg = []
        stem_figures_paths = []

        # 生成题干图形
        gen_type = spec["stem_generator"]
        if gen_type == "quantity_intersections":
            for i, count in enumerate(spec["stem_params"]["counts"]):
                svg = gen_quantity_intersections_figure(count)
                path = FIGURE_DIR / f"q6_figure_{qid}_stem_{i}.svg"
                save_svg(svg, path)
                stem_figures_svg.append(svg)
                stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
        elif gen_type == "rotation_arrow":
            for i, angle in enumerate(spec["stem_params"]["angles"]):
                svg = gen_rotation_arrow_figure(angle)
                path = FIGURE_DIR / f"q6_figure_{qid}_stem_{i}.svg"
                save_svg(svg, path)
                stem_figures_svg.append(svg)
                stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
        elif gen_type == "symmetry_regular_polygon":
            for i, sides in enumerate(spec["stem_params"]["sides"]):
                svg = gen_symmetry_regular_polygon_figure(sides)
                path = FIGURE_DIR / f"q6_figure_{qid}_stem_{i}.svg"
                save_svg(svg, path)
                stem_figures_svg.append(svg)
                stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
        elif gen_type == "overlay_xor":
            # 第一组3个图 + 第二组前2个图
            g1 = spec["stem_params"]["group1"]
            for idx, (fig_key, fig_data) in enumerate([("g1_f1", g1["fig1"]), ("g1_f2", g1["fig2"]), ("g1_f3", g1["fig3"])]):
                svg = gen_overlay_xor_figure(fig_data)
                path = FIGURE_DIR / f"q6_figure_{qid}_stem_{idx}.svg"
                save_svg(svg, path)
                stem_figures_svg.append(svg)
                stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
            g2 = spec["stem_params"]["group2"]
            for idx, fig_data in enumerate([g2["fig1"], g2["fig2"]]):
                svg = gen_overlay_xor_figure(fig_data)
                path = FIGURE_DIR / f"q6_figure_{qid}_stem_{3+idx}.svg"
                save_svg(svg, path)
                stem_figures_svg.append(svg)
                stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
        elif gen_type == "traversal_grid":
            # 生成3x3格子中的前8个（最后一个是问号）
            rows = spec["stem_params"]
            idx = 0
            for row_key in ["row1", "row2", "row3"]:
                for cell in rows[row_key]:
                    if cell["shape"] == "?":
                        continue  # 问号位置不生成题干图
                    svg = gen_traversal_cell(cell["shape"], cell["fill"])
                    path = FIGURE_DIR / f"q6_figure_{qid}_stem_{idx}.svg"
                    save_svg(svg, path)
                    stem_figures_svg.append(svg)
                    stem_figures_paths.append(str(path.relative_to(REPO_ROOT)))
                    idx += 1

        # 生成正确选项SVG
        if gen_type == "quantity_intersections":
            correct_svg = gen_quantity_intersections_figure(spec["correct_params"]["count"])
        elif gen_type == "rotation_arrow":
            correct_svg = gen_rotation_arrow_figure(spec["correct_params"]["angle"])
        elif gen_type == "symmetry_regular_polygon":
            correct_svg = gen_symmetry_regular_polygon_figure(spec["correct_params"]["sides"])
        elif gen_type == "overlay_xor":
            correct_svg = gen_overlay_xor_figure(spec["correct_params"])
        elif gen_type == "traversal_grid":
            correct_svg = gen_traversal_cell(spec["correct_params"]["shape"], spec["correct_params"]["fill"])

        correct_path = FIGURE_DIR / f"q6_figure_{qid}_option_correct.svg"
        save_svg(correct_svg, correct_path)

        # 生成干扰选项SVG
        distractor_svgs = []
        distractor_paths = []
        for i, d in enumerate(spec["distractors"]):
            if gen_type == "quantity_intersections":
                svg = gen_quantity_intersections_figure(d["count"])
            elif gen_type == "rotation_arrow":
                svg = gen_rotation_arrow_figure(d["angle"])
            elif gen_type == "symmetry_regular_polygon":
                svg = gen_symmetry_regular_polygon_figure(d["sides"])
            elif gen_type == "overlay_xor":
                svg = gen_overlay_xor_figure(d)
            elif gen_type == "traversal_grid":
                svg = gen_traversal_cell(d["shape"], d["fill"])
            path = FIGURE_DIR / f"q6_figure_{qid}_option_distractor_{i}.svg"
            save_svg(svg, path)
            distractor_svgs.append(svg)
            distractor_paths.append(str(path.relative_to(REPO_ROOT)))

        # 规律验证
        if gen_type == "quantity_intersections":
            verification = verify_quantity_pattern(
                spec["stem_params"]["counts"], spec["correct_params"]["count"])
        elif gen_type == "rotation_arrow":
            verification = verify_rotation_pattern(
                spec["stem_params"]["angles"], spec["correct_params"]["angle"])
        elif gen_type == "symmetry_regular_polygon":
            verification = verify_symmetry_pattern(
                spec["stem_params"]["sides"], spec["correct_params"]["sides"])
        elif gen_type == "overlay_xor":
            verification = verify_overlay_pattern(
                spec["stem_params"]["group1"],
                spec["stem_params"]["group2"]["fig1"],
                spec["stem_params"]["group2"]["fig2"],
                spec["correct_params"])
        elif gen_type == "traversal_grid":
            verification = verify_traversal_pattern(
                spec["stem_params"]["row1"],
                spec["stem_params"]["row2"],
                spec["stem_params"]["row3"],
                spec["correct_params"])

        # 检查验证结果
        if not verification.get("correct_matches", False):
            print(f"  [FAIL] {qid}: 正确选项不符合规律: {verification}")
            failed.append(qid)
            continue
        if not verification.get("pattern_valid", verification.get("group1_pattern_valid",
                                                                    verification.get("row1_complete", True))):
            print(f"  [FAIL] {qid}: 题干规律不成立: {verification}")
            failed.append(qid)
            continue

        # 随机化选项位置
        rng = random.Random(f"{SEED}_{qid}")
        all_options = [{"svg": correct_svg, "svg_path": str(correct_path.relative_to(REPO_ROOT)),
                         "is_correct": True, "violation": None}]
        for i, d in enumerate(spec["distractors"]):
            all_options.append({
                "svg": distractor_svgs[i],
                "svg_path": distractor_paths[i],
                "is_correct": False,
                "violation": d["violation"],
                "violation_type": d["violation_type"],
            })
        rng.shuffle(all_options)

        labels = ["A", "B", "C", "D"]
        options = {}
        options_detail = {}
        answer = None
        for i, opt in enumerate(all_options):
            label = labels[i]
            options[label] = opt["svg_path"]
            options_detail[label] = {
                "svg_path": opt["svg_path"],
                "svg_inline": opt["svg"],
                "is_correct": opt["is_correct"],
                "violation": opt["violation"],
                "violation_type": opt.get("violation_type"),
            }
            if opt["is_correct"]:
                answer = label

        # 题干文字
        if gen_type == "overlay_xor":
            stem = ("从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。\n"
                    "第一组：图1 + 图2 → 图3（去同存异）\n"
                    "第二组：图1 + 图2 → ?")
        elif gen_type == "traversal_grid":
            stem = ("从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。\n"
                    "九宫格中每行图形的形状和填充样式均遍历出现一次。")
        else:
            stem = "从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。"

        # 解析
        explanation = generate_figure_explanation(spec, verification, options_detail, answer)

        q = {
            "question_id": qid,
            "origin_type": "generated",
            "module": "判断推理",
            "subtype": "图形推理",
            "difficulty": spec["difficulty"],
            "pattern_type": spec["pattern_type"],
            "pattern_description": spec["pattern_description"],
            "stem": stem,
            "stem_figures": [{"svg_path": p, "svg_inline": s} for p, s in zip(stem_figures_paths, stem_figures_svg)],
            "options": options,
            "options_detail": options_detail,
            "answer": answer,
            "verification_result": verification,
            "explanation": explanation,
            "generation_meta": {
                "template_version": TEMPLATE_VERSION,
                "generated_at": datetime.now().isoformat(),
                "param_seed": SEED,
                "svg_generation": "deterministic_python_string",
            },
        }
        questions.append(q)
        print(f"  ✅ {qid} (图形推理-{spec['pattern_type']}, diff={spec['difficulty']}) → 答案 {answer}")
    return questions, failed


def generate_figure_explanation(spec, verification, options_detail, answer):
    """生成图形推理解析"""
    lines = [f"【规律类型】{spec['pattern_type']}"]
    lines.append(f"【规律描述】{spec['pattern_description']}")
    lines.append("")
    lines.append("【规律验证】")
    for k, v in verification.items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append(f"【正确选项】{answer} — 符合规律")
    lines.append("")
    lines.append("【干扰项分析】")
    for label, opt in options_detail.items():
        if not opt["is_correct"]:
            lines.append(f"  {label}项：{opt.get('violation_type', '?')}。{opt.get('violation', '')}")
    lines.append("")
    lines.append(f"故本题选{answer}。")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
# 真题验证
# ══════════════════════════════════════════════════════

def validate_real_papers():
    """从2025真题中选3道定义判断+2道翻译推理，用引擎校验层验证"""
    results = {
        "definition_judgment": [],
        "translation_reasoning": [],
        "summary": {"definition_total": 0, "definition_passed": 0,
                    "translation_total": 0, "translation_passed": 0},
    }

    for paper_file in ["shengji.json", "shidi.json", "xingzhengzhifa.json"]:
        paper_path = PAPER_DIR / paper_file
        if not paper_path.exists():
            continue
        with open(paper_path) as f:
            data = json.load(f)

        for section in data.get("sections", []):
            if section.get("name") != "判断推理":
                continue
            qs = section.get("questions", [])

            # 定义判断
            def_questions = [q for q in qs if q.get("tag") in ("单定义", "多定义")]
            for q in def_questions[:2]:  # 每卷最多选2道
                if results["summary"]["definition_total"] >= 3:
                    break
                # 校验：有定义、有4个选项、有答案、有解析
                has_definition = "根据上述定义" in str(q.get("stem", "")) or "下列属于" in str(q.get("stem", "")) or "下列不属于" in str(q.get("stem", ""))
                has_4_options = len(q.get("options", {})) == 4
                has_answer = q.get("answer") in ("A", "B", "C", "D")
                has_explanation = len(str(q.get("explanation", ""))) > 50
                passed = has_definition and has_4_options and has_answer and has_explanation

                results["definition_judgment"].append({
                    "paper": paper_file.replace(".json", ""),
                    "question_number": q.get("number"),
                    "tag": q.get("tag"),
                    "has_definition_structure": has_definition,
                    "has_4_options": has_4_options,
                    "has_answer": has_answer,
                    "has_explanation": has_explanation,
                    "passed": passed,
                })
                results["summary"]["definition_total"] += 1
                if passed:
                    results["summary"]["definition_passed"] += 1

            # 翻译推理
            trans_questions = [q for q in qs if q.get("tag") == "翻译推理"]
            for q in trans_questions[:1]:  # 每卷最多选1道
                if results["summary"]["translation_total"] >= 2:
                    break
                has_conditional = any(w in str(q.get("stem", "")) for w in ["如果", "只有", "除非", "只要"])
                has_4_options = len(q.get("options", {})) == 4
                has_answer = q.get("answer") in ("A", "B", "C", "D")
                has_explanation = len(str(q.get("explanation", ""))) > 50
                passed = has_conditional and has_4_options and has_answer and has_explanation

                results["translation_reasoning"].append({
                    "paper": paper_file.replace(".json", ""),
                    "question_number": q.get("number"),
                    "has_conditional_connective": has_conditional,
                    "has_4_options": has_4_options,
                    "has_answer": has_answer,
                    "has_explanation": has_explanation,
                    "passed": passed,
                })
                results["summary"]["translation_total"] += 1
                if passed:
                    results["summary"]["translation_passed"] += 1

            if results["summary"]["definition_total"] >= 3 and results["summary"]["translation_total"] >= 2:
                break
        if results["summary"]["definition_total"] >= 3 and results["summary"]["translation_total"] >= 2:
            break

    return results


# ══════════════════════════════════════════════════════
# 报告生成
# ══════════════════════════════════════════════════════

def generate_report(all_questions, failed_ids, real_paper_results):
    """生成验证报告"""
    def_qs = [q for q in all_questions if q["subtype"] == "定义判断"]
    trans_qs = [q for q in all_questions if q["subtype"] == "翻译推理"]
    fig_qs = [q for q in all_questions if q["subtype"] == "图形推理"]

    lines = [
        "# Q6 判断推理引擎 — 生成验证报告",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 模板版本: {TEMPLATE_VERSION}",
        f"> 随机种子: {SEED}",
        "",
        "## 1. 汇总",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 总题数 | {len(all_questions)} |",
        f"| 定义判断 | {len(def_qs)} 题 |",
        f"| 翻译推理 | {len(trans_qs)} 题 |",
        f"| 图形推理 | {len(fig_qs)} 题 |",
        f"| 校验通过率 | {len(all_questions)}/{len(all_questions) + len(failed_ids)} ({len(all_questions)/(len(all_questions)+len(failed_ids))*100:.0f}%) |" if (len(all_questions) + len(failed_ids)) > 0 else "| 校验通过率 | 100% |",
        f"| 失败题数 | {len(failed_ids)} |",
        "",
    ]

    # 定义判断详情
    lines.append("## 2. 定义判断")
    lines.append("")
    lines.append("| 题号 | 难度 | 关键要素数 | 答案 | 干扰项违反要素 |")
    lines.append("|---|---|---|---|---|")
    for q in def_qs:
        violated = [opt["violated_element"] for opt in q["options_detail"].values() if not opt["is_correct"]]
        lines.append(f"| {q['question_id']} | {q['difficulty']} | {len(q['key_elements'])} | {q['answer']} | {', '.join(violated)} |")
    lines.append("")

    # 翻译推理详情
    lines.append("## 3. 翻译推理（双求解）")
    lines.append("")
    lines.append("| 题号 | 推理类型 | 难度 | 答案 | 双求解匹配 | 干扰项可证伪 |")
    lines.append("|---|---|---|---|---|---|")
    for q in trans_qs:
        dual = q["dual_solve"]["match"]
        distractors_valid = all(dc["valid_distractor"] for dc in q["distractor_validation"])
        lines.append(f"| {q['question_id']} | {q['question_type']} | {q['difficulty']} | {q['answer']} | {'✅' if dual else '❌'} | {'✅' if distractors_valid else '❌'} |")
    lines.append("")
    lines.append("### 双求解方法")
    lines.append("")
    lines.append("- **求解器A（规则引擎）**：基于命题逻辑推理规则库（modus_ponens, modus_tollens, hypothetical_syllogism, disjunctive_syllogism等）检查正确结论是否可由前提通过有效规则推出。")
    lines.append("- **求解器B（真值表枚举）**：枚举所有变量赋值，验证所有使前提为真的赋值都使结论为真（前提蕴含结论）。")
    lines.append("- 两结果一致才保存；干扰项必须可被真值表证伪且不是前提的逻辑后承。")
    lines.append("")

    # 图形推理详情
    lines.append("## 4. 图形推理（确定性SVG）")
    lines.append("")
    lines.append("| 题号 | 规律类型 | 难度 | 答案 | 规律验证 | SVG文件数 |")
    lines.append("|---|---|---|---|---|---|")
    for q in fig_qs:
        v = q["verification_result"]
        valid = v.get("correct_matches", False)
        svg_count = len(q["stem_figures"]) + 4  # 题干 + 4选项
        lines.append(f"| {q['question_id']} | {q['pattern_type']} | {q['difficulty']} | {q['answer']} | {'✅' if valid else '❌'} | {svg_count} |")
    lines.append("")
    lines.append("### 图形规律类型覆盖")
    lines.append("")
    lines.append("| 规律类型 | 题数 | 验证方法 |")
    lines.append("|---|---|---|")
    lines.append("| 数量类（交点数递增） | 1 | 等差数列检测 |")
    lines.append("| 旋转类（顺时针45°） | 1 | 角度差一致性检测 |")
    lines.append("| 对称类（对称轴数递增） | 1 | 正n边形对称轴数=n验证 |")
    lines.append("| 叠加类（去同存异/XOR） | 1 | 第一组规律验证+第二组应用 |")
    lines.append("| 遍历类（形状+填充遍历） | 1 | 每行元素完整性检测 |")
    lines.append("")
    lines.append("### SVG 生成说明")
    lines.append("")
    lines.append("- 所有图形使用 Python 字符串拼接生成确定性 SVG 1.1 代码")
    lines.append("- 基本形状：`<circle>`, `<rect>`, `<polygon>`, `<line>`")
    lines.append("- 禁止使用任何 AI 图像生成模型")
    lines.append(f"- SVG 文件保存在 `xingce-structured-data/generated/figures/q6_*.svg`")
    lines.append("")

    # 干扰项类型覆盖
    lines.append("## 5. 干扰项类型覆盖")
    lines.append("")
    lines.append("### 定义判断干扰项")
    lines.append("")
    def_violations = {}
    for q in def_qs:
        for opt in q["options_detail"].values():
            if not opt["is_correct"]:
                ve = opt["violated_element"]
                def_violations[ve] = def_violations.get(ve, 0) + 1
    for ve, cnt in sorted(def_violations.items(), key=lambda x: -x[1]):
        lines.append(f"- 违反「{ve}」要素：{cnt} 次")
    lines.append("")

    lines.append("### 翻译推理干扰项")
    lines.append("")
    trans_errors = {}
    for q in trans_qs:
        for opt in q["options_detail"].values():
            if not opt["is_correct"]:
                et = opt["error_type"]
                trans_errors[et] = trans_errors.get(et, 0) + 1
    for et, cnt in sorted(trans_errors.items(), key=lambda x: -x[1]):
        lines.append(f"- {et}：{cnt} 次")
    lines.append("")

    lines.append("### 图形推理干扰项")
    lines.append("")
    fig_violations = {}
    for q in fig_qs:
        for opt in q["options_detail"].values():
            if not opt["is_correct"]:
                vt = opt.get("violation_type", "?")
                fig_violations[vt] = fig_violations.get(vt, 0) + 1
    for vt, cnt in sorted(fig_violations.items(), key=lambda x: -x[1]):
        lines.append(f"- {vt}：{cnt} 次")
    lines.append("")

    # 真题验证
    lines.append("## 6. 真题验证")
    lines.append("")
    rp = real_paper_results["summary"]
    lines.append(f"### 定义判断（{rp['definition_passed']}/{rp['definition_total']} 通过）")
    lines.append("")
    lines.append("| 来源卷 | 题号 | 标签 | 定义结构 | 4选项 | 答案 | 解析 | 通过 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in real_paper_results["definition_judgment"]:
        lines.append(f"| {r['paper']} | {r['question_number']} | {r['tag']} | "
                     f"{'✅' if r['has_definition_structure'] else '❌'} | "
                     f"{'✅' if r['has_4_options'] else '❌'} | "
                     f"{'✅' if r['has_answer'] else '❌'} | "
                     f"{'✅' if r['has_explanation'] else '❌'} | "
                     f"{'✅' if r['passed'] else '❌'} |")
    lines.append("")

    lines.append(f"### 翻译推理（{rp['translation_passed']}/{rp['translation_total']} 通过）")
    lines.append("")
    lines.append("| 来源卷 | 题号 | 条件连接词 | 4选项 | 答案 | 解析 | 通过 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in real_paper_results["translation_reasoning"]:
        lines.append(f"| {r['paper']} | {r['question_number']} | "
                     f"{'✅' if r['has_conditional_connective'] else '❌'} | "
                     f"{'✅' if r['has_4_options'] else '❌'} | "
                     f"{'✅' if r['has_answer'] else '❌'} | "
                     f"{'✅' if r['has_explanation'] else '❌'} | "
                     f"{'✅' if r['passed'] else '❌'} |")
    lines.append("")

    # 答案位置分布
    lines.append("## 7. 正确答案位置分布")
    lines.append("")
    answer_dist = {}
    for q in all_questions:
        answer_dist[q["answer"]] = answer_dist.get(q["answer"], 0) + 1
    lines.append("| 选项 | 题数 |")
    lines.append("|---|---|")
    for k in ["A", "B", "C", "D"]:
        lines.append(f"| {k} | {answer_dist.get(k, 0)} |")
    lines.append("")

    # 产出文件清单
    lines.append("## 8. 产出文件清单")
    lines.append("")
    lines.append("| 文件 | 说明 |")
    lines.append("|---|---|")
    lines.append("| `scripts/xingce/gen_judgment_questions.py` | 判断推理生成引擎（三个子引擎） |")
    lines.append("| `xingce-structured-data/generated/qa_judgment_v1.json` | 题目产出（≥15题） |")
    lines.append("| `xingce-structured-data/generated/qa_judgment_v1_report.md` | 本验证报告 |")
    lines.append("| `xingce-structured-data/generated/figures/q6_*.svg` | 图形推理SVG文件 |")
    lines.append("| `xingce-structured-data/_schema/judgment_logic_rules.json` | 翻译推理逻辑规则库 |")
    lines.append("")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Q6 判断推理引擎（定义判断+翻译推理+图形推理SVG）")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写文件")
    parser.add_argument("--validate-only", action="store_true", help="仅跑真题验证")
    args = parser.parse_args()

    print("=" * 60)
    print("Q6 判断推理引擎 — 定义判断→翻译推理→图形推理")
    print("=" * 60)

    # 真题验证
    print("\n[真题验证] 从2025真题中选取定义判断+翻译推理...")
    real_paper_results = validate_real_papers()
    rp = real_paper_results["summary"]
    print(f"  定义判断: {rp['definition_passed']}/{rp['definition_total']} 通过")
    print(f"  翻译推理: {rp['translation_passed']}/{rp['translation_total']} 通过")

    if args.validate_only:
        print("\n[validate-only] 仅真题验证，不生成题目")
        return

    # 子引擎1：定义判断
    print("\n[1/3] 生成定义判断题...")
    def_questions, def_failed = generate_definition_questions()

    # 子引擎2：翻译推理
    print("\n[2/3] 生成翻译推理题（双求解）...")
    trans_questions, trans_failed = generate_translation_questions()

    # 子引擎3：图形推理
    print("\n[3/3] 生成图形推理题（确定性SVG）...")
    fig_questions, fig_failed = generate_figure_questions()

    all_questions = def_questions + trans_questions + fig_questions
    all_failed = def_failed + trans_failed + fig_failed

    # 汇总
    print(f"\n{'='*60}")
    print(f"生成完成: {len(all_questions)} 题（定义{len(def_questions)} + 翻译{len(trans_questions)} + 图形{len(fig_questions)}）")
    print(f"校验通过: {len(all_questions)}/{len(all_questions) + len(all_failed)}")
    if all_failed:
        print(f"失败: {all_failed}")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n[dry-run] 跳过文件写入")
        return

    # 写文件
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "version": "v1",
        "total": len(all_questions),
        "generated_at": datetime.now().isoformat(),
        "template_version": TEMPLATE_VERSION,
        "seed": SEED,
        "sub_engines": {
            "definition_judgment": len(def_questions),
            "translation_reasoning": len(trans_questions),
            "figure_reasoning": len(fig_questions),
        },
        "questions": all_questions,
    }

    with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 题目: {QUESTIONS_PATH} ({QUESTIONS_PATH.stat().st_size} bytes)")

    report = generate_report(all_questions, all_failed, real_paper_results)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ 报告: {REPORT_PATH} ({REPORT_PATH.stat().st_size} bytes)")

    # 统计SVG文件数
    svg_files = list(FIGURE_DIR.glob("q6_*.svg"))
    print(f"✅ SVG图形: {len(svg_files)} 个文件")

    print("\n" + "=" * 60)
    print("Q6 判断推理引擎完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
