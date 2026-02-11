# -*- coding: utf-8 -*-
"""
Working version with multi-select field support.
"""
import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_sources.hybrid_collector import DemoDataSource
from utils.compliance import check_emergency_stop, log_fetch

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


def write_to_feishu(records, source_name: str = "unknown"):
    """
    Write records to Feishu with multi-select support.

    Note: "免笔试" field is excluded because it's a Person type field,
    not a boolean. This can be handled differently if needed.
    """
    token = get_token()
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}

    success_count = 0

    print(f"\n正在写入 {len(records)} 条记录到飞书...")

    for i, record in enumerate(records, 1):
        # Build request with Chinese field names
        fields = {
            "批次": record.get("批次", "春招"),
            "公司名称": record.get("公司名称", ""),
            "岗位": record.get("岗位", ""),
            "行业": record.get("行业", "互联网"),
            "企业类型": record.get("企业类型", "民营企业"),
            "学历要求": record.get("学历要求", "本科及以上"),
            "信息来源": record.get("信息来源", source_name),
            "内推码": record.get("内推码", ""),
        }

        # Handle multi-select field (工作城市)
        cities = record.get("工作城市", [])
        if cities:
            if isinstance(cities, list):
                # Convert to list of strings if needed
                cities = [str(c) for c in cities]
                fields["工作城市"] = cities
            else:
                fields["工作城市"] = [str(cities)]

        # Note: Skip "免笔试" field as it's a Person type, not boolean
        # If you need it, you'd need to format it as a Person object

        payload = {"fields": fields}

        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if data.get("code") == 0:
                success_count += 1
                city_str = ", ".join(cities) if cities else "未设置"
                print(f"  [{i}/{len(records)}] {record.get('公司名称')} - {record.get('岗位')} ({city_str}) [OK]")
            else:
                log_fetch(record.get("信息来源", source_name), source_name, False, 0)
                print(f"  [{i}/{len(records)}] {record.get('公司名称')} - {record.get('岗位')} [FAILED: {data.get('msg')}]")

        except Exception as e:
            log_fetch(record.get("信息来源", source_name), source_name, False, 0)
            print(f"  [{i}/{len(records)}] {record.get('公司名称')} - {record.get('岗位')} [ERROR: {e}]")

    return success_count


def main():
    """Main entry point."""
    print("=" * 60)
    print("招聘信息汇总系统 - 增强版（支持多选字段）")
    print("=" * 60)
    print()

    # Check emergency stop
    if check_emergency_stop():
        print("检测到停止信号，退出...")
        return

    # Get demo data
    print("使用演示数据模式...")
    crawler = DemoDataSource(count=10)
    records = crawler.fetch()

    if not records:
        print("\n没有收集到任何数据，退出...")
        return

    print(f"\n总共收集到 {len(records)} 条记录")

    # Show preview
    print("\n数据预览:")
    for i, r in enumerate(records[:5], 1):
        cities = r.get("工作城市", [])
        city_str = ", ".join(cities) if cities else "未设置"
        print(f"  {i}. {r['公司名称']} - {r['岗位']} ({city_str})")
    print()

    # Write to Feishu
    try:
        success_count = write_to_feishu(records, "招聘信息汇总系统")

        print()
        print("=" * 60)
        print(f"完成！成功写入 {success_count}/{len(records)} 条记录")
        print("=" * 60)
        print()
        print("请打开飞书表格查看数据：")
        print(f"https://pxb6kilxyue.feishu.cn/base/D6Q8boL8Ea2bREsEKVYcHt8UnLL/app/{FEISHU_APP_TOKEN}/table/{FEISHU_TABLE_ID}")
        print()
        print("注意：")
        print("  [OK] 多选字段（工作城市）已支持")
        print("  [SKIP] 复选框字段（免笔试）暂时禁用（类型问题）")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
