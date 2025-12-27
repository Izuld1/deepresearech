"""
steps/stepX_write_paragraph.py
------------------------------

Step X: Evidence-Bound Paragraph Writing（基于证据池的分段写作）

职责：
- 对每一个【已裁决保留的子目标 / section】
- 仅基于其 evidence_pool 生成对应正文段落
- 不引入任何外部知识或未检索到的信息

设计原则：
- LLM 只负责“受限表达与归纳”
- 系统负责边界约束、失败兜底与稳定性
- 输出为稳定 contract，供后续 report assemble 使用
"""

from typing import Dict, Any, List
import re

from core.llm_gateway import LLMGateway


# =========================
# 1) Prompt
# =========================

SYSTEM_EVIDENCE_BOUND_WRITER = """
你是“Evidence-Bound Academic Writer（基于证据的学术写作者）”。

你的唯一任务是：
- 基于【给定证据池】为【指定段落标题】撰写对应学术正文段落。

必须严格遵守以下硬性规则（违反任一条均视为错误）：
1. 只能使用证据池中明确出现的信息
2. 不得引入任何外部背景知识、常识性补充或推断性结论
3. 不得扩展证据池中未出现的分类体系、机制或定义
4. 不得使用“通常认为 / 普遍认为 / 一般来说”等泛化表达
5. 不得出现临床建议、总结性判断或未来研究展望
6. 不得引用证据池中未明确出现的作者、年份或文献
7. 所有陈述必须能在证据池中找到直接或间接依据

写作风格要求：
- 学术论文正文风格
- 客观、中性、描述性
- 允许归纳，但不允许外推
""".strip()


USER_EVIDENCE_BOUND_WRITER = """
【段落标题】
{section_title}

【证据池（仅此可用）】
{evidence_pool}

请严格按照以下 JSON 格式输出（字段不可增减）：

{{
  "content": str
}}
""".strip()


# =========================
# 2) 核心函数
# =========================

