"""
论文身份卡自动提取脚本 v2.1 (重构版)
============================================================
功能：
1. 自动同步主题桶配置到文件夹结构
2. 支持按主题桶分文件夹管理PDF
3. 交互式选择处理哪些文件夹
4. 支持断点续跑 / 覆盖重跑
5. JSON按文件夹分组存储，CSV分文件夹+总汇总

使用方法：
============================================================
1. 设置环境变量：
   Windows CMD:    set DEEPSEEK_API_KEY=your_key
   Windows PS:     $env:DEEPSEEK_API_KEY="your_key"
   Linux/Mac:      export DEEPSEEK_API_KEY="your_key"

2. 安装依赖：
   pip install openai pymupdf

3. 运行脚本：
   python auto_runner.py
"""

import time
import json
from pathlib import Path

# 从核心模块导入
from .core import (
    # 配置
    PDF_DIR, JSON_DIR, CSV_DIR, PROMPT_FILE, THEME_FILE,
    REQUEST_INTERVAL, ALL_CSV_NAME, ERROR_LOG,
    # 模型
    FolderStatus,
    # 工具函数
    print_separator, print_header,
    get_display_width, pad_center, pad_left,
    log_error, extract_number_from_filename,
    # PDF 处理
    extract_pdf_text,
    # LLM 客户端
    test_api_connection, call_llm, clean_json_response,
    # CSV 处理
    init_csv, append_to_csv,
)


# ============================================================
# 步骤1: 检查配置文件
# ============================================================
def check_required_files() -> bool:
    """检查必要文件是否存在"""
    print("\n📁 检查配置文件...")
    all_ok = True
    
    checks = [
        (PROMPT_FILE, "Prompt模板"),
        (THEME_FILE, "主题桶配置"),
    ]
    
    for path, name in checks:
        if path.exists():
            print(f"   ✅ {name}: {path.name}")
        else:
            print(f"   ❌ {name}不存在: {path}")
            all_ok = False
    
    # PDF目录不存在则创建
    if not PDF_DIR.exists():
        PDF_DIR.mkdir(parents=True)
        print(f"   ✅ PDF目录: {PDF_DIR.name} (已创建)")
    else:
        print(f"   ✅ PDF目录: {PDF_DIR.name}")
    
    return all_ok


# ============================================================
# 步骤2: 同步文件夹结构
# ============================================================
def parse_theme_buckets() -> list[str]:
    """从主题桶配置文件解析一级主题名称"""
    content = THEME_FILE.read_text(encoding='utf-8')
    themes = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('##'):
            theme_name = line.lstrip('#').strip()
            if theme_name:
                themes.append(theme_name)
    return themes


def sync_folder_structure() -> None:
    """根据主题桶配置同步文件夹结构"""
    print("\n📂 同步文件夹结构...")
    
    themes = parse_theme_buckets()
    print(f"   从主题桶配置中解析到 {len(themes)} 个主题")
    
    if not themes:
        print("   ⚠️ 未解析到任何主题，请检查theme_buckets.md格式")
        return
    
    # 获取已存在的文件夹
    existing_folders = set()
    if PDF_DIR.exists():
        for item in PDF_DIR.iterdir():
            if item.is_dir():
                existing_folders.add(item.name)
    
    # 创建缺失的文件夹
    created_count = 0
    for theme in themes:
        folder_path = PDF_DIR / theme
        if theme not in existing_folders:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ 新建: {theme}")
            created_count += 1
    
    skipped_count = len(themes) - created_count
    if skipped_count > 0:
        print(f"   ⏩ 已存在: {skipped_count} 个文件夹（跳过）")
    
    print("   同步完成")


# ============================================================
# 步骤3: 扫描PDF文件
# ============================================================
def get_json_path_for_pdf(pdf_path: Path, folder_name: str) -> Path:
    """根据PDF路径生成对应的JSON路径"""
    return JSON_DIR / folder_name / (pdf_path.stem + ".json")


