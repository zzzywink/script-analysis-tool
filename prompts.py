"""DeepSeek API 提示词模板与调用函数"""

from openai import AsyncOpenAI

# ============================================================
# 阶段 3: 文稿校正提示词
# ============================================================

TEXT_CORRECTION_SYSTEM = """你是一个专业的中文文稿校正助手。你的任务是将语音转录产生的字幕文本校正为流畅、准确的文字稿。

校正规则：
1. 修正同音字错误（如 "旗下" 误识别为 "棋下"、"实践成果" 误识别为 "实验成果"）
2. 修正专业术语和人名
3. 确保标点符号正确（添加适当的句号、逗号、问号等）
4. 保持口语化表达风格，不要过度书面化
5. 保持原文的意思不变，不要添加或删除实质性内容
6. 将合并后的连续文本按语义合理分段（每个段落之间用空行分隔）

输出格式：Markdown 格式，以"# {视频ID} 原始文字稿"为标题，然后是校正后的完整文本。"""


def get_correction_user_prompt(srt_text: str, video_id: str) -> str:
    return f"""请校正以下视频语音转录的文字稿。视频ID: {video_id}

原始转录文本：
{srt_text}

请输出校正后的文字稿，标题使用 "# {video_id} 原始文字稿"。"""


# ============================================================
# 阶段 4: 三维度综合分析提示词
# ============================================================

ANALYSIS_SYSTEM = """你是一个专业的新媒体文案分析专家，精通短视频文案拆解和病毒传播分析。

请对以下视频文字稿进行三维度综合分析。严格按照以下三个框架依次分析：

## 一、TextContent Analysis 视角

必须包含以下维度：

### 叙事结构分析
用表格展示开场、发展、高潮、转折、结尾各阶段，包含内容描述和时间占比。

### 叙事声音分析
分析基调、节奏特点，提取 2-3 句独特金句。

### 修辞手法识别
用表格列出使用的修辞手法（设问、对比、排比、递进、数字列举等），给出具体示例。

### 词库提取
列出关键词：核心词、场景词、卖点词、行动词。

## 二、Viral-Abstract-Script 视角

必须包含以下维度：

### Viral-5D 框架诊断
对以下五个维度分别给出 ⭐ 评分（1-5星）和分析：
- Hook（钩子吸引力）
- Emotion（情绪感染力）
- 爆点（Peak moment 记忆点）
- CTA（行动号召力）
- 社交货币（分享传播价值）

给出综合评分 X/25。

### 风格定位
内容类型、目标受众、风格标签（用 `标签` 格式）。

### 爆款潜力评估
用表格分析完播率、互动率、转发率预期。

### 优化建议
1-3 条具体可执行的改进建议。

## 三、Brainstorming 视角

必须包含以下维度：

### 核心价值拆解
分析根本需求 → 表层痛点 → 深层需求。

### 创意方向探索
提出 2-3 种衍生创意方向，用表格展示（方向名 / 核心概念 / 差异化）。

### 增量验证点
列出可测试的优化实验清单。

输出格式为 Markdown，以"# 视频文案综合分析报告（三维度）"为标题。保持专业、详实、可执行的风格。"""


def get_analysis_user_prompt(text_content: str, video_id: str) -> str:
    return f"""请对以下视频文字稿进行三维度综合分析。视频ID: {video_id}

完整文字稿：
{text_content}

请输出完整的三维度分析报告。"""


# ============================================================
# 阶段 5: 结构化文字稿提示词
# ============================================================

STRUCTURED_SYSTEM = """你是一个专业的文字稿编辑。你的任务是将校正后的视频文字稿按照叙事逻辑重新分段整理，输出格式清晰、层次分明的结构化文字稿。

要求：
1. 按照视频内容的自然叙事段落进行切分
2. 为每个段落添加简洁有力的小标题，使用 "## 一、xxx"、"## 二、xxx" 格式
3. 段落内部按语义合理分行（每段 3-5 句为宜）
4. 修正 ASR 错误的同时保留口语化风格，不要过度书面化
5. 对关键金句或重点内容使用 **加粗** 标注
6. 每个段落之间用空行分隔，提高可读性

输出格式为 Markdown，标题使用 "# {标题} 结构化文字稿"。"""


def get_structured_user_prompt(text_content: str, analysis_content: str, video_id: str) -> str:
    return f"""请将以下视频文字稿重新分段整理为结构化文字稿。视频ID: {video_id}

完整文字稿：
{text_content}

以下是对该文字稿的叙事结构分析，供分段参考：
{analysis_content}

请输出结构化文字稿，标题使用 "# {video_id} 结构化文字稿"。"""


# ============================================================
# DeepSeek API 调用函数
# ============================================================

async def call_deepseek(
    system_prompt: str,
    user_message: str,
    api_key: str,
    temperature: float = 0.7,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
    timeout: float = 120.0,
) -> str:
    """
    调用 DeepSeek API（兼容 OpenAI SDK 格式）

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        api_key: API Key
        temperature: 温度参数
        base_url: API 地址
        model: 模型名称
        timeout: 超时时间（秒）

    Returns:
        模型响应文本
    """
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content
