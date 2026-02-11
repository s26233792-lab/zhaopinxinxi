# -*- coding: utf-8 -*-
"""
Research Feishu API field types and formats.
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID")

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def get_token():
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    response = requests.post(url, json=payload)
    return response.json().get("tenant_access_token")


def analyze_fields():
    """Analyze field structure and provide test cases."""
    print("=" * 60)
    print("飞书 API 字段类型分析")
    print("=" * 60)
    print()

    token = get_token()
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/fields"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data}")
        return

    fields = data.get("data", {}).get("items", [])

    # Field type constants
    TYPE_NAMES = {
        1: "文本 (Text)",
        2: "数字 (Number)",
        3: "单选 (SingleSelect)",
        4: "多选 (MultiSelect)",
        5: "日期 (Date)",
        11: "复选框 (Checkbox)",
        15: "人员 (Person)",
        17: "群组 (Group)",
        18: "电话 (Phone)",
        19: "邮件 (Email)",
        20: "URL",
        21: "引用 (Reference)",
    }

    print("字段列表：\n")

    text_fields = []
    select_fields = []
    checkbox_fields = []
    multi_fields = []

    for f in fields:
        name = f.get("field_name", "?")
        fid = f.get("field_id", "?")
        ftype = f.get("type")
        type_name = TYPE_NAMES.get(ftype, f"Unknown({ftype})")
        ui_type = f.get("ui_type", "")

        print(f"- {name}")
        print(f"  Type: {type_name}")
        print(f"  Field ID: {fid}")
        print(f"  UI Type: {ui_type}")

        # Show options for select/multi-select
        if ftype in [3, 4]:  # SingleSelect or MultiSelect
            options = f.get("property", {}).get("options", [])
            if options:
                option_names = [opt.get("name", "") for opt in options]
                print(f"  选项: {', '.join(option_names)}")

        print()

        # Categorize fields
        if ftype == 1:
            text_fields.append(name)
        elif ftype == 4:
            multi_fields.append(name)
        elif ftype == 11:
            checkbox_fields.append(name)
        elif ftype == 3:
            select_fields.append(name)

    print("=" * 60)
    print("字段分类总结")
    print("=" * 60)
    print(f"文本字段: {', '.join(text_fields)}")
    print(f"单选字段: {', '.join(select_fields)}")
    print(f"多选字段: {', '.join(multi_fields)}")
    print(f"复选框字段: {', '.join(checkbox_fields)}")
    print()

    return {
        "token": token,
        "text_fields": text_fields,
        "select_fields": select_fields,
        "multi_fields": multi_fields,
        "checkbox_fields": checkbox_fields,
        "fields": fields
    }


def test_multi_field(token, field_name, field_id):
    """Test writing a multi-select field."""
    print(f"\n测试多选字段: {field_name}")
    print(f"Field ID: {field_id}")

    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}

    # Test different formats
    test_cases = [
        {"name": "格式1: 字符串数组", "value": ["北京"]},
        {"name": "格式2: 多个选项", "value": ["北京", "上海"]},
        {"name": "格式3: 单个选项（不用数组）", "value": "北京"},
    ]

    for test in test_cases:
        payload = {
            "fields": {
                "公司名称": f"测试_{test['name']}",
                "岗位": "测试岗位",
                field_id: test["value"]
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        status = "[OK]" if data.get("code") == 0 else "[FAILED]"
        print(f"  {status} {test['name']}: {data.get('msg', data)}")


def test_checkbox_field(token, field_name, field_id):
    """Test writing a checkbox field."""
    print(f"\n测试复选框字段: {field_name}")
    print(f"Field ID: {field_id}")

    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}

    # Test different formats
    test_cases = [
        {"name": "格式1: True", "value": True},
        {"name": "格式2: False", "value": False},
        {"name": "格式3: 字符串'true'", "value": "true"},
        {"name": "格式4: 字符串'是'", "value": "是"},
    ]

    for test in test_cases:
        payload = {
            "fields": {
                "公司名称": f"测试_{test['name']}",
                "岗位": "测试岗位",
                field_id: test["value"]
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        status = "[OK]" if data.get("code") == 0 else "[FAILED]"
        print(f"  {status} {test['name']}: {data.get('msg', data)}")


def main():
    """Run analysis and tests."""
    info = analyze_fields()

    # Test multi-select fields
    if info["multi_fields"]:
        for field_name in info["multi_fields"]:
            # Find field ID
            for f in info["fields"]:
                if f.get("field_name") == field_name:
                    test_multi_field(info["token"], field_name, f.get("field_id"))
                    break

    # Test checkbox fields
    if info["checkbox_fields"]:
        for field_name in info["checkbox_fields"]:
            for f in info["fields"]:
                if f.get("field_name") == field_name:
                    test_checkbox_field(info["token"], field_name, f.get("field_id"))
                    break


if __name__ == "__main__":
    main()
