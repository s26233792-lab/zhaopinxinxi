# -*- coding: utf-8 -*-
"""
Demo crawler that generates sample recruitment data.
This is for testing the full pipeline before implementing real web scrapers.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from crawlers.base import BaseCrawler


class DemoCrawler(BaseCrawler):
    """
    Demo crawler that generates realistic sample recruitment data.
    Useful for testing the Feishu integration pipeline.
    """

    # Sample data
    COMPANIES = [
        "字节跳动", "腾讯", "阿里巴巴", "美团", "京东",
        "百度", "网易", "小米", "华为", "滴滴出行",
        "快手", "拼多多", "哔哩哔哩", "小红书", "蚂蚁集团"
    ]

    POSITIONS = [
        "后端开发工程师", "前端开发工程师", "算法工程师",
        "产品经理", "数据分析师", "UI设计师",
        "测试工程师", "运维工程师", "Java开发", "Python开发"
    ]

    INDUSTRIES = ["互联网", "金融", "制造", "教育", "医疗"]
    COMPANY_TYPES = ["民营企业", "国企", "央企", "外企", "创业公司"]
    EDUCATIONS = ["本科", "硕士", "博士", "本科及以上"]
    CITIES = [["北京"], ["上海"], ["深圳"], ["杭州"], ["北京", "上海"],
              ["广州"], ["成都"], ["武汉"], ["南京"], ["西安"]]

    def __init__(self):
        super().__init__(
            name="demo",
            base_url="https://demo.example.com"
        )

    def fetch_records(self, count: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate sample recruitment records.

        Args:
            count: Number of records to generate
            **kwargs: Additional parameters (ignored)

        Returns:
            List of normalized recruitment records
        """
        records = []

        for i in range(count):
            record = self._generate_record(i)
            records.append(record)

        return records

    def _generate_record(self, index: int) -> Dict[str, Any]:
        """Generate a single sample record."""
        company = random.choice(self.COMPANIES)
        position = random.choice(self.POSITIONS)
        industry = random.choice(self.INDUSTRIES)
        company_type = random.choice(self.COMPANY_TYPES)
        education = random.choice(self.EDUCATIONS)
        cities = random.choice(self.CITIES)

        # Generate dates
        today = datetime.now()
        publish_date = today - timedelta(days=random.randint(0, 30))
        deadline = today + timedelta(days=random.randint(7, 60))

        # Determine batch based on current month
        month = today.month
        if month >= 9 and month <= 11:
            batch = random.choice(["秋招提前批", "秋招", "秋招补录"])
        elif month >= 2 and month <= 5:
            batch = random.choice(["春招提前批", "春招", "春招补录"])
        else:
            batch = random.choice(["暑期实习", "寒假实习", "日常实习"])

        # Some companies don't require written test
        no_written_test = random.random() < 0.3

        # Generate referral code (optional)
        referral_code = ""
        if random.random() < 0.5:
            referral_code = f"{company[:2].upper()}{''.join(random.choices('0123456789', k=4))}"

        record = {
            "批次": batch,
            "公司名称": company,
            "企业类型": company_type,
            "行业": industry,
            "工作城市": cities,
            "岗位": position,
            "学历要求": education,
            "免笔试": no_written_test,
            "信息来源": f"https://example.com/job/{index}",
            "内推码": referral_code,
            "publish_date": publish_date,
            "deadline": deadline
        }

        return self.normalize_record(record)

    def normalize_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the generated record to our standard format."""
        normalized = {
            "批次": raw_record.get("批次", ""),
            "公司名称": raw_record.get("公司名称", ""),
            "企业类型": raw_record.get("企业类型", ""),
            "行业": raw_record.get("行业", ""),
            "工作城市": raw_record.get("工作城市", []),
            "岗位": raw_record.get("岗位", ""),
            "学历要求": raw_record.get("学历要求", ""),
            "免笔试": raw_record.get("免笔试", False),
            "信息来源": raw_record.get("信息来源", ""),
            "内推码": raw_record.get("内推码", ""),
        }
        return normalized


def main():
    """Test the demo crawler."""
    print("=" * 50)
    print("演示爬虫测试")
    print("=" * 50)
    print()

    crawler = DemoCrawler()
    records = crawler.run(count=10)

    print()
    print(f"生成了 {len(records)} 条招聘信息：")
    print()

    for i, record in enumerate(records, 1):
        print(f"{i}. {record['公司名称']} - {record['岗位']}")
        print(f"   批次: {record['批次']}")
        print(f"   城市: {', '.join(record['工作城市'])}")
        print(f"   学历: {record['学历要求']}")
        print(f"   免笔试: {'是' if record['免笔试'] else '否'}")
        print()

    return records


if __name__ == "__main__":
    main()
