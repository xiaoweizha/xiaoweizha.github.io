#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import datetime

def list_documents():
    """列出知识库中的所有文档"""
    print("📚 知识库文档列表")
    print("=" * 60)

    storage_path = Path("./storage")

    if not storage_path.exists():
        print("❌ 存储目录不存在")
        return

    documents = list(storage_path.glob("*"))

    if not documents:
        print("📝 知识库为空，暂无文档")
        return

    print(f"📊 共找到 {len(documents)} 个文档：\n")

    # 按修改时间排序
    documents.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for i, doc_path in enumerate(documents, 1):
        if doc_path.is_file():
            # 解析文件信息
            filename = doc_path.name
            doc_id = filename.split('_')[0] if '_' in filename else "unknown"
            original_name = '_'.join(filename.split('_')[1:]) if '_' in filename else filename

            # 文件统计信息
            file_size = doc_path.stat().st_size
            size_str = format_size(file_size)

            # 修改时间
            mod_time = datetime.fromtimestamp(doc_path.stat().st_mtime)
            time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

            # 文件类型
            file_ext = doc_path.suffix.lower()
            file_type = get_file_type(file_ext)

            print(f"{i}. 📄 {original_name}")
            print(f"   🔑 ID: {doc_id}")
            print(f"   📊 大小: {size_str}")
            print(f"   📅 上传时间: {time_str}")
            print(f"   🏷️  类型: {file_type}")
            print(f"   📁 路径: {doc_path}")
            print()

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_file_type(extension):
    """获取文件类型描述"""
    type_map = {
        '.pdf': 'PDF文档',
        '.docx': 'Word文档',
        '.doc': 'Word文档',
        '.txt': '文本文件',
        '.md': 'Markdown文档',
        '.html': 'HTML文档',
        '.xlsx': 'Excel表格',
        '.xls': 'Excel表格',
        '.pptx': 'PowerPoint演示文稿',
        '.ppt': 'PowerPoint演示文稿'
    }
    return type_map.get(extension, f"{extension.upper()}文件")

def show_document_details(doc_id):
    """显示特定文档的详细信息"""
    storage_path = Path("./storage")

    # 查找匹配的文档
    for doc_path in storage_path.glob(f"{doc_id}_*"):
        print(f"\n📄 文档详细信息")
        print("=" * 40)

        # 基本信息
        filename = doc_path.name
        original_name = '_'.join(filename.split('_')[1:])
        file_size = format_size(doc_path.stat().st_size)
        mod_time = datetime.fromtimestamp(doc_path.stat().st_mtime)

        print(f"原始文件名: {original_name}")
        print(f"文档ID: {doc_id}")
        print(f"文件大小: {file_size}")
        print(f"上传时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"存储路径: {doc_path}")

        # 如果是文本文件，显示内容预览
        if doc_path.suffix.lower() in ['.txt', '.md']:
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    preview = content[:500] + "..." if len(content) > 500 else content
                    print(f"\n📝 内容预览:")
                    print("-" * 40)
                    print(preview)
            except Exception as e:
                print(f"❌ 无法读取文件内容: {e}")

        return True

    print(f"❌ 未找到ID为 {doc_id} 的文档")
    return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 显示特定文档详情
        doc_id = sys.argv[1]
        show_document_details(doc_id)
    else:
        # 显示所有文档列表
        list_documents()

        # 提示用户可以查看详情
        print("💡 提示：使用 'python3 list_documents.py <document_id>' 查看文档详情")