from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
# 业务模块
import db_manager
import weather_query
import llm_service

# ---配置模版目录---
templates = Jinja2Templates(directory="templates")

# 定义 lifespan 管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时运行：初始化数据库
    db_manager.init_db()
    print("数据库初始化完成!")
    yield
    # 关闭时运行（留空即可）
    print("应用关闭")

# 初始化 FastAPI 应用，并传入 lifespan
app = FastAPI(title="天气AI", lifespan=lifespan)

# ---定义数据模型---
# 定义请求数据的格式 (用来接收前端传来的 JSON)
class CityRequest(BaseModel):
    city: str

# 定义返回数据的格式 (可选，但推荐，方便文档展示)
class AdviceResponse(BaseModel):
    city: str
    advice: str
    status: str = "success"

# ---核心业务逻辑函数---
def process_weather_logic(city_name: str)->str:
    # 获取 Location ID (会自动查库或调 API)
    loc_id = weather_query.get_city_location(city_name)
    if not loc_id:
        raise ValueError(f"找不到城市：{city_name}")
    # 获取天气原始数据 (会自动查库或调 API)
    raw_data = weather_query.get_weather_raw(loc_id)
    if not raw_data:
        raise ValueError("获取天气数据失败")
    # 解析天气数据 (变成好读的列表)
    parsed_weather = weather_query.parse_weather_data(raw_data)
    # 调用 LLM 获取建议
    ai_advice = llm_service.get_ai_advice(city_name,parsed_weather)
    # --- 逻辑结束 ---
    return ai_advice

# --- 网页接口 (GET) ---
@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    # 显示网页，不传递 advice
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={"advice": None}
    )

# --- 网页提交接口 (POST) ---
@app.post("/get_advice", response_class=HTMLResponse)
async def submit_form(request: Request, city: str = Form(...)):
    try:
        # 调用核心逻辑
        advice = process_weather_logic(city.strip())
        # 重新渲染网页，并把 advice 传过去显示
        return templates.TemplateResponse(
            name="index.html",
            request=request,
            context={"advice": advice}
        )
    except Exception as e:
        # 如果出错，把错误信息也传给网页显示
        return templates.TemplateResponse(
            name="index.html",
            request=request,
            context={"advice": f"发生错误: {e}"}
        )

# --- API 接口 ---
@app.post("/api/get_advice", response_model=AdviceResponse)
async def get_advice_api(request: CityRequest):
    try:
        advice = process_weather_logic(request.city.strip())
        return {"city": request.city, "advice": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))