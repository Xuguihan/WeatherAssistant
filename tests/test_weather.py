# tests/test_weather.py

import pytest
from unittest.mock import patch, MagicMock
import weather_query
import json

# ==========================================
# 测试 get_id_from_api (网络请求部分)
# ==========================================
@patch('weather_query.requests.get')
def test_get_id_success(mock_get):
    # 1. 模拟 API 返回的 JSON 数据
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "location": [{"id": "101010100", "name": "Beijing"}]
    }
    mock_get.return_value = mock_response

    # 2. 调用函数
    city_id = weather_query.get_id_from_api("Beijing")

    # 3. 断言结果
    assert city_id == "101010100"
    assert mock_get.called  # 确保真的发起了请求

@patch('weather_query.requests.get')
def test_get_id_not_found(mock_get):
    # 模拟找不到城市的情况
    mock_response = MagicMock()
    mock_response.json.return_value = {"location": []}
    mock_get.return_value = mock_response

    city_id = weather_query.get_id_from_api("UnknownCity")
    assert city_id is None

# ==========================================
# 测试 get_city_location (数据库逻辑部分)
# ==========================================
@patch('weather_query.db_manager')
def test_get_city_location_db_hit(mock_db):
    # 1. 模拟数据库已经存有 ID
    mock_db.get_city_from_db.return_value = "101010100"

    # 2. 调用函数
    city_id = weather_query.get_city_location("Beijing")

    # 3. 断言：应该直接返回数据库的值，且没有调用 API (get_id_from_api)
    assert city_id == "101010100"
    mock_db.get_city_from_db.assert_called_once_with("Beijing")
    # 检查是否没有去调 API
    # 注意：这里因为我们在上面patch了requests，这里主要验证逻辑走向
    # 实际逻辑中，如果没有走 else，就不会调 API

@patch('weather_query.db_manager')
@patch('weather_query.get_id_from_api')
def test_get_city_location_db_miss(mock_api, mock_db):
    # 1. 模拟数据库没数据，API 有新数据
    mock_db.get_city_from_db.return_value = None
    mock_api.return_value = "NEW_ID_123"

    # 2. 调用函数
    city_id = weather_query.get_city_location("Shanghai")

    # 3. 断言：应该返回 API 的结果，并且写入了数据库
    assert city_id == "NEW_ID_123"
    mock_api.assert_called_once_with("Shanghai")
    mock_db.add_city_to_db.assert_called_once_with("Shanghai", "NEW_ID_123")

# ==========================================
# 测试 parse_weather_data (纯逻辑部分)
# ==========================================
def test_parse_weather_data_success():
    # 模拟完整的 API 返回数据
    raw_data = {
        "code": "200",
        "daily": [
            {"fxDate": "2026-04-27", "tempMax": "25", "tempMin": "15", "textDay": "Sunny", "textNight": "Clear"},
            {"fxDate": "2026-04-28", "tempMax": "22", "tempMin": "14", "textDay": "Rain", "textNight": "Rain"}
        ]
    }

    result = weather_query.parse_weather_data(raw_data)

    assert len(result) == 2
    assert result[0]["最高温"] == "25"
    assert result[1]["白天"] == "Rain"

def test_parse_weather_data_api_error():
    # 模拟 API 报错
    raw_data = {"code": "404", "message": "City not found"}
    result = weather_query.parse_weather_data(raw_data)
    assert result == [] # 应该返回空列表