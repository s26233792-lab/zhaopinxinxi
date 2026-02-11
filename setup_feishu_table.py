# -*- coding: utf-8 -*-
"""
Setup script for creating Feishu Bitable with required fields.
Run this script to automatically create the table and get credentials.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# Feishu API endpoints
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def get_tenant_access_token():
    """Get tenant access token for API calls."""
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }

    response = requests.post(url, json=payload)
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"Failed to get access token: {data.get('msg')}")

    return data.get("tenant_access_token")


def create_app(token):
    """Create a new app (bitable)."""
    url = f"{FEISHU_API_BASE}/bitable/v1/apps"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "招聘信息汇总表",
        "folder_token": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"Failed to create app: {data.get('msg')}")

    app_data = data.get("data", {}).get("app", {})
    return app_data.get("app_token"), app_data.get("app_id")


def get_tables(token, app_token):
    """Get all tables in the app."""
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"Failed to get tables: {data.get('msg')}")

    return data.get("data", {}).get("items", [])


def create_table(token, app_token):
    """Get the default table."""
    tables = get_tables(token, app_token)

    if not tables:
        raise Exception("No tables found in the app")

    table_id = tables[0].get("table_id")
    table_name = tables[0].get("name")

    return table_id, table_name


def main():
    """Main function to setup Feishu table."""
    print("=" * 50)
    print("飞书表格自动创建脚本")
    print("=" * 50)
    print()

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("错误：请先在 .env 文件中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return

    print(f"App ID: {FEISHU_APP_ID}")
    print(f"App Secret: {FEISHU_APP_SECRET[:10]}...")
    print()

    try:
        # Step 1: Get access token
        print("步骤 1/3: 获取访问令牌...")
        token = get_tenant_access_token()
        print("[OK] 访问令牌获取成功")
        print()

        # Step 2: Create app
        print("步骤 2/3: 创建多维表格应用...")
        app_token, app_id = create_app(token)
        print(f"[OK] 应用创建成功")
        print(f"  App Token: {app_token}")
        print()

        # Step 3: Get table
        print("步骤 3/3: 获取数据表信息...")
        table_id, table_name = create_table(token, app_token)
        print(f"[OK] 表格信息获取成功")
        print(f"  Table ID: {table_id}")
        print(f"  Table Name: {table_name}")
        print()

        # Summary
        print("=" * 50)
        print("创建完成！")
        print("=" * 50)
        print()
        print("请复制以下信息到 .env 文件：")
        print()
        print(f"FEISHU_APP_TOKEN={app_token}")
        print(f"FEISHU_TABLE_ID={table_id}")
        print()
        print("表格访问链接：")
        print(f"https://pxb6kilxyue.feishu.cn/base/D6Q8boL8Ea2bREsEKVYcHt8UnLL/app/{app_token}/table/{table_id}")
        print()

    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
