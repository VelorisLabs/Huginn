"""
PDF批量重命名脚本
功能：为00_inbox_pdfs下各子文件夹中的PDF自动编号
规则：
  - 每个子文件夹独立编号（01_, 02_, 03_...）
  - 按文件修改时间排序
  - 跳过已编号的PDF，续接编号
  - 格式：01_原文件名.pdf, 02_原文件名.pdf
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import time

# 强制 UTF-8 输出
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# 项目根目录下的 PDF 目录
BASE_DIR = Path(__file__).parent.parent / "00_inbox_pdfs"


def extract_current_number(filename: str) -> int:
    """
    从文件名提取编号（如 01_xxx.pdf -> 1）
    如果未编号返回0
    """
    match = re.match(r'^(\d+)[_\-]', filename)
    return int(match.group(1)) if match else 0


def get_max_number_in_folder(folder_path: Path) -> int:
    """获取文件夹中已编号PDF的最大序号"""
    max_num = 0
    for file in folder_path.glob("*.pdf"):
        num = extract_current_number(file.name)
        max_num = max(max_num, num)
    return max_num


def count_unnumbered_pdfs(folder_path: Path) -> int:
    """获取文件夹中未编号PDF的数量"""
    count = 0
    for file in folder_path.glob("*.pdf"):
        if extract_current_number(file.name) == 0:
            count += 1
    return count


def get_unnumbered_pdfs(folder_path: Path) -> List[Tuple[Path, float]]:
    """
    获取未编号的PDF列表，按修改时间排序
    返回：[(文件路径, 修改时间), ...]
    """
    unnumbered = []
    for file in folder_path.glob("*.pdf"):
        if extract_current_number(file.name) == 0:
            mtime = file.stat().st_mtime
            unnumbered.append((file, mtime))

    # 按修改时间排序（从早到晚）
    unnumbered.sort(key=lambda x: x[1])
    return unnumbered


def rename_pdfs_in_folder(folder_path: Path, show_details: bool = False) -> int:
    """
    重命名某个文件夹内的未编号PDF
    返回：重命名的文件数量
    """
    # 获取当前最大编号
    max_num = get_max_number_in_folder(folder_path)

    # 获取未编号的PDF
    unnumbered = get_unnumbered_pdfs(folder_path)

    if not unnumbered:
        return 0

    rename_count = 0
    skipped_count = 0

    for file, _ in unnumbered:
        max_num += 1
        new_name = f"{max_num:02d}_{file.stem}.pdf"
        new_path = folder_path / new_name

        # 检查新文件名是否已存在
        if new_path.exists():
            if show_details:
                print(f"   ⊘ {new_name} (文件已存在)")
            skipped_count += 1
            continue

        # 执行重命名
        file.rename(new_path)
        if show_details:
            print(f"   ✓ {new_name}")
        rename_count += 1

    return rename_count


def get_folder_status(folder_path: Path) -> Tuple[int, int]:
    """获取文件夹中的总PDF数和待编号数"""
    total_pdfs = len(list(folder_path.glob("*.pdf")))
    unnumbered = count_unnumbered_pdfs(folder_path)
    return total_pdfs, unnumbered


def display_folders_with_status(folders_with_status: List[Tuple[Path, int, int]]) -> None:
    """显示所有子文件夹及其待编号PDF数量"""
    print("\n📂 发现以下文件夹:\n")
    for idx, (folder, total, unnumbered) in enumerate(folders_with_status, 1):
        status = f"[{unnumbered}个待编号]" if unnumbered > 0 else "[✓已完成]"
        print(f"  {idx:2d}. {status:12s} {folder.name}")
    print()


def get_user_choice() -> str:
    """获取用户交互选择"""
    print("请选择操作模式:")
    print("  [A] 全部执行 - 对所有待编号的PDF批量编号")
    print("  [S] 选择执行 - 选择特定文件夹编号")
    print("  [Q] 退出\n")

    while True:
        choice = input("输入 [A/S/Q] > ").strip().upper()
        if choice in ('A', 'S', 'Q'):
            return choice
        print("❌ 输入错误，请输入 A、S 或 Q")


def get_folder_selection(folders_with_status: List[Tuple[Path, int, int]]) -> List[int]:
    """获取用户选择的文件夹索引"""
    print("请选择要编号的文件夹 (输入序号，多个用逗号分隔):")
    print("示例: 1,3 (表示选择第1和第3个文件夹)\n")

    while True:
        try:
            user_input = input("输入序号 > ").strip()
            if not user_input:
                print("❌ 请至少选择一个文件夹")
                continue

            indices = [int(x.strip()) - 1 for x in user_input.split(',')]

            # 验证索引范围
            if any(i < 0 or i >= len(folders_with_status) for i in indices):
                print(f"❌ 序号必须在 1-{len(folders_with_status)} 之间")
                continue

            return indices
        except ValueError:
            print("❌ 输入格式错误，请输入数字并用逗号分隔")


def process_folders(folders_with_status: List[Tuple[Path, int, int]], selected_indices: List[int]) -> int:
    """处理选定的文件夹，返回总重命名数"""
    total_renamed = 0

    for idx in selected_indices:
        folder, total, unnumbered = folders_with_status[idx]

        if unnumbered == 0:
            print(f"📁 {folder.name}")
            print(f"   (跳过，无待编号PDF)\n")
            continue

        print(f"📁 {folder.name} ({total}个PDF，{unnumbered}个待编号)")
        renamed = rename_pdfs_in_folder(folder, show_details=True)
        total_renamed += renamed
        print(f"   ✅ 完成 ({renamed}个重命名)\n")

    return total_renamed


def main():
    """主函数：交互式PDF批量重命名"""
    if not BASE_DIR.exists():
        print(f"[ERROR] 路径不存在: {BASE_DIR}")
        return

    # 获取所有有PDF的子文件夹
    all_folders = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()])

    if not all_folders:
        print("[INFO] 没有找到子文件夹")
        return

    # 筛选出有PDF的文件夹，并计算状态
    folders_with_status = []
    for folder in all_folders:
        total, unnumbered = get_folder_status(folder)
        if total > 0:
            folders_with_status.append((folder, total, unnumbered))

    if not folders_with_status:
        print("[INFO] 没有找到包含PDF的文件夹")
        return

    # 显示文件夹列表
    display_folders_with_status(folders_with_status)

    # 获取用户选择
    choice = get_user_choice()

    if choice == 'Q':
        print("👋 已退出")
        return

    # 确定要处理的文件夹
    if choice == 'A':
        selected_indices = list(range(len(folders_with_status)))
    else:  # choice == 'S'
        selected_indices = get_folder_selection(folders_with_status)

    print()

    # 执行重命名
    total_renamed = process_folders(folders_with_status, selected_indices)

    print(f"✅ 完成！共重命名 {total_renamed} 个PDF文件")


if __name__ == "__main__":
    main()
