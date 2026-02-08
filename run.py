#!/usr/bin/env python
"""
论文身份卡自动提取系统 - 统一命令行入口
==========================================

使用方法：
    python run.py extract      # P0: 提取论文信息
    python run.py rescore      # P1: 场景重算评分
    python run.py cluster      # P2: 聚类分析
    python run.py visualize    # P3: 生成可视化图表
    python run.py export       # P3: 导出静态HTML
    python run.py api          # 启动 FastAPI 后端服务
    python run.py full         # 运行完整流水线 (extract → rescore → cluster)

示例：
    python run.py extract                    # 交互式提取
    python run.py rescore                    # 场景重算
    python run.py api                        # 启动后端API
    python run.py full                       # 完整流水线
"""

import sys
import subprocess
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.resolve()
SRC_DIR = ROOT_DIR / "src"
API_DIR = ROOT_DIR / "api"
FRONTEND_DIR = ROOT_DIR / "frontend"


def run_extract():
    """运行 P0 提取脚本"""
    print("=" * 60)
    print("  📄 P0: 论文信息提取")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "src.extraction"], cwd=ROOT_DIR)


def run_rescore():
    """运行 P1 场景重算脚本"""
    print("=" * 60)
    print("  🎯 P1: 场景重算评分")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "src.rescoring"], cwd=ROOT_DIR)


def run_cluster():
    """运行 P2 聚类分析脚本"""
    print("=" * 60)
    print("  🔗 P2: 聚类分析")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "src.clustering"], cwd=ROOT_DIR)


def run_visualize():
    """运行 P3 可视化脚本"""
    print("=" * 60)
    print("  📊 P3: 生成可视化图表")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "src.visualize"], cwd=ROOT_DIR)


def run_export():
    """运行 P3 静态HTML导出"""
    print("=" * 60)
    print("  🌐 P3: 导出静态HTML")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "src.static_export"], cwd=ROOT_DIR)


def run_api():
    """启动 FastAPI 后端服务"""
    print("=" * 60)
    print("  🚀 启动 FastAPI 后端服务")
    print("=" * 60)
    print(f"  📁 API 目录: {API_DIR}")
    print("  🌐 API 地址: http://localhost:8000")
    print("  📖 API 文档: http://localhost:8000/api/v1/docs")
    print("=" * 60)
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "api.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ], cwd=ROOT_DIR)


def run_full_pipeline():
    """运行完整流水线"""
    print("=" * 60)
    print("  🔄 运行完整流水线")
    print("=" * 60)
    
    steps = [
        ("P0: 提取", run_extract),
        ("P1: 重算", run_rescore),
        ("P2: 聚类", run_cluster),
    ]
    
    for name, func in steps:
        print(f"\n>>> {name}")
        func()
    
    print("\n" + "=" * 60)
    print("  ✅ 流水线完成!")
    print("=" * 60)


def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("可用命令:")
    print("  extract   - P0: 提取论文信息")
    print("  rescore   - P1: 场景重算评分")
    print("  cluster   - P2: 聚类分析")
    print("  visualize - P3: 生成可视化图表")
    print("  export    - P3: 导出静态HTML")
    print("  api       - 启动 FastAPI 后端服务")
    print("  full      - 运行完整流水线")
    print("  help      - 显示此帮助信息")


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "extract": run_extract,
        "rescore": run_rescore,
        "cluster": run_cluster,
        "visualize": run_visualize,
        "export": run_export,
        "api": run_api,
        "server": run_api,
        "full": run_full_pipeline,
        "all": run_full_pipeline,
        "help": show_help,
        "-h": show_help,
        "--help": show_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ 未知命令: {command}")
        print("运行 'python run.py help' 查看可用命令")
        sys.exit(1)


if __name__ == "__main__":
    main()
