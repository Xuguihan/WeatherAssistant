from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 配置区,从环境变量中读取
llm_api_key=os.getenv("LLM_KEY")
url=os.getenv("LLM_URL")

# 初始化客户端
client = OpenAI(
    api_key=llm_api_key, 
    base_url=url
)

def get_ai_advice(data_list) -> str:
    """
    调用 LLM 获取建议
    """
    sys_prompt="""
    你是一个专业的生活助手。
    任务：根据提供的天气数据，给出最核心的穿衣和出行建议。。
    要求：
    1、语气:亲切、自然，像朋友一样给建议，不要像机器人一样只报数据。
    2、依据:严格基于提供的天气数据进行分析。
    3、场景:如果用户没有指定具体场景，请默认根据当前天气给出通用的生活建议（如是否带伞、穿衣厚度）。
    4、限制:总字数控制在 150 字以内。如果数据中缺少某些信息，不要编造，直接说明。
    """

    user_prompt=f"""
    请对以下天气数据采用合适格式播报，并根据数据给出核心的生活建议:
    {data_list}
    """

    try:
        # 调用 API
        response = client.chat.completions.create(
            model="qwen-plus",  
            messages=[
                {"role": "system", 
                 "content": sys_prompt},
                {"role": "user", "content":user_prompt}
            ],
            temperature=0.8, # 创造力参数，0-2之间
            max_tokens=200   # 最多生成200个token
        )
        
        # 提取并返回 AI 的回答
        return response.choices[0].message.content
        
    except Exception as e:
        return f"调用 AI 时出错: {e}"


    