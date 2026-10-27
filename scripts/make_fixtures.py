"""生成假材料样例（仅供自测，非真实业务数据）。

用法：
    python scripts/make_fixtures.py
将创建 fixtures/材料1.xlsx（产品数量=25）与 fixtures/材料2.xlsx（单价=4），
预期计算 货款 = 25 × 4 = 100。
"""

import os

from openpyxl import Workbook

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX_DIR = os.path.join(BASE, "fixtures")


def main():
    os.makedirs(FIX_DIR, exist_ok=True)

    wb1 = Workbook()
    ws1 = wb1.active
    ws1.title = "材料1"
    ws1.append(["产品数量"])
    ws1.append([25])
    wb1.save(os.path.join(FIX_DIR, "材料1.xlsx"))

    wb2 = Workbook()
    ws2 = wb2.active
    ws2.title = "材料2"
    ws2.append(["单价"])
    ws2.append([4])
    wb2.save(os.path.join(FIX_DIR, "材料2.xlsx"))

    print("已生成 fixtures：")
    print("  ", os.path.join(FIX_DIR, "材料1.xlsx"), "(产品数量=25)")
    print("  ", os.path.join(FIX_DIR, "材料2.xlsx"), "(单价=4)")


if __name__ == "__main__":
    main()
