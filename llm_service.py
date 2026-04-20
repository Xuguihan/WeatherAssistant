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

def get_ai_advice(city_name:str,data_list:list) -> str:
    """
    调用 LLM 获取建议
    """
    sys_prompt=f"""
    你是一个专业的生活助手。
    任务：根据提供的天气数据，给出核心的穿衣和出行建议。
    要求：
    1、语气:亲切、自然、有活力，像朋友一样给出建议,适当加入表情符号。
    2、限制:总字数控制在 200 字以内。如果数据中缺少某些信息，不要编造，直接说明。
    3、格式:回复内容为两段:第一段:"{city_name}天气预报：……"(分别说明未来3天的天气和气温范围,对未来4至7天的概括即可)
    第二段："生活建议：……"（总结未来一周的变化趋势，根据天气数据给出通用的生活建议，如是否带伞、穿衣厚度等）
    """
    user_prompt=f"""
    这是{city_name}未来一周的天气数据,请进行播报并给出核心的生活建议,数据如下:
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


    