# -*- coding: utf-8 -*-
"""
Feishu Table Views and Organization Setup

This script helps create organized views and filters for the recruitment table.
Run this after recreating the Feishu table and updating .env credentials.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID")

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def get_token():
    """Get Feishu access token."""
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    response = requests.post(url, json=payload)
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"Failed to get token: {data.get('msg')}")

    return data.get("tenant_access_token")


def get_table_views(token):
    """Get existing views in the table."""
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/views"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") == 0:
        return data.get("data", {}).get("items", [])
    else:
        print(f"Error getting views: {data.get('msg')}")
        return []


def get_fields(token):
    """Get all fields in the table."""
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/fields"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") == 0:
        return data.get("data", {}).get("items", [])
    else:
        print(f"Error getting fields: {data.get('msg')}")
        return []


def print_organization_guide(fields):
    """Print manual organization guide."""
    print("\n" + "=" * 60)
    print("飞书表格分类整理指南")
    print("=" * 60)

    print("\n## 推荐创建的视图：\n")

    views = [
        {
            "name": "全部信息",
            "description": "显示所有记录，默认视图",
            "filters": "无",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "今日更新",
            "description": "只显示今天更新的岗位",
            "filters": "筛选条件: 岗位更新 = 今天",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "本周更新",
            "description": "显示最近7天更新的岗位",
            "filters": "筛选条件: 岗位更新 = 最近7天",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "互联网行业",
            "description": "只显示互联网相关岗位",
            "filters": "筛���条件: 行业 包含 '互联网'",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "央国企/事业编",
            "description": "显示国企、央企、事业单位岗位",
            "filters": "筛选条件: 企业类型 包含 '国企' 或 '央企' 或 '事业单位'",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "免笔试岗位",
            "description": "显示免笔试的岗位（如字段已配置）",
            "filters": "筛选条件: 免笔试 = 是",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "北京岗位",
            "description": "显示工作城市包含北京的岗位",
            "filters": "筛选条件: 工作城市 包含 '北京'",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "上海岗位",
            "description": "显示工作城市包含上海的岗位",
            "filters": "筛选条件: 工作城市 包含 '上海'",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "深圳岗位",
            "description": "显示工作城市包含深圳的岗位",
            "filters": "筛选条件: 工作城市 包含 '深圳'",
            "sort": "按 岗位更新 降序"
        },
        {
            "name": "本科及以上",
            "description": "显示本科学历要求的岗位",
            "filters": "筛选条件: 学历要求 = '本科' 或 '本科及以上'",
            "sort": "按 岗位更新 降序"
        }
    ]

    for i, view in enumerate(views, 1):
        print(f"\n{i}. {view['name']}")
        print(f"   说明: {view['description']}")
        print(f"   筛选: {view['filters']}")
        print(f"   排序: {view['sort']}")

    print("\n" + "-" * 60)
    print("\n## 手动创建视图步骤：")
    print("1. 打开飞书表格")
    print("2. 点击表格右上角 '+' 按钮（新建视图）")
    print("3. 输入视图名称")
    print("4. 点击筛选图标，设置筛选条件")
    print("5. 点击排序图标，设置排序规则")
    print("6. 保存视图")

    print("\n" + "-" * 60)
    print("\n## 推荐的字段分组：")
    print("\n分组1: 按企业类型分组")
    print("  - 民营企业")
    print("  - 国企")
    print("  - 央企")
    print("  - 外企")
    print("  - 创业公司")
    print("\n分组2: 按行业分组")
    print("  - 互联网")
    print("  - 金融")
    print("  - 制造")
    print("  - 教育")
    print("  - 医疗")
    print("\n分组3: 按工作城市分组")
    print("  - 北京")
    print("  - 上海")
    print("  - 深圳")
    print("  - 杭州")
    print("  - 广州")
    print("  - 成都")
    print("  - 其他")

    print("\n" + "-" * 60)
    print("\n## 推荐的看板视图（Kanban）：")
    print("\n看板1: 按企业类型展示")
    print("  - 分组依据: 企业类型")
    print("  - 每张卡片显示: 公司名称、岗位、城市")
    print("\n看板2: 按行业展示")
    print("  - 分组依据: 行业")
    print("  - 每张卡片显示: 公司名称、岗位、城市")
    print("\n看板3: 按城市展示")
    print("  - 分组依据: 工作城市")
    print("  - 每张卡片显示: 公司名称、岗位、企业类型")

    print("\n" + "-" * 60)
    print("\n## 推荐的日历视图：")
    print("\n日历: 按截止时间展示")
    print("  - 日期字段: 截止时间")
    print("  - 标题字段: 公司名称 - 岗位")
    print("  - 方便查看即将截止的岗位")

    print("\n" + "=" * 60)


def print_manual_setup_instructions():
    """Print detailed manual setup instructions."""
    print("\n" + "=" * 60)
    print("表格分类整理 - 手动操作指南")
    print("=" * 60)

    print("\n### 第一步：确认字段设置")
    print("-" * 40)
    print("\n请确保以下字段已正确创建：")
    print("\n1. 批次 (文本)")
    print("2. 公司名称 (文本)")
    print("3. 岗位 (文本)")
    print("4. 企业类型 (单选)")
    print("   选项: 民营企业、国企、央企、外企、创业公司、事业单位")
    print("\n5. 行业 (单选)")
    print("   选项: 互联网、金融、制造、教育、医疗、其他")
    print("\n6. 工作城市 (多选) - 重要!")
    print("   选项: 北京、上海、深圳、杭州、广州、成都、其他")
    print("\n7. 学历要求 (单选)")
    print("   选项: 本科、硕士、博士、本科及以上、不限")
    print("\n8. 岗位更新 (日期)")
    print("9. 截止时间 (日期)")
    print("10. 信息来源 (URL)")
    print("11. 内推码 (文本)")

    print("\n\n### 第二步：创建视图")
    print("-" * 40)
    print("\n视图创建步骤：")
    print("1. 点击表格右上角的 \"+\" 图标")
    print("2. 选择 \"表格视图\"")
    print("3. 输入视图名称")
    print("4. 点击筛选器图标，设置筛选条件")
    print("5. 点击排序图标，设置排序规则")
    print("6. 点击保存")

    print("\n\n### 第三步：推荐视图配置")
    print("-" * 40)

    view_configs = [
        {
            "name": "今日更新",
            "filter": "岗位更新 | 是 | 今天",
            "sort": "岗位更新 | 降序"
        },
        {
            "name": "互联网行业",
            "filter": "行业 | 是 | 互联网",
            "sort": "岗位更新 | 降序"
        },
        {
            "name": "央国企",
            "filter": "企业类型 | 包含 | 国企",
            "sort": "岗位更新 | 降序"
        },
        {
            "name": "北京岗位",
            "filter": "工作城市 | 包含 | 北京",
            "sort": "岗位更新 | 降序"
        },
        {
            "name": "上海岗位",
            "filter": "工作城市 | 包含 | 上海",
            "sort": "岗位更新 | 降序"
        }
    ]

    for config in view_configs:
        print(f"\n视图: {config['name']}")
        print(f"  筛选: {config['filter']}")
        print(f"  排序: {config['sort']}")

    print("\n\n### 第四步：创建分组（可选）")
    print("-" * 40)
    print("\n分组可以让数据更清晰：")
    print("\n1. 点击右上角 \"...\" 更多选项")
    print("2. 选择 \"分组\"")
    print("3. 选择分组字段（如：企业类型、行业、工作城市）")
    print("4. 保存分组设置")

    print("\n\n### 第五步：设置表格颜色（美化）")
    print("-" * 40)
    print("\n1. 为不同行业设置不同颜色")
    print("2. 为不同企业类型设置标签颜色")
    print("3. 为紧急岗位（即将截止）设置高亮")

    print("\n\n### 第六步：共享表格")
    print("-" * 40)
    print("\n1. 点击右上角 \"共享\"")
    print("2. 设置分享权限（可查看/可编辑）")
    print("3. 复制分享链接")
    print("4. 分享给目标用户")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    print("=" * 60)
    print("飞书表格分类整理工具")
    print("=" * 60)
    print()

    # Check if credentials are configured
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID]):
        print("错误: 飞书凭证未完整配置")
        print("\n请先在 .env 文件中配置以下内容：")
        print("  FEISHU_APP_ID=")
        print("  FEISHU_APP_SECRET=")
        print("  FEISHU_APP_TOKEN=")
        print("  FEISHU_TABLE_ID=")
        print()
        print_manual_setup_instructions()
        return

    try:
        # Get token
        print("正在连接飞书...")
        token = get_token()
        print("[OK] 连接成功")

        # Get fields
        print("\n正在获取表格字段...")
        fields = get_fields(token)
        print(f"[OK] 找到 {len(fields)} 个字段")

        # Print field list
        print("\n当前字段列表:")
        for f in fields:
            print(f"  - {f.get('field_name', '?')} ({f.get('type', '?')})")

        # Get existing views
        print("\n正在获取现有视图...")
        views = get_table_views(token)
        print(f"[OK] 找到 {len(views)} 个视图")

        if views:
            print("\n现有视图:")
            for v in views:
                print(f"  - {v.get('view_name', '?')}")

        # Print organization guide
        print_organization_guide(fields)

        # Note about API limitations
        print("\n" + "=" * 60)
        print("重要提示")
        print("=" * 60)
        print("\n飞书API目前可能不支持直接通过代码创建视图和筛选器。")
        print("请参考上面的指南，在飞书界面中手动创建视图。")
        print("\n创建视图后，数据写入功能不受影响，可以正常使用。")

        print("\n" + "=" * 60)
        print("整理完成！请按照上述指南在飞书中设置视图。")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