def scan_folders() -> tuple[list[FolderStatus], list[Path]]:
    """
    扫描PDF目录
    返回: (有PDF的文件夹列表, 根目录散落的PDF列表)
    """
    folders = {}
    root_pdfs = []
    
    # 扫描所有PDF
    for item in PDF_DIR.iterdir():
        if item.is_file() and item.suffix.lower() == '.pdf':
            root_pdfs.append(item)
        elif item.is_dir():
            folder_name = item.name
            pdf_files = sorted(
                [f for f in item.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'],
                key=lambda x: x.name
            )
            
            if pdf_files:
                folder = FolderStatus(
                    name=folder_name,
                    path=item,
                    total_pdfs=len(pdf_files),
                    pdf_files=pdf_files
                )
                
                for pdf_path in pdf_files:
                    json_path = get_json_path_for_pdf(pdf_path, folder_name)
                    if json_path.exists():
                        folder.processed += 1
                    else:
                        folder.pending += 1
                
                folders[folder_name] = folder
    
    result = list(folders.values())
    result.sort(key=lambda x: x.name)
    
    return result, root_pdfs


def display_folder_status(folders: list[FolderStatus], root_pdfs: list[Path], empty_folder_count: int):
    """显示文件夹状态表"""
    print("\n📊 扫描PDF文件...")
    
    if root_pdfs:
        print(f"\n   ⚠️ 警告: 发现 {len(root_pdfs)} 个PDF在根目录，请移到子文件夹")
        for pdf in root_pdfs[:5]:
            print(f"      - {pdf.name}")
        if len(root_pdfs) > 5:
            print(f"      ... 等共 {len(root_pdfs)} 个文件")
        print("   这些文件将被跳过")
    
    if not folders:
        print("\n   ⚠️ 未找到任何PDF文件（请将PDF放入子文件夹中）")
        return
    
    COL_NO = 6
    COL_NAME = 32
    COL_NUM = 8

    print()
    print(f"┌{'─'*COL_NO}┬{'─'*COL_NAME}┬{'─'*COL_NUM}┬{'─'*COL_NUM}┬{'─'*COL_NUM}┐")
    print(f"│{pad_center('序号', COL_NO)}│{pad_center('文件夹名称', COL_NAME)}│{pad_center('PDF总数', COL_NUM)}│{pad_center('已处理', COL_NUM)}│{pad_center('待处理', COL_NUM)}│")
    print(f"├{'─'*COL_NO}┼{'─'*COL_NAME}┼{'─'*COL_NUM}┼{'─'*COL_NUM}┼{'─'*COL_NUM}┤")

    for i, folder in enumerate(folders, 1):
        name_display = folder.name
        if get_display_width(name_display) > COL_NAME - 2:
            while get_display_width(name_display + "...") > COL_NAME - 2:
                name_display = name_display[:-1]
            name_display = name_display + "..."

        no_str = f"[{i}]"
        print(f"│{pad_center(no_str, COL_NO)}│ {pad_left(name_display, COL_NAME - 1)}│{pad_center(str(folder.total_pdfs), COL_NUM)}│{pad_center(str(folder.processed), COL_NUM)}│{pad_center(str(folder.pending), COL_NUM)}│")

    total_pdfs = sum(f.total_pdfs for f in folders)
    total_processed = sum(f.processed for f in folders)
    total_pending = sum(f.pending for f in folders)

    print(f"├{'─'*COL_NO}┼{'─'*COL_NAME}┼{'─'*COL_NUM}┼{'─'*COL_NUM}┼{'─'*COL_NUM}┤")
    print(f"│{pad_center('合计', COL_NO)}│{' '*COL_NAME}│{pad_center(str(total_pdfs), COL_NUM)}│{pad_center(str(total_processed), COL_NUM)}│{pad_center(str(total_pending), COL_NUM)}│")
    print(f"└{'─'*COL_NO}┴{'─'*COL_NAME}┴{'─'*COL_NUM}┴{'─'*COL_NUM}┴{'─'*COL_NUM}┘")
    
    if empty_folder_count > 0:
        print(f"\n   💡 提示: 有 {empty_folder_count} 个空文件夹未显示（无PDF）")


# ============================================================
# 步骤4: 用户交互
# ============================================================
def get_user_choice(folders: list[FolderStatus]) -> tuple[str, list[int], bool]:
    """获取用户选择"""
    print("\n请选择操作模式:")
    print("  [A] 全部执行 - 处理所有待处理的PDF（跳过已处理）")
    print("  [R] 全部重跑 - 重新处理所有PDF（覆盖已有结果）")
    print("  [S] 选择执行 - 选择特定文件夹处理")
    print("  [Q] 退出")
    print()
    
    while True:
        choice = input("请输入选项 [A/R/S/Q]: ").strip().upper()
        
        if choice == 'Q':
            return ('quit', [], False)
        
        elif choice == 'A':
            indices = [i for i, f in enumerate(folders) if f.pending > 0]
            if not indices:
                print("   ⚠️ 没有待处理的文件")
                return ('quit', [], False)
            return ('all', indices, False)
        
        elif choice == 'R':
            confirm = input("   ⚠️ 确认覆盖所有已处理的结果? [y/N]: ").strip().lower()
            if confirm == 'y':
                indices = [i for i, f in enumerate(folders) if f.total_pdfs > 0]
                return ('all', indices, True)
            else:
                print("   已取消")
                continue
        
        elif choice == 'S':
            return get_folder_selection(folders)
        
        else:
            print("   ❌ 无效选项，请重新输入")


def get_folder_selection(folders: list[FolderStatus]) -> tuple[str, list[int], bool]:
    """获取用户选择的文件夹"""
    print()
    print("请输入要处理的文件夹序号:")
    print("  - 单个: 1")
    print("  - 多个: 1,3,5")
    print("  - 范围: 1-5")
    print("  - 混合: 1,3-5,7")
    print("  - 返回: B")
    print()
    
    while True:
        selection = input("请输入序号: ").strip()
        
        if selection.upper() == 'B':
            return get_user_choice(folders)
        
        try:
            indices = parse_selection(selection, len(folders))
            if not indices:
                print("   ❌ 未选择任何文件夹")
                continue
            
            print(f"\n   已选择 {len(indices)} 个文件夹:")
            for i in indices:
                f = folders[i]
                print(f"     - {f.name} (待处理: {f.pending})")
            
            has_processed = any(folders[i].processed > 0 for i in indices)
            overwrite = False
            if has_processed:
                print()
                print("   检测到已有处理结果，请选择:")
                print("   [N] 跳过已处理（默认）")
                print("   [O] 覆盖已处理")
                ow_choice = input("   请选择 [N/O]: ").strip().upper()
                overwrite = (ow_choice == 'O')
            
            confirm = input("\n   确认开始处理? [Y/n]: ").strip().lower()
            if confirm in ('', 'y', 'yes'):
                return ('select', indices, overwrite)
            else:
                print("   已取消")
                continue
                
        except ValueError as e:
            print(f"   ❌ {e}")
            continue


def parse_selection(selection: str, max_num: int) -> list[int]:
    """解析用户输入的序号"""
    indices = set()
    parts = selection.replace(' ', '').split(',')
    
    for part in parts:
        if not part:
            continue
        if '-' in part:
            try:
                start, end = part.split('-')
                start, end = int(start), int(end)
                if start < 1 or end > max_num or start > end:
                    raise ValueError(f"范围 {part} 无效")
                indices.update(range(start - 1, end))
            except (ValueError, IndexError):
                raise ValueError(f"无法解析范围: {part}")
        else:
            try:
                num = int(part)
                if num < 1 or num > max_num:
                    raise ValueError(f"序号 {num} 超出范围 (1-{max_num})")
                indices.add(num - 1)
            except ValueError:
                raise ValueError(f"无法解析序号: {part}")
    
    return sorted(list(indices))


# ============================================================
# 步骤5: 核心处理逻辑
# ============================================================
def load_theme_buckets() -> str:
    """读取主题桶配置文件内容"""
    return THEME_FILE.read_text(encoding='utf-8')


def load_prompt_template() -> str:
    """读取Prompt模板"""
    return PROMPT_FILE.read_text(encoding='utf-8')


def build_full_prompt(prompt_template: str, theme_content: str, pdf_text: str) -> str:
    """构建完整的Prompt"""
    prompt_with_theme = prompt_template.replace("{THEME_BUCKETS}", theme_content)
    return f"""{prompt_with_theme}

---

以下是论文的全文内容，请按照上述要求进行信息提取：

{pdf_text}
"""


def process_folder(
    folder: FolderStatus,
    prompt_template: str,
    theme_content: str,
    overwrite: bool = False,
    global_index_start: int = 1
) -> tuple[dict, int]:
    """处理单个文件夹"""
    stats = {"success": 0, "skip": 0, "fail": 0}
    global_index = global_index_start
    
    json_folder = JSON_DIR / folder.name
    json_folder.mkdir(parents=True, exist_ok=True)
    
    csv_path = CSV_DIR / f"{folder.name}.csv"
    all_csv_path = CSV_DIR / ALL_CSV_NAME
    
    if overwrite and csv_path.exists():
        csv_path.unlink()
    
    init_csv(csv_path)
    init_csv(all_csv_path)
    
    to_process = []
    for pdf_path in folder.pdf_files:
        json_path = json_folder / (pdf_path.stem + ".json")
        if overwrite or not json_path.exists():
            to_process.append(pdf_path)
        else:
            stats["skip"] += 1
    
    if not to_process:
        return stats, global_index
    
    for i, pdf_path in enumerate(to_process, 1):
        json_path = json_folder / (pdf_path.stem + ".json")
        
        print(f"\n   [{i}/{len(to_process)}] {pdf_path.name}")
        
        try:
            print(f"      📄 提取文本...", end=" ")
            pdf_text = extract_pdf_text(pdf_path)
            print(f"{len(pdf_text)}字符")
            
            print(f"      🤖 调用LLM...")
            start_time = time.time()
            response_text = call_llm(
                build_full_prompt(prompt_template, theme_content, pdf_text)
            )
            elapsed = time.time() - start_time
            print(f"      ✅ 响应完成 ({elapsed:.1f}秒)")
            
            clean_text = clean_json_response(response_text)
            data = json.loads(clean_text)
            
            data["source_folder"] = folder.name
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"      💾 JSON 保存成功")
            
            local_index = extract_number_from_filename(pdf_path.name)

            append_to_csv(csv_path, data, index_value=local_index)
            append_to_csv(all_csv_path, data, index_value=str(global_index))
            print(f"      📝 CSV 更新成功 (本地编号: {local_index}, 全局编号: {global_index})")

            stats["success"] += 1
            global_index += 1
            
        except json.JSONDecodeError as e:
            print(f"      ❌ JSON解析失败: {e}")
            stats["fail"] += 1
            log_error(pdf_path.name, f"JSON解析失败: {e}")
            
        except Exception as e:
            print(f"      ❌ 处理失败: {e}")
            stats["fail"] += 1
            log_error(pdf_path.name, str(e))
        
        if i < len(to_process):
            print(f"      ⏳ 等待{REQUEST_INTERVAL}秒...")
            time.sleep(REQUEST_INTERVAL)

    return stats, global_index


