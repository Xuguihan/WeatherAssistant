import requests
import os
from dotenv import load_dotenv
import db_manager
import json
from datetime import datetime

# 加载.env文件
load_dotenv()

# 配置区,从环境变量中读取
api_host=os.getenv("WEATHER_HOST")
api_key=os.getenv("WEATHER_KEY")

geo_url=f"https://{api_host}/geo/v2/city/lookup"
weather_url=f"https://{api_host}/v7/weather/7d"

# ------调用接口函数------
def get_id_from_api(city_name:str)->str:
    """
    从API接口处查询地区ID
    """
    params = {
        "location": city_name,
        "key": api_key
    }
    try:
        response = requests.get(geo_url, params=params,timeout=10)
        response.raise_for_status() # 如果状态码不是 200，直接抛出异常
        data = response.json()
        # 检查是否有 location 数据
        if data.get("location"):
            return data["location"][0]["id"]
        else:
            print(f"未找到城市 '{city_name}'，请检查拼写。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
        return None
    
def get_info_from_api(city_id:str)->dict:
    params={
        "location":city_id,
        "key":api_key
    }
    try:
        response = requests.get(weather_url, params=params,timeout=10)
        raw_data=response.json()
        return raw_data # 即使失败也返回 JSON，交给 parser 处理
    except Exception as e:
        print(f"网络请求异常: {e}")
        return {"code": "500", "message": str(e)} # 返回一个标准错误格式


# ------获取地区ID和天气信息函数------
def get_city_location(city_name:str)->str:
    """
    输入地区名称,返回地区ID,如果未找到则返回 None(优先查库,没有则调用API)
    """
    print(f"用户正在查找:{city_name}")
    location_id=None
    # 查询数据库里是否有地区ID
    record=db_manager.get_city_from_db(city_name)
    if record:
        location_id=record
        print(f"数据库命中城市id:{location_id}")
        return location_id
    else:
        print("数据库未命中,正在调用API查询城市ID……")
        location_id=get_id_from_api(city_name)
        db_manager.add_city_to_db(city_name,location_id) # 将查询信息写入数据库
        return location_id

def get_weather_raw(city_id:str)->dict:
    """
    输入地区ID,获取原始数据(优先查库,没有调用API)
    """
    raw_data={}
    now = datetime.now().isoformat() # 取系统时间
    target_date=now.split('T')[0] # 提取当前日期
    # 查看数据库里是否有天气信息
    record=db_manager.get_weather_from_db(city_id,target_date)
    if record:
        raw_data=json.loads(record) # 将字符串转化为字典
        print("数据库命中天气信息！")
        return raw_data
    else:
        print("数据库未命中,正在调用API查询天气信息……")
        raw_data=get_info_from_api(city_id)
        raw_data_str = json.dumps(raw_data, ensure_ascii=False) # 将字典转化为字符串
        db_manager.update_weather_in_db(city_id,target_date,raw_data_str)
        return raw_data # 即使失败也返回 JSON，交给 parser 处理

def parse_weather_data(raw_data: dict) -> list:
    """
    解析原始数据,转换成需要的格式
    """
    if raw_data.get("code") != "200": 
        print(f"天气 API 错误: {raw_data.get('message', 'Unknown Error')}")
        return []
    
    data_list = []
    for item in raw_data["daily"]:
        # 只提取我们需要的字段
        data_list.append({
            "日期": item["fxDate"],
            "最高温": item["tempMax"],
            "最低温": item["tempMin"],
            "白天": item["textDay"],
            "夜晚": item["textNight"]
        })
    return data_list


    