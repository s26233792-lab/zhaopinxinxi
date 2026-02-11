"""
Feishu API configuration and field mapping.
This module handles the connection to existing Feishu tables.
"""
from typing import Dict, Any, List
from .settings import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID

# Feishu API credentials
FEISHU_CONFIG = {
    "app_id": FEISHU_APP_ID,
    "app_secret": FEISHU_APP_SECRET,
    "app_token": FEISHU_APP_TOKEN,
    "table_id": FEISHU_TABLE_ID,
}

# Field mapping between internal data model and Feishu table fields
# This should be configured based on your existing Feishu table structure
FIELD_MAPPING: Dict[str, str] = {
    # Internal field name -> Feishu field id/name
    "publish_date": "岗位更新",  # field_id or field_name
    "batch": "批次",
    "company_name": "公司名称",
    "company_type": "企业类型",
    "industry": "行业",
    "city": "工作城市",
    "position": "岗位",
    "education": "学历要求",
    "deadline": "截止时间",
    "target": "招聘对象",
    "no_written_test": "免笔试",
    "source": "信息来源",
    "referral_code": "内推码",
}

# Feishu field type definitions
# Adjust these based on your existing table
FIELD_TYPES: Dict[str, str] = {
    "publish_date": "date",  # 日期
    "batch": "text",  # 文本
    "company_name": "text",  # 文本
    "company_type": "select",  # 单选
    "industry": "multiSelect",  # 多选
    "city": "multiSelect",  # 多选
    "position": "text",  # 文本
    "education": "select",  # 单选
    "deadline": "date",  # 日期
    "target": "multiSelect",  # 多选
    "no_written_test": "checkbox",  # 是/否
    "source": "url",  # URL
    "referral_code": "text",  # 文本
}

# Standard values for select/multiSelect fields
# These should match the options in your existing Feishu table
COMPANY_TYPE_OPTIONS = ["民营企业", "国有企业", "央企", "外资企业", "创业公司", "其他"]
INDUSTRY_OPTIONS = ["互联网", "金融", "制造业", "教育", "医疗", "房地产", "零售", "能源", "其他"]
EDUCATION_OPTIONS = ["本科", "硕士", "博士", "本科及以上", "硕士及以上", "不限"]
TARGET_OPTIONS = ["2026届", "2025届", "2024届", "往届"]

# API endpoints
ENDPOINTS = {
    "get_tenant_access_token": "/auth/v3/tenant_access_token/internal",
    "get_app_table_token": "/bitable/v1/app/{app_token}/table/{table_id}/token",
    "get_table_records": "/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    "create_table_record": "/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    "batch_create_table_records": "/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
    "update_table_record": "/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
    "batch_update_table_records": "/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
    "get_table_fields": "/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
}


def get_feishu_field_value(internal_field: str, value: Any) -> Dict[str, Any]:
    """
    Convert internal field value to Feishu API format.

    Args:
        internal_field: Internal field name
        value: Field value

    Returns:
        Dictionary in Feishu API format
    """
    field_type = FIELD_TYPES.get(internal_field, "text")
    feishu_field = FIELD_MAPPING.get(internal_field, internal_field)

    if value is None or value == "":
        return None

    result = {"field_id": feishu_field}

    if field_type == "date":
        result["date"] = value.strftime("%Y-%m-%d") if hasattr(value, "strftime") else str(value)
    elif field_type == "select":
        result["select"] = {"name": value}
    elif field_type == "multiSelect":
        if isinstance(value, list):
            result["multiSelect"] = [{"name": v} for v in value]
        else:
            result["multiSelect"] = [{"name": value}]
    elif field_type == "checkbox":
        result["checkbox"] = bool(value)
    elif field_type == "url":
        result["url"] = str(value)
    else:  # text
        result["text"] = str(value)

    return result


def build_feishu_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a Feishu record from internal data format.

    Args:
        data: Internal data dictionary

    Returns:
        Feishu record dictionary
    """
    fields = {}

    for internal_field, value in data.items():
        if internal_field in FIELD_MAPPING:
            feishu_value = get_feishu_field_value(internal_field, value)
            if feishu_value:
                feishu_field = FIELD_MAPPING[internal_field]
                fields[feishu_field] = feishu_value

    return {"fields": fields}