# ============================================================
# 主函数
# ============================================================
def main():
    print_header("📚 论文身份卡自动提取工具 v2.1")
    
    if not check_required_files():
        print("\n⚠️ 请检查配置文件后重试")
        return
    
    sync_folder_structure()
    
    if not test_api_connection():
        print("\n⚠️ API连接失败，请检查配置")
        return
    
    folders, root_pdfs = scan_folders()
    
    themes = parse_theme_buckets()
    existing_folder_names = {f.name for f in folders}
    empty_folder_count = len([t for t in themes if t not in existing_folder_names])
    
    display_folder_status(folders, root_pdfs, empty_folder_count)
    
    if not folders:
        return
    
    mode, selected_indices, overwrite = get_user_choice(folders)
    
    if mode == 'quit':
        print("\n👋 已退出")
        return
    
    print("\n📂 加载配置文件...")
    prompt_template = load_prompt_template()
    theme_content = load_theme_buckets()
    print("   ✅ 配置已加载")
    
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    total_stats = {"success": 0, "skip": 0, "fail": 0}
    global_index = 1

    for idx in selected_indices:
        folder = folders[idx]

        if not overwrite and folder.pending == 0:
            continue

        print_separator("-")
        print("🚀 开始任务")
        print_separator("-")
        print(f"📁 正在处理: {folder.name}")
        print(f"   PDF数量: {folder.total_pdfs} | 已处理: {folder.processed} | 待处理: {folder.pending}")
        print_separator("-")

        stats, global_index = process_folder(
            folder, prompt_template, theme_content, overwrite, global_index
        )

        for key in total_stats:
            total_stats[key] += stats[key]

        print(f"\n   📊 本文件夹完成: 成功 {stats['success']} | 跳过 {stats['skip']} | 失败 {stats['fail']}")
    
    print_separator()
    print("📊 全部处理完成")
    print_separator()
    print(f"   ✅ 成功: {total_stats['success']}")
    print(f"   ⏩ 跳过: {total_stats['skip']}")
    print(f"   ❌ 失败: {total_stats['fail']}")
    print()
    print(f"   📂 输出位置:")
    print(f"      JSON: {JSON_DIR}/")
    print(f"      CSV:  {CSV_DIR}/")
    print(f"      汇总: {CSV_DIR / ALL_CSV_NAME}")
    
    if total_stats["fail"] > 0:
        print(f"      错误日志: {ERROR_LOG}")
    
    print_separator()


if __name__ == "__main__":
    main()
