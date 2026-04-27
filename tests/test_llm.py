# tests/test_llm.py

import pytest
from unittest.mock import patch, MagicMock
import llm_service

# ==========================================
# 测试 get_ai_advice (正常情况)
# ==========================================
@patch('llm_service.client')
def test_get_ai_advice_success(mock_client):
    # 1. 构造模拟的返回对象结构
    # OpenAI 的返回结构比较深: response.choices[0].message.content
    mock_choice = MagicMock()
    mock_choice.message.content = "这里是大模型的回复：明天记得带伞哦！"
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    # 让 client.chat.completions.create 返回我们的模拟对象
    mock_client.chat.completions.create.return_value = mock_response

    # 2. 调用函数
    fake_data = [{"日期": "2026-04-27", "白天": "Sunny"}]
    response_text = llm_service.get_ai_advice("Beijing", fake_data)

    # 3. 断言
    assert response_text == "这里是大模型的回复：明天记得带伞哦！"
    
    # 进阶断言：检查是否调用了 create 方法
    mock_client.chat.completions.create.assert_called_once()

# ==========================================
# 测试 get_ai_advice (异常情况)
# ==========================================
@patch('llm_service.client')
def test_get_ai_advice_failure(mock_client):
    # 1. 模拟 API 抛出异常（比如网络断了，或者 Key 错了）
    mock_client.chat.completions.create.side_effect = Exception("Network Error")

    # 2. 调用函数
    response_text = llm_service.get_ai_advice("Beijing", [])

    # 3. 断言：应该返回包含错误信息的字符串，而不是让程序崩溃
    assert "调用 AI 时出错" in response_text
    assert "Network Error" in response_text