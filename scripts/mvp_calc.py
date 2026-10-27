"""CLI 回归工具：无 UI 直接计算货款并写出 结果.xlsx。

用法：
    python scripts/mvp_calc.py --material1 材料1.xlsx --material2 材料2.xlsx --out 结果.xlsx
"""

import argparse
import os
import sys

# 允许从仓库根目录运行：把父目录加入 sys.path 以 import mvp_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_core import compute_payment, build_result  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="粤通卡日报 MVP 计算 CLI")
    parser.add_argument("--material1", required=True, help="材料1.xlsx 路径（含「产品数量」）")
    parser.add_argument("--material2", required=True, help="材料2.xlsx 路径（含「单价」）")
    parser.add_argument("--out", required=True, help="输出的 结果.xlsx 路径")
    args = parser.parse_args()

    value = compute_payment(args.material1, args.material2)
    build_result(args.out, value)
    print(f"货款 = {value}")
    print(f"已写出: {args.out}")


if __name__ == "__main__":
    main()
