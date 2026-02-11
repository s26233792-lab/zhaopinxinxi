# -*- coding: utf-8 -*-
"""
Hybrid data source manager - supports multiple data input methods.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch recruitment records from this source.

        Returns:
            List of normalized recruitment records
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        pass


class ManualInputSource(DataSource):
    """
    Manual input via command line interface.
    Allows users to manually input recruitment information.
    """

    def get_source_name(self) -> str:
        return "手动输入"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Interactive manual input.
        Returns:
            List of manually entered records
        """
        records = []

        print("\n=== 手动输入招聘信息 ===")
        print("输入完成后直接回车跳过，输入 'q' 退出\n")

        while True:
            record = self._input_record()
            if record is None:  # User wants to exit
                break
            if record:  # Valid record
                records.append(record)

            # Ask if user wants to continue
            if input("\n继续输入？(y/n): ").lower() != 'y':
                break

        return records

    def _input_record(self) -> Optional[Dict[str, Any]]:
        """Input a single record."""
        record = {}

        # Company name (required)
        company = input("公司名称: ").strip()
        if company.lower() == 'q' or not company:
            return None
        record["公司名称"] = company

        # Position (required)
        position = input("岗位名称: ").strip()
        if not position:
            return None
        record["岗位"] = position

        # Optional fields
        batch = input("招聘批次（如：春招、秋招，回车跳过）: ").strip()
        if batch:
            record["批次"] = batch
        else:
            record["批次"] = "春招"  # Default

        company_type = input("企业类型（民营/国企/央企/外企，回车跳过）: ").strip()
        record["企业类型"] = company_type or "民营企业"

        industry = input("行业（互联网/金融/制造等，回车跳过）: ").strip()
        record["行业"] = industry or "互联网"

        cities = input("工作城市（多个用空格分隔，回车跳过）: ").strip()
        record["工作城市"] = cities.split() if cities else ["北京"]

        education = input("学历要求（本科/硕士/博士，回车跳过）: ").strip()
        record["学历要求"] = education or "本科及以上"

        no_test = input("免笔试？(y/n，回车跳过): ").strip().lower()
        record["免笔试"] = no_test == 'y'

        source = input("信息来源链接（回车跳过）: ").strip()
        record["信息来源"] = source or "手动录入"

        referral = input("内推码（回车跳过）: ").strip()
        record["内推码"] = referral

        return record


class FileImportSource(DataSource):
    """
    Import from file (JSON/CSV/TXT).
    Allows batch import from local files.
    """

    def get_source_name(self) -> str:
        return "文件导入"

    def fetch(self) -> List[Dict[str, Any]]:
        """Import from file."""
        print("\n=== 文件导入 ===")
        print("支持的文件格式：JSON, CSV, TXT")

        filepath = input("请输入文件路径: ").strip()

        if not filepath or not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            return []

        extension = os.path.splitext(filepath)[1].lower()

        try:
            if extension == '.json':
                return self._import_json(filepath)
            elif extension == '.csv':
                return self._import_csv(filepath)
            elif extension == '.txt':
                return self._import_txt(filepath)
            else:
                print(f"不支持的文件格式: {extension}")
                return []
        except Exception as e:
            print(f"导入失败: {e}")
            return []

    def _import_json(self, filepath: str) -> List[Dict[str, Any]]:
        """Import from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'records' in data:
            return data['records']
        else:
            return []

    def _import_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Import from CSV file."""
        import csv

        records = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert to our format
                record = {
                    "公司名称": row.get("公司名称", ""),
                    "岗位": row.get("岗位", row.get("职位", "")),
                    "批次": row.get("批次", "春招"),
                    "企业类型": row.get("企业类型", "民营企业"),
                    "行业": row.get("行业", "互联网"),
                    "工作城市": row.get("工作城市", "北京").split(","),
                    "学历要求": row.get("学历要求", "本科及以上"),
                    "免笔试": row.get("免笔试", "false").lower() == "true",
                    "信息来源": row.get("信息来源", "文件导入"),
                    "内推码": row.get("内推码", ""),
                }
                records.append(record)

        return records

    def _import_txt(self, filepath: str) -> List[Dict[str, Any]]:
        """Import from text file (one record per line)."""
        records = []

        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # Parse format: 公司名,岗位名,行业,城市
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    record = {
                        "公司名称": parts[0],
                        "岗位": parts[1],
                        "批次": "春招",
                        "企业类型": "民营企业",
                        "行业": parts[2] if len(parts) > 2 else "互联网",
                        "工作城市": [parts[3]] if len(parts) > 3 else ["北京"],
                        "学历要求": "本科及以上",
                        "免笔试": False,
                        "信息来源": f"文件导入 (行{line_num})",
                        "内推码": "",
                    }
                    records.append(record)

        return records


class DemoDataSource(DataSource):
    """
    Demo data source for testing.
    Generates realistic sample data.
    """

    def get_source_name(self) -> str:
        return "演示数据"

    def __init__(self, count: int = 10):
        self.count = count

    def fetch(self) -> List[Dict[str, Any]]:
        """Generate demo records."""
        from crawlers.demo_crawler import DemoCrawler

        crawler = DemoCrawler()
        return crawler.run(count=self.count)


class HybridDataCollector:
    """
    Hybrid data collector that supports multiple data sources.
    """

    def __init__(self):
        """Initialize the collector."""
        self.sources = {
            "1": ("手动输入", ManualInputSource()),
            "2": ("文件导入", FileImportSource()),
            "3": ("演示数据", DemoDataSource(count=10)),
        }

    def show_menu(self):
        """Display data source menu."""
        print("\n" + "=" * 50)
        print("招聘信息数据源选择")
        print("=" * 50)
        for key, (name, _) in self.sources.items():
            print(f"{key}. {name}")
        print("0. 退出")
        print()

    def run(self) -> List[Dict[str, Any]]:
        """
        Run the data collector.
        Returns:
            List of all collected records
        """
        all_records = []

        while True:
            self.show_menu()
            choice = input("请选择数据源（可多选，用空格分隔，如: 1 3）: ").strip()

            if choice == "0":
                break

            selected = choice.split()
            valid_choices = [c for c in selected if c in self.sources]

            if not valid_choices:
                print("无效的选择，请重试")
                continue

            for choice_key in valid_choices:
                _, source = self.sources[choice_key]
                print(f"\n正在从 {source.get_source_name()} 获取数据...")
                records = source.fetch()
                print(f"[OK] 获取到 {len(records)} 条记录")
                all_records.extend(records)

                # Ask if user wants to continue with more sources
                if len(all_records) > 0:
                    cont = input("\n是否继续添加其他数据源？(y/n): ").strip().lower()
                    if cont != 'y':
                        break

            break

        return all_records


def main():
    """Test the hybrid data collector."""
    collector = HybridDataCollector()
    records = collector.run()

    print(f"\n总共收集到 {len(records)} 条记录")

    if records:
        print("\n数据预览:")
        for i, record in enumerate(records[:5], 1):
            print(f"{i}. {record.get('公司名称')} - {record.get('岗位')}")

    return records


if __name__ == "__main__":
    main()
