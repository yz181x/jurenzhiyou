import yaml
import os
import shutil
from datetime import datetime

def backup_directory(src_dir):
    """创建源目录的备份"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"{src_dir}_backup_{timestamp}"
    shutil.copytree(src_dir, backup_dir)
    print(f"Created backup at: {backup_dir}")
    return backup_dir

def convert_yaml_files(directory):
    """转换目录下所有的YAML文件为多行格式"""
    converted_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                file_path = os.path.join(root, file)
                try:
                    # 读取YAML文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        data = yaml.safe_load(content)
                    
                    # 重新写入，使用多行格式
                    with open(file_path, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, 
                                allow_unicode=True,      # 允许Unicode字符
                                default_flow_style=False,# 使用多行格式
                                sort_keys=False,         # 保持键的顺序
                                indent=2,               # 设置缩进
                                width=float("inf"))      # 防止长行折行
                    
                    print(f"✓ Converted: {file_path}")
                    converted_count += 1
                    
                except Exception as e:
                    print(f"✗ Error processing {file_path}: {e}")
                    error_count += 1
    
    return converted_count, error_count

def main():
    # 获取当前目录
    current_dir = os.getcwd()
    
    # 创建备份
    print("Creating backup...")
    backup_dir = backup_directory(current_dir)
    
    # 转换文件
    print("\nConverting YAML files...")
    converted, errors = convert_yaml_files(current_dir)
    
    # 打印统计信息
    print("\nConversion completed!")
    print(f"Successfully converted: {converted} files")
    print(f"Errors encountered: {errors} files")
    print(f"Backup location: {backup_dir}")

if __name__ == "__main__":
    main()