def write_evidence_bound_paragraph(
    gateway: LLMGateway,
    section_title: str,
    evidence_pool: List[Dict[str, Any]],
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    输入：
      - section_title: 当前段落标题
      - evidence_pool: 已裁决的证据池

    输出：
      - paragraph object（稳定 contract）
    """

    # -------- 1. 证据池序列化 --------
    serialized = []
    for idx, ev in enumerate(evidence_pool, start=1):
        text = ev.get("text", "").strip()
        source = ev.get("source", "").strip()
        if text:
            serialized.append(
                f"[Evidence {idx} | Source: {source}]\n{text}"
            )

    evidence_text = "\n\n".join(serialized)

    # -------- 2. 构造 messages --------
    messages = [
        {"role": "system", "content": SYSTEM_EVIDENCE_BOUND_WRITER},
        {
            "role": "user",
            "content": USER_EVIDENCE_BOUND_WRITER.format(
                section_title=section_title,
                evidence_pool=evidence_text,
            ),
        },
    ]

    # -------- 3. 按 Step2 规范调用 Gateway --------
    result = gateway.ask_json(messages, timeout=timeout)

    paragraph_text = result.get("content", "").strip()

    # -------- 4. 系统级兜底检查 --------
    # _basic_style_guard(paragraph_text)

    return {
        "section_title": section_title,
        "content": paragraph_text,
        "status": "generated",
    }


# =========================
# 3) 风格与越界防护
# =========================

FORBIDDEN_PATTERNS = [
    r"普遍认为",
    r"一般来说",
    r"通常认为",
    r"提示",
    r"建议",
    r"未来研究",
    r"有助于",
    r"因此可以",
    r"这表明",
]


def _basic_style_guard(text: str) -> None:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            raise ValueError(
                f"Forbidden pattern detected: {pattern}"
            )

    if len(text) < 150:
        raise ValueError("Paragraph too short.")

    if len(text) > 600:
        raise ValueError("Paragraph too long.")


def generate_paragraphs_for_sub_goals(
    gateway: LLMGateway,
    result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    输入：
      - gateway: 外部构建好的 LLMGateway
      - result: 上游步骤产出的完整 result（包含 sub_goal_results）

    输出：
      - paragraphs: List[Dict]
    """

    paragraphs: List[Dict[str, Any]] = []

    sub_goal_results = result.get("sub_goal_results", [])

    for idx, sub_goal in enumerate(sub_goal_results, start=1):
        # -------- 基本字段提取 --------

        section_title = sub_goal.get("intent", "").strip()
        sub_goal_id = sub_goal.get("sub_goal_id", "")
        parent_section_id = sub_goal.get("parent_section_id", "")
        pool = (
            sub_goal
            .get("result", {})
            .get("pool", {})
            .get("contexts", [])
        )

        # -------- 兜底：无证据直接跳过 --------
        if not section_title or not pool:
            paragraphs.append({
                "sub_goal_id": sub_goal_id,
                "parent_section_id": parent_section_id,
                "section_title": section_title,
                "status": "skipped",
                "reason": "empty section_title or evidence_pool",
                "content": "",
            })
            continue

        # -------- 调用单段写作 --------
        paragraph = write_evidence_bound_paragraph(
            gateway=gateway,
            section_title=section_title,
            evidence_pool=pool,
        )

        # -------- 统一补充元信息 --------
        paragraphs.append({
            "sub_goal_id": sub_goal_id,
            "parent_section_id": parent_section_id,
            "section_title": section_title,
            "status": paragraph.get("status", "generated"),
            "content": paragraph.get("content", ""),
        })

    return paragraphs



if __name__ == "__main__":
    # gateway = LLMGateway(model="gpt-5.2")

    # section_title = "腕骨骨折的临床分类体系及其对应的解剖学基础"

    # paragraph = write_evidence_bound_paragraph(
    #     gateway=gateway,
    #     section_title=section_title,
    #     evidence_pool="[{'text': '1 材料与方法\n1.1 一般资料\n选取2016 年1 月-2022 年12月期间山西医科大学第二医院骨科就诊的791 例桡 骨远端骨折患者为研究对象，统计患者的年龄、性别、损伤能量、有无骨质疏松、桡 骨远端骨折类型等信息，就其发病特点和临床诊断进行回顾性分析。\n纳入标准：1.符合桡骨远端骨折的诊断标准；2.一般资料完整并签署知情同意书； 3. 影像学资料完整。\n排除标准：1.X线或CT缺失的患者；2.曾有同侧腕骨骨折手术既往史；3.其他原 因引起的腕骨骨折（如病理性骨折等）。\n1.2 研究方法和内容\n收集来自山西医科大学第二医院自2016 年1 月1 日至2022 年12 月31 日期间 就诊的桡骨远端骨折患者的临床资料，包含年龄、性别、受伤机制、以及影像学等资 料，共计791 例。详细收集患者桡骨远端骨折类型、有无骨质疏松、受伤能量等信息， 讨论以下内容：\n①桡骨远端骨折伴发腕骨骨折的发病率及其特点；', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '山西医科大学\n硕士学位论文\n桡骨远端骨折合并腕骨骨折的发病率及危险因素分析\nTo analyze the incidence and risk factors of distal radius fractures combined with carpal fractures\n研究生：赵潇雄 指导教师：常文凯主任医师 专业名称：骨科 研究方向：骨显微手外科 学位类型：专业学位 所在学院： 第二临床学院\n中国山西\n二〇二三年三月二十五日\n 分类号：R683 \n 学校代码：10114 \n 密级：公开\n 学号：202000230470 \n桡骨远端骨折合并腕骨骨折的发病率及危险因素分析\nTo analyze the incidence and risk factors of distal radius fractures combined with carpal fractures\n研究生：赵潇雄 指导教师：常文凯主任医师 专业名称：骨科 研究方向：骨显微手外科 学位类型：专业学位 所在学院：第二临床学院\n中国山西\n二O二三年三月二十五日\n目录\n前言.. 1 材料与方法. 2 1.1 一般资料.. 2 1.2 研究方法和内容.. 2 1.3 统计学处理.. 3\n2 结果.... 4 \n2.1 桡骨远端骨折伴腕骨骨折的发病率及其特点. 4 \n2.2 桡骨远端骨折伴发腕骨骨折的危险因素.. 5 2.2.1 桡骨远端骨折伴腕骨骨折相关风险单因素分析. 6 2.2.2 桡骨远端骨折伴腕骨骨折相关风险多因素分析.. 6 2.2.3 危险因素对桡骨远端骨折伴腕骨骨折预测价值 7', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '3 讨论... 9 \n3.1 桡骨远端骨折伴腕骨的发病率及其特点.. 9 \n3.2 桡骨远端骨折伴发腕骨骨折的危险因素\n.. 10 \n4 结论.. 13 参考文献.. 14 综述月骨无菌性坏死的治疗进展... 16 参考文献.......\n. 25\n桡骨远端骨折合并腕骨骨折的发病率及危险因素分析\n摘要\n目的：\n研究桡骨远端骨折患者伴发腕骨骨折的发病率和特点，探讨桡骨远端骨折伴发 腕骨骨折的危险因素。\n方法：\n收集我院骨科自2016年1月1日到2022年12月31日期间所有桡骨远端骨折 患者的基本资料，包含年龄、性别、受伤机制、以及影像学等资料，共计791 例。\n详细收集桡骨远端骨折患者的骨折类型、有无骨质疏松、受伤能量等信息，讨论以 下内容：\n①桡骨远端骨折伴发腕骨骨折的发病率及其特点；\n②各种因素对桡骨远端骨折伴发腕骨骨折的影响。\n结果：\n最终纳入791 例桡骨远端骨折患者，其中50 例患者同时伴有腕骨骨折，发病 率为6.32%。50 例患者中，男性33 例，女性17 例，年龄10~88岁，平均年龄（48.2 ±16.4）岁。其中合并舟状骨骨折的有38例（76.0%）；合并月骨骨折的有10例（20%）； 合并三角骨骨折的有6 例（12.0%）；合并豆状骨骨折的有1 例（2.0%）：合并大 多角骨骨折的有2 例（4.0%）；合并小多角骨骨折的有1 例（2.0%）；合并钩骨骨 折的有3 例（6.0%）；无合并头状骨骨折的患者（0%）。此外，与桡骨远端骨折相 关的腕骨骨折有97%发生于近端腕骨。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '为了进一步探讨AO分型为B型、高能量损伤以及骨质疏松对桡骨远端骨折伴腕 骨骨折的预测价值，我们绘测了AO分型为B型，高能量损伤以及骨质疏松的ROC 曲线。结果显示三者的AUC值分别为0.721、0.748、0.742。其中，AO分型为B型 的灵敏度为76.00%，特异度为68.15%；高能量损伤的灵敏度为84.00%，特异度为 65.59%；骨质疏松的灵敏度为60.00%，特异度为88.39%，三者联合的AUC值为0.908。\n三者在预测桡骨远端骨折伴腕骨骨折的灵敏度和特异度各占优势，三者联合可以互相 补充，并可以提高诊断效能。\n本文的局限性：1.部分石膏固定保守治疗的患者未行CT检查，一些腕骨骨折可\n能会在X线检查种漏诊。其次，AO分型为B型和C型的骨折患者CT的使用率要高 于AO分型为A型的骨折患者，具有一定的选择偏倚。2. 本研究为单中心回顾性研 究，仍需大量、前瞻性的研究进一步证明我们的结论。\n4 结论\n1.桡骨远端骨折伴腕骨骨折的发生率较低，临床上极易漏诊应予以重视。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '3.2 桡骨远端骨折伴发腕骨骨折的危险因素\n本研究发现，桡骨远端骨折伴腕骨骨折的发生与高能量损伤、AO分型为B型、 伴有骨质疏松具有统计学意义（P<0.05），而与性别和年龄差异无统计学意义 （P>0.05）。后将AO分型为B型、伴有骨质疏松、高能量损伤纳入多因素Logsitic 回归分析后发现，三者均为桡骨远端骨折伴腕骨骨折发生的独立危险因素。上述结果 提示，若桡骨远端骨折的患者AO分型为B型，同时伴有骨质疏松，且受伤机制为高 能量损伤，应予以腕关节CT或MRI 检查，警惕腕骨骨折的发生。\n临床上桡骨远端骨折分型有多种，传统上有以人名分类[23-24]：爱尔兰医师Colles\n于1814 年第一次报道伸直型桡骨远端骨折，亦称Colles 骨折；英格兰医师Smith 于 1847年第一次报道屈曲型桡骨远端骨折，亦称Smith 骨折；美国医师Barton于1938 年第一次报道累及桡骨远端关节面同时伴腕关节半脱位的骨折，亦称Barton 骨折； 骨科医师Frykman于1976 年提出Frykman分型，此类型强调了桡腕关节和桡尺关节 的重要性。20 世纪90 年代AO组织提出新的分型，此分型主要根据桡骨远端骨折的 严重程度进行分类：A型为关节外骨折，B型为部分关节骨折；C型为关节内骨折。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': 'Galley等［13］根据头状骨到三角骨中立位的最短 距离（距离）对月骨进行分型，距离 为型C-月T骨，距离为C型-T月骨，≤2 m距m ⅠC-T≥4 mmⅡC-T>2 mm且<4 mm为中间组位。Borgese等［14］回顾性 地对223 个腕关节进行了X线片和磁共振成像 （MRI）检查，发现月骨形态、性别及月三角骨间韧带 损伤状态均对距离有显著影响：拥有型月骨 者、男性和伴有C-月T三角骨间韧带损伤者的Ⅱ腕关节 距离分别大于拥有型月骨者、女性和无月三 C角-骨T间韧带损伤者的腕关Ⅰ节。\n1.2\u3000血供\u3000\n月骨的血液供应主要来源于周围韧带内的滋 养血管。罗映晖等［15］认为，多数月骨由掌、背侧两 组动脉系统进行血液供应，掌侧的动脉是月骨的主 要血供来源，由于掌侧动脉的周围环境不利于损伤月骨骨折分为部分骨折、掌侧或背侧骨折、完全骨 后修复，因此，他们认为月骨掌侧的动脉损害可能折、水平压迫骨折。等［28］根据骨折不稳 是月骨缺血性坏死的主要原因。然而，王大伟等［16］定程度将月骨骨折分S为hu无nm移ug位am型、半脱位型和脱位 对8例新鲜成人上肢标本进行血管灌注试验，发现型，认为此种分类有助于了解这些罕见损伤的频谱', 'source': '月骨骨折的治疗进展_阿卜杜热依木·阿卜杜克热木.pdf'}, {'text': '此分型详细的描述了骨折线与关节面的关系，对骨折做出全面评估和治疗指导。本研 究发现AO分型为B型是桡骨远端骨折伴腕骨骨折的危险因素。桡骨远端有3 个关节 面，分别为位于桡背侧的舟骨关节面、尺掌侧的月骨关节面以及垂直两者的乙状切迹。\n故当腕关节着地桡偏且过度背伸时，桡骨远端发生关节内骨折，近排腕骨与骨折块受 力不均匀，舟状骨所承受的负荷最大且最容易发生骨折。故AO分型为B型的桡骨远 端骨折易合并舟骨骨折。\n本研究发现高能量损伤和骨质疏松也是桡骨远端骨折伴腕骨骨折的独立危险因 素。高能量损伤一般指交通事故、1.5 米以上的高处坠落、运动、工业事故以及重物 击打所造成的损伤。而骨质疏松是人类常见的骨骼疾病，其特征是骨量减少和骨小梁 等结构退行性变，最终导致骨密度降低，脆性增大，低能量骨折的风险增加。据文献 报道，全球约有2 亿女性患有骨质疏松症，年龄50 岁以上的女性约有三分之一可能 会发生与骨质疏松症相关的骨折，而年龄50 岁以上的男性约有五分之一可能发生与 骨质疏松症相关的骨折[25-26]。与骨质疏松症有关的骨折常发生于腰椎、髋关节和腕关 节。当腕部受到较高能量的外力时，腕骨及腕间韧带极易受到损伤。若同时合并有骨 质疏松，则腕骨骨折的风险会明显增高。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '【关键词】腕骨骨折诊断显微外科手术治疗结果\nDiagnosis and treatment of carpal scaphoid fracture Lu Laij in，L iu Zhigang，Nakamura，et al．Depar-t ment of H and Surgery，The First Teaching H osp ital of Norman Bethune University of Medical Sciences， Changchun130021\n【Abstract】Objective e -To investigate the effective method ，to reduce the erronous diagnostic rat． aMned thinocdisd ence of nonunion of the carpal scaphoid -fractures（CSF）a，nd c，hoose ，the standard management 59cases of CSF were diagnosed by Xray examinationsCTMRIarthrography and isotopicscanning of the wrist，and were treated by8methods，namely，non-operation，cross Kirschner w ire fixa- tion ，free bone grafting w ith Kirschner w ire fixation ，vascularized radial bone grafting based on the dor- sal branch of anterior interosseous artery，Herbert’s screw fixation w ith or w ithout wedge bone grafting， osteotomy of necrosed proximal scaphoid and tendon bulb embedding，proximal carpectomy，and radio- ．．Results carpal fusionThe treatment outcome and the i％nd．ications of these procedures were com，pare-d Clinical correct diagnostic rate of CSF was100In8cases of conservative treatmentnonunion werefound in4．All 55cases receiving surgical treatment got osseous union，but 4cases had shortening and ．Conclusions -- DISI deform％ities4position Xray ．examinations combined w ith bilateral comparisoniagnosing the achieved95diagnostic rate for scaphoid fracture CT and MRI played a critical role in dfract．’as ser pr．\nu【rKe eiy n weoarrdly s】a nd late stageHerberts scrCarpal bone Fracture fixation wDiagnosis ew\n腕舟骨骨折在腕骨骨折中最为多见，［1］报告 其占全部腕骨骨折的％，多由交通事故D和u运nn动性损 伤所致。由于其特殊的82解剖位置、功能、供血特点和目 前诊断技术的限制，在临床诊断和治疗效果上尚存在 较多问题亟待解决：如新鲜腕舟骨骨折的漏诊，晚期腕 舟骨骨不连、骨坏死、腕关节不稳等并发症的多发，临 床固定时间过长导致遗有腕关节疼痛和不同程度的功 能丧失等。在总结本院和作者在日本名古屋大学研修 时收治的例腕舟骨骨折临床资料的基础上，就其临 床诊断、新5诊9断技术的应用、治疗方法的选择和并发症 的治疗等，提出我们的观点和体会。', 'source': '腕舟骨骨折的临床诊断和治疗_路来金.pdf'}, {'text': '对单纯性桡骨远端骨折组和桡骨远端骨折伴腕骨骨折组进行相关性分析，发现 桡骨远端骨折与腕骨骨折同时发生与AO分型为B型、高能量损伤以及骨质疏松相 关，进一步纳入多因素logistic 分析结果提示：AO分型为B型（OR=14.532，95%CI：\n6.627~31.869）、高能量损伤（OR=9.749，95%CI：4.130~23.012）、合并有骨质疏松 （OR=8.099，95%CI：3.880~16.907）为桡骨远端骨折合并腕骨骨折发生的独立危 险因素。ROC曲线显示，高能量损伤预测桡骨远端骨折伴腕骨骨折的AUC为0.748 （95%CI 0.716-0.778，P<0.001）；AO分型为B型预测桡骨远端骨折伴腕骨骨折的 AUC为0.742（95%CI 0.710-0.772，P<0.001）；合并骨质疏松预测桡骨远端骨折伴 腕骨骨折的AUC为0.721（95%CI 0.688-0.752，P<0.001）；三者联合预测桡骨远端 骨折伴腕骨骨折的AUC为0.908（95% CI 0.886-0.927，P<0.001）。利用MedCalc 软件比较高能量损伤、AO分型为B型、合并骨质疏松以及三者联合预测桡骨远端 骨折伴腕骨骨折的AUC 值，结果示高能量损伤、AO分型为B型与合并骨质疏松 相比，三者间两两比较差异不具有统计学意义（P>0.05）,而三者联合的AUC值大 于高能量损伤（Z=4.967,P<0.001)、骨质疏松（Z=4.967,P<0.001）及AO 分型为B 型（Z=2.468，P<0.001)，差异具有统计学意义。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '将单因素分析中具有统计学意义的3 个相关因素进一步多因素分析以排除其他 混杂因素干扰，利logistic 回归分析模型进行分析，结果如下表（表4）。结果显示高 能量损伤（OR=9.749，95%CI：4.130~23.012）、AO分型为B型（OR=14.532，95%CI： 6.627~31.869）、合并有骨质疏松（OR=8.099，95%CI：3.880~16.907）为桡骨远端骨 折合并腕骨骨折发生的独立危险因素。\n2.2.3 危险因素对桡骨远端骨折伴腕骨骨折预测价值\n以所有入组患者为高能量损伤、AO分型为B型、合并骨质疏松与桡骨远端骨折 伴腕骨骨折发生关系绘制ROC曲线。结果显示高能量损伤诊断骨远端骨折伴腕骨骨 折的AUC为0.748（95%CI 0.716-0.778，P<0.001）；AO分型为B型诊断桡骨远端骨 折伴腕骨骨折的AUC为0.742（95%CI 0.710-0.772，P<0.001）；合并骨质疏松诊断骨 远端骨折伴腕骨骨折的AUC 为0.721（95%CI 0.688-0.752，P<0.001）；三者联合的 AUC为0.908（95% CI 0.886-0.927，P<0.001）。（表5，图2）。利用MedCalc 软件比 较高能量损伤、AO分型为B型、合并骨质疏松及三者联合预测桡骨远端骨折同时伴 腕骨骨折的AUC值，结果示高能量损伤、AO分型为B型、合并骨质疏松三者间两 两比较差异不具有统计学意义（P>0.05）, 三者联合的AUC 值大于高能量损伤 （Z=4.967,P<0.001)、骨质疏松（Z=4.967,P<0.001）及AO 分型为B 型（Z=2.468， P<0.001)，差异具有统计学意义。（表6）', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '2.2 桡骨远端骨折伴发腕骨骨折的危险因素\n本研究有50 例患者诊断为桡骨远端骨折合并腕骨骨折，其中男性33 例（33/50）， 年龄主要分布在30-60 岁之间（33/50），高损伤能量42 例（42/50），AO分型以B型 为主（37/50），骨质疏松患者20 例（20/50）。（详见表2）\n2.2.1桡骨远端骨折伴腕骨骨折相关风险单因素分析\n根据表2，50 例桡骨远端骨折伴腕骨骨折患者中，性别以男性为主，年龄以30-60 岁年龄段为主，AO分型以B型为主，且伴有骨质疏松的患者较多，将以上因素纳入 单因素logistic 回归，分析各因素与桡骨远端骨折伴腕骨骨折发生的相关性，结果如 下表2.3 显示，高能量损伤、AO分型为B型、伴有骨质疏松与桡骨远端骨折伴腕骨 骨折的发生相关，差异具有统计学意义（P<0.05），而与性别和年龄差异无统计学意 义（P>0.05）。(详见表3)\n2.2.2桡骨远端骨折伴腕骨骨折相关风险多因素分析', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '7\n3 讨论\n桡骨远端骨折在任何年龄段均较常见，若同时伴有严重骨质疏松发生骨折的风险 则更高[4]。其致病原因多为摔伤、高处坠落伤、重物击打和交通事故等。通常桡骨远 端骨折常伴有其他几种类型的损伤，包括尺骨远端骨折（6%-9%）、尺骨茎突骨折 （55-61%）、TFCC（39%-43%）、舟月韧带损伤（16%-40%）以及月三角骨韧带损伤 （9%-15%）[5-8]。然而，关于桡骨远端骨折伴发腕骨骨折的文献鲜有报道。由于桡骨 远端骨折伴发腕骨骨折在临床上的发病率不高，急性腕骨骨折在X 线移位显示不明 显、急诊工作性质等种种原因，明确桡骨远端骨折合并腕骨骨折的危险因素就显得尤 为重要。\n3.1 桡骨远端骨折伴腕骨的发病率及其特点\n组成腕关节的八块腕骨由近端向远端，由桡侧向尺侧分别为舟骨、月骨、三角骨、 豌豆骨、大多角骨、小多角骨、头状骨和钩骨，且腕骨之间的稳定性由多条掌侧和背 侧韧带维持。由于腕骨体积较小，且结构复杂，X线较难诊断腕骨骨折。漏诊或误诊 腕骨骨折可能会导致严重并发症：骨不愈合、畸形愈合、缺血性骨坏死、腕关节不稳 以及创伤性骨关节炎。本研究发现我院就诊的桡骨远端骨折患者同时伴有腕骨骨折的 发病率为6.32%，且大多数诊断由CT 确诊。而Komura 等[9]报道桡骨远端骨折患者 伴有腕骨骨折的发病率为7.00%。Welling 等[10]发现约有30%的腕骨骨折在X线诊断 漏诊，因此建议临床工作中对于腕部损伤的患者应在X线检查结果阴性后行CT检查。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '月骨周围脱位的影像学分析及临床应用\n华群1，胡勇2\n（1．宁波市第六医院放射科，浙江宁波315040；2．宁波市第六医院骨科）\n【摘要】目的：分析月骨周围脱位的影像学表现，提高对月骨周围脱位的认识和诊断水平。方法：回顾性分析 56 例月骨周围脱位患者X线片与多层螺旋CT 薄层扫描及三维重建（3D）和多平面重建（MPR）图像。其中男55 例，女 1 例；年龄18～47 岁，平均32．4 岁。结果：56 例月骨周围脱位，均为背侧型，其中经舟状骨月骨周围脱位11 例，不伴腕 骨骨折的单纯月骨周围脱位10 例，经舟状骨、三角骨、月骨周围脱位26 例（其中1 例伴豌豆骨撕脱骨折），经三角骨、 月骨周围脱位6 例，经头状骨、月骨周围脱位3 例。伴尺桡骨远端骨折24 例，伴掌腕关节脱位4 例。X线片诊断准确 29 例，误漏诊27 例。运用CT 薄层扫描及重建技术诊断全部准确。结论：熟悉腕关节的正常影像学解剖，掌握各型月骨 周围脱位的影像学特点，是作出准确诊断和及时治疗的基础。多层螺旋CT 薄层扫描及重建能够直观清晰地显示骨折 脱位的类型，为临床确定骨折分型、选择合适的治疗方案提供了可靠而直观的依据，是避免误漏诊的关键。', 'source': '月骨周围脱位的影像学分析及临床应用_华群.pdf'}, {'text': '本病的诊断思路：对腕骨排列紊乱，怀疑有月骨周围脱位 者，应首先确认月骨、头状骨与桡骨远端的关系，桡月关节是 否保持正常或基本正常，当发现头状骨近侧圆形关节面不坐 落在月骨远侧关节凹里，且头状骨纵轴中线位于桡骨纵轴中 线的背侧或掌侧，不论月骨有无掌倾或背倾，都应诊断为月骨 周围脱位。在此基础上再观察月骨与舟状骨、三角骨正常关系 有无破坏，以及有无舟状骨、三角骨和其他腕骨骨折。\n3．2 多层螺旋CT 3D和MPR重建在腕关节骨折脱位诊疗 中的价值长期以来腕关节创伤的诊断主要依赖于X线片， 而X线片仅仅是二维影像，对于解剖结构复杂又有相互重叠 的腕关节骨折脱位，特别是要发现骨折片小、移位不明显的骨 折，或者当腕关节有外固定石膏时，要想看清腕骨及腕关节结 构还是非常困难的。加之急诊腕关节外伤患者局部肿痛畸形、 活动受限、检查时欠合作，尤其是发生严重骨折脱位后其正常 的解剖关系已经发生改变，从而影响了骨折脱位的正确分型， 甚至误漏诊。本组病例X线片误漏诊较多的原因，主要是月 骨周围脱位常伴有其他腕骨骨折，且骨折块重叠、显示不清， 部分为细小撕脱性骨折及无移位骨折。', 'source': '月骨周围脱位的影像学分析及临床应用_华群.pdf'}, {'text': '2.3\u3000小结\n当桡骨远端骨折与既往手舟骨、月骨陈旧伤同时\n存在导致腕关节功能障碍时，如何判定本次外伤在损 伤结局中的参与程度是一个难点。通过本例，笔者认 为外伤与自身疾病的因果关系分析主要从以下几个 方面综合考虑：（1）鉴别与认定新鲜损伤与陈旧损伤； （2）详细了解自身既往疾病或损伤的严重程度、分型， 分析其对关节活动的影响；（3）结合外伤史、手术史、 病史及影像学资料，分析外伤所致骨折类型、愈后发 展变化及骨折部位对关节功能的影响；（4）对当前损 伤结局作出客观准确的判断，正确测量并评估后遗功 能障碍。\n在判断因果关系时，了解损伤影响功能障碍的解 剖学基础是相当重要的，损伤严重程度与功能障碍程 度相对应，例如利用分型来判断该关节骨折类 型。同时，通过对以往A案O例的流行病学分析，在一定 程度上能够辅助分析类似案例的因果关系，但需要注 意的是，由于统计的信息具有局限性，不能仅依靠统 计结果来判定因果关系，要同时结合伤情的特殊情 况，如致伤机制、严重程度、愈后情况等，并分析解剖 学基础，以获得公正可靠的鉴定意见。', 'source': '手舟骨、月骨陈旧伤合并桡骨远端骨折残疾等级及因果关系鉴定1例_于凯丽.pdf'}, {'text': 'Kiuru等[11]也建议对于复杂的腕关节骨折在X线结果不明确时，应行CT检查进行评 估，因为除舟骨骨折外，其他腕骨骨折在X线检查中灵敏度较低，难以确诊。此外， MRI 既能诊断腕骨骨折，同时也可以诊断腕部韧带损伤[12]。有文献表明，在诊断腕 骨损伤时，CT的灵敏度、特异度和准确度分别为67%、96%和91%，MRI 分别为67%、 96%、85%[13]。虽然MRI 与CT均可诊断腕关节损伤，但CT对于检查骨质连续性更 为敏感，且在急诊情况下也容易进行。\n舟骨骨折是最常见的腕骨骨折，约占腕骨的70%；其次为三角骨骨折，约占所有 腕骨的18%，且有超过90%的腕骨骨折均发生于近端腕骨[14-15]。在本研究中，舟骨 骨折占所有腕骨骨折的76%，三角骨骨折占所有腕骨的12%，并且与桡骨远端骨折\n相关的腕骨骨折有97%发生于近端腕骨，50 例患者中均未发生桡骨远端骨折伴头状 骨骨折。因此，与桡骨远端骨折相关的腕骨骨折发生的频率和分布大致与普通腕骨骨 折相同。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '2 结果\n2.1 桡骨远端骨折伴腕骨骨折的发病率及其特点\n研究结果显示，791 例桡骨远端骨折患者中有50 例合并腕骨骨折，发生率为 6.32%。其中男性33 例，女性17 例，年龄10~88岁，平均年龄（48.2±16.4）岁（表 1）。其中合并舟状骨骨折的有38 例（76.0%）；合并月骨骨折的有10 例（20%）；合 并三角骨骨折的有6 例（12.0%）；合并豆状骨骨折的有1 例（2.0%）：合并大多角骨 骨折的有2 例（4.0%）；合并小多角骨骨折的有1 例（2.0%）；合并钩骨骨折的有3 例（6.0%）；无合并头状骨骨折的患者（0%）（图1）。\n在50 例桡骨远端骨折合并腕骨骨折的病例中，舟状骨骨折最为常见，且大多数 骨折多发生于近端腕骨。此外，在50 例桡骨远端合并腕骨骨折的病例中，42 例只有 1 处腕骨骨折，5 例有2 处腕骨骨折，3 例有3 处腕骨骨折。50 例中有8 例伴有两块 以上腕骨骨折。', 'source': '桡骨远端骨折合并腕骨骨折的发病率及危险因素分析_赵潇雄.pdf'}, {'text': '月供\n骨的解剖学特点及损伤机制出发，总结分析月骨骨 折的分类、影像学特点及治疗方法，综述如下。\n1 月骨的解剖学特点及损伤机制\n1.1\u3000形态学特点\n月骨作为腕关节运动的桥梁分为内、外2个部 分，分别与头状骨、桡骨远端相关节，其解剖形态复 杂而不规则，个体差异较大［7］。月骨掌骨面呈方形， 外侧面呈新月形。作为腕关节中轴线，月骨是手\n腕地\n上唯一掌侧宽而背侧窄的骨［8］。月骨位于腕骨的中 央，表面被大量的无知觉关节软骨覆盖［9］，主体部分 被桡骨远端背唇包围，不能直接触诊，影像学定位 不清［10］，因此容易漏诊。\nViegas等［11］根据月骨的外形特征将其分为Ⅰ型 和型。型仅有一个单一的头月关节面；型有 个Ⅱ中腕关Ⅰ节面，一个与头状骨相关节，另一Ⅱ个与钩 2骨相关节。Hein等［12］对169例舟状骨骨折患者进行 了回顾分析，结果显示无论是手术治疗还是非手术 治疗，拥有型月骨的患者均比拥有型月骨的患 者更容易发Ⅱ生骨不连，且型月骨小关Ⅰ节大小不是 发生骨不连的显著危险因I素I。', 'source': '月骨骨折的治疗进展_阿卜杜热依木·阿卜杜克热木.pdf'}, {'text': '常合并舟状骨、头1状.1%骨、桡骨茎突骨折等其他损伤。腕部处于背伸位时掌背侧的局部疼痛，严重时会有 由于大量无神经纤维的软骨覆盖在月骨的表面，\n月皮\n阿卜杜热依木·阿卜杜克热木1，2，季佳庆1，2，殷子越1，2，钱继魁1，2，樊健1，2 1. 同济大学附属同济医院骨科，上海00065； 22. 同济大学医学院，上海200092\n［摘要］月骨骨折是较为罕见的腕部骨折，通常与高能创伤有关，常伴有腕关节其他骨损伤，如舟状骨、头状\n法和预后，目前仍存有争议。本文从月骨的解剖学特点及损伤机制出发，对月骨骨折的分类、影像学特点及治疗方\n ［文献标志码］A ［文章编号］2095-378X（2024）01-0067-05 \n［引用本文］阿卜杜热依木·阿卜杜克热木，季佳庆，殷子越，等. 月骨骨折的治疗进展［J］. 外科研究与新技术\nProgress in the treatment of lunate fracture\n2. Medical School of Tongji University，Shanghai 200092，China', 'source': '月骨骨折的治疗进展_阿卜杜热依木·阿卜杜克热木.pdf'}, {'text': '盘突出症的临床疗效观察［Ｊ］．生物骨科材料与临床研究，\n２０２３，２０（４）：５１－５５． ［１４］王晚红，唐锐，陈伟国，等．２４例机器人辅助单侧双通道脊柱内\n镜融合术治疗腰椎滑脱症患者的护理［Ｊ］．护理实践与研究，\n２０２３，２０（１０）：１５７３－１５７８．\n（接收日期：２０２５－０４－２１）\n·病例报道·\n患者，男，３０岁，因摔伤致右腕肿痛桡骨茎突舟骨月骨周围骨折脱位。入院离并暴露拇长伸肌腱及拇长短肌腱，向\n血管、皮肤损伤。先予手法复位，医师抓机透视可见断端对位对线可，但桡月关 握患者手指及腕部加以牵引，牵引过程节不稳，予２枚克氏针固定桡月关节，再 中推挤压迫月骨的同时屈曲腕关节，复次透视确认桡月关节在位，腕骨间关节 位后患肢疼痛减轻，各手指活动无明显对位正常，逐层缝合切口，右腕掌屈中立 受限，考虑月骨已复位。摄Ｘ线片复查位石膏托固定。术后右手末梢血运良 显示月骨复位。次日ＣＴ检查显示右腕好。术后６周拆除石膏固定并拔除克氏 桡骨远端舟状骨月骨三角骨骨折针术后４个月随访显示右腕关节功能', 'source': '经桡骨茎突舟骨月骨周围骨折脱位治疗1例_朱意成.pdf'}, {'text': '并发症，直接影响腕及手的功能。本文收集56 例月骨周围脱1．2 影像学检查 位，对其X线及CT 表现进行分析，并结合文献资料进行讨 论，旨在减少漏误诊，为临床提供准确及时的诊断意见。\n·临床研究·\nZhongguo Gushang ／China J Orthop＆Trauma，2009，22（6）：445 447 www．zggszz．com\n1．2．1 X线检查使用PHILIPS Digital Diagnost THDR 机， 术前、术后均拍摄腕关节正侧位X线片，部分摄斜位X线片。\nX线正位应注意腕骨的3 条弧线（图1），X线中立侧位应观 察桡骨、月骨、头状骨、第3 掌骨的中轴线构成的一条纵轴线\n系正常，其他腕骨向背侧移位，月骨掌倾，桡骨中轴线不能通过月骨中轴线与头状骨和第3 掌骨连成一条直线图5 男，27 岁，高处坠落多发 伤，右腕变形肿胀5a．腕关节CT 舟月骨平面冠状位重建示舟状骨、三角骨近侧骨折块、月骨与桡骨关系正常5b．腕关节CT 三维重建前面 观示舟状骨、三角骨近侧骨折块、月骨与桡骨关系正常，而舟状骨、三角骨远侧骨折块与其他腕骨一起向背侧移位，月骨远侧关节面空虚', 'source': '月骨周围脱位的影像学分析及临床应用_华群.pdf'}, {'text': '- Visual Type: Medical imaging collage (radiological scans including CT and X-ray images)\n- Title: None\n- Axes / Legends / Labels: \n  - Sub-figure labels: “③a”, “③b”, “④a”, “④b”, “⑤a”, “⑤b” (in circular markers at bottom-right of each panel)\n  - Caption text to the right of images: “图3 男,43岁,因跑步摔倒致左腕肿痛畸形就诊 3a. 关节CT月骨平面矢状位重建,经舟状骨、月骨周围脱位,头状骨明显位于月骨背侧,月骨与桡骨远端关系正常 3b. 腕关节CT三维重建前面观:月骨远侧关节凹空虚,舟状骨近侧骨折块与月骨关系正常,舟状骨远侧骨折块及其他腕骨向背侧移位 图4 男,38岁,车祸致左腕肿胀,活动受限 4a. 腕关节X线正位片示月骨周围脱位,腕关节弧线一和弧线二连续性中断,月骨旋转,头关节间隙明显增宽 4b. 腕关节X线侧位片示月骨与桡骨”\n- Data Points: \n  - Image ③a: Sagittal CT reconstruction showing lunate bone, scaphoid fracture, and dorsal displacement of capitate relative to lunate.\n  - Image ③b: 3D CT anterior view showing empty distal lunate articular surface; proximal scaphoid fragment aligned with lunate, distal scaphoid and other carpal bones displaced dorsally.\n  - Image ④a: Anteroposterior wrist X-ray showing perilyunate dislocation, disruption of Gilula’s arcs, rotated lunate, widened capitolunate joint space.\n  - Image ④b: Lateral wrist X-ray showing alignment between lunate and radius.\n  - Image ⑤a: Sagittal CT slice showing carpal bones and possible fracture/displacement (contextual based on caption).\n  - Image ⑤b: 3D CT reconstruction showing carpal bones from oblique angle, consistent with dorsal displacement pattern.\n- Trends / Insights: \n  - Images depict traumatic wrist injuries in two male patients (ages 43 and 38), specifically perilyunate dislocations with associated scaphoid fractures and dorsal carpal displacement.\n  - CT imaging (3D and sagittal reconstructions) provides detailed visualization of bone alignment and fracture fragments, while X-rays confirm disruption of normal carpal arc continuity and joint spacing — key diagnostic indicators for perilyunate instability.\n  - Consistent pattern across cases: lunate remains aligned with radius, but surrounding carpal bones (especially capitate and distal scaphoid) are displaced dorsally, indicating ligamentous injury and instability.\n- Captions / Annotations: \n  - The caption provides clinical context: patient demographics (age, sex), mechanism of injury (running fall, car accident), and radiological findings (dislocation type, bone relationships, arc disruptions). \n  - Relevance: Essential for correlating imaging findings with clinical presentation and confirming diagnosis of perilyunate dislocation with scaphoid fracture — a high-energy wrist injury requiring urgent orthopedic intervention.间隙明显增宽4b．腕关节X线侧位片示月骨与桡骨关\n腕关节弧线一和弧线二连续性中断，月骨旋转，头月关节\n胀，活动受限4a．腕关节X线正位片示月骨周围脱位，\n及其他腕骨向背侧移位图4 男，38 岁，车祸致左腕肿\n舟状骨近侧骨折块与月骨关系正常，舟状骨远侧骨折块\n3b．腕关节CT 三维重建前面观：月骨远侧关节凹空虚，\n位，头状骨明显位于月骨背侧，月骨与桡骨远端关系正常\n关节CT 头月骨平面矢状位重建，经舟状骨、月骨周围脱\n图3 男，43 岁，因跑步摔倒致左腕肿痛畸形就诊3a．腕\n3a \n4a \n4b\n5a', 'source': '月骨周围脱位的影像学分析及临床应用_华群.pdf'}]",  # 你给我的那一大坨
    # )

    # print("\n=== Generated Paragraph ===\n")
    # print(paragraph["content"])
    pass

