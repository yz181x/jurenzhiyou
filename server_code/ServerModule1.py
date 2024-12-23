import anvil.media
import pandas as pd
import zipfile
import random
import string
from io import BytesIO
import requests
import json, re

@anvil.server.callable
def extract_names(uploaded_file):
    # 从Excel中提取名称
    file = BytesIO(uploaded_file.get_bytes())
    df = pd.read_excel(file, header=None)
    for i in range(3):  # 遍历前三行查找“Name”表头
        if "Name" in df.iloc[i].values:
            name_col = df.iloc[i].values.tolist().index("Name")
            return df.iloc[i + 1:, name_col].dropna().tolist()
    raise ValueError("未找到‘Name’表头")

@anvil.server.callable
def extract_names_with_filter(uploaded_file):
    # 从Excel中提取名称
    file = BytesIO(uploaded_file.get_bytes())
    df = pd.read_excel(file, header=None)
    
    for i in range(3):  # 遍历前三行查找“Name”表头
        if "Name" in df.iloc[i].values:
            name_col = df.iloc[i].values.tolist().index("Name")
            names = df.iloc[i + 1:, name_col].dropna().tolist()
            
            # 处理名称过滤逻辑
            filtered_names = []
            for name in names:
                # 转换为字符串，防止意外的非字符串数据
                name = str(name)
                
                # 跳过以 '‘' 开头的名称
                if name.startswith('‘') or '---' in name or '//' in name:
                    continue
                
                # 移除 [] 「」『』中的内容
                name = re.sub(r'\[.*?\]', '', name)
                name = re.sub(r'「.*?」', '', name)
                name = re.sub(r'『.*?』', '', name)
                
                # 移除 Lv1、Lv.2、LvMAX 等内容
                name = re.sub(r'Lv\d+', '', name)
                name = re.sub(r'Lv\.\d+', '', name)
                name = re.sub(r'LvMAX', '', name)
                
                # 移除独立的数字部分（当数字后跟随中文字符时）
                name = re.sub(r'\b\d+\s*(?=\D)', '', name)
                
                # 移除多余的空格
                name = name.strip()
                
                # 如果处理后的名称非空，则添加到过滤后的列表
                if name:
                    filtered_names.append(name)
            
            # 去重并保持顺序
            unique_names = list(dict.fromkeys(filtered_names))
            return unique_names
    
    raise ValueError("未找到‘Name’表头")

@anvil.server.callable
def generate_names(old_names):
    # 生成新的名字，保持风格一致
    return ["EQ_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in old_names]

@anvil.server.callable
def generate_names_with_dify(old_names):
    api_url = 'http://dify-xjp.d5j.tech/v1/chat-messages'
    api_key = 'app-mfM8om4adlkPFZqYopVZori8'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    all_new_names = []
    
    # 将名字分批，每批50个
    batch_size = 50
    batches = [old_names[i:i + batch_size] for i in range(0, len(old_names), batch_size)]
    
    for batch in batches:
        # 将当前批次的名字拼接为字符串
        input_names = ', '.join(batch)
        
        # 构造 POST 请求的 payload
        payload = {
            "query": input_names,
            "inputs": {},
            "response_mode": "blocking",
            "user": "anvil-tools"
        }

        # print("old_name:", payload['query'])
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()            
            if "answer" in result:
                answer = result['answer'].replace('，', ',')
                # print("new_name:", answer)
                batch_new_names = [name.strip() for name in answer.split(',') if name.strip()]
                if len(batch_new_names) >= len(batch):
                    # 如果新名字的个数大于或等于旧名字，取前len(batch)个新名字
                    all_new_names.extend(batch_new_names[:len(batch)])
                elif len(batch_new_names) < len(batch):
                    # 如果新名字的个数小于旧名字，用旧名字补齐
                    all_new_names.extend(batch_new_names + batch[len(batch_new_names):])
            else:
                raise ValueError("API返回的数据无效")
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 如果所有批次成功
    result = {"success": True, "new_names": all_new_names}
    return result

@anvil.server.callable
def save_updated_file(items, uploaded_file):
    # 保存更新后的装备表
    file = BytesIO(uploaded_file.get_bytes())
    df = pd.read_excel(file)
    old_to_new = {item["old_name"]: item["new_name"] for item in items if item["new_name"]}
    for col in df.columns:
        df[col] = df[col].replace(old_to_new)
    output = BytesIO()
    df.to_excel(output, index=False)
    return anvil.BlobMedia("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", output.getvalue(), name="重新起名后的装备表.xls")

@anvil.server.callable
def save_mapping_file(items):
    # 保存新旧名字对应关系为CSV
    mapping_data = "\n".join(f'{item["old_name"]} -> {item["new_name"]}' for item in items if item["new_name"])
    return anvil.BlobMedia("text/csv", mapping_data.encode("utf-8"), name="Name_Mapping.csv")

@anvil.server.callable
def rename_monster_equipment(name_mapping_file, monster_files):
    # 读取新旧名称对应关系文件
    try:
        mapping_data = name_mapping_file.get_bytes().decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"UTF-8 解码失败：{e}")
        # 尝试 GBK 解码
        try:
            mapping_data = name_mapping_file.get_bytes().decode("gbk")
        except UnicodeDecodeError as e2:
            print(f"GBK 解码也失败：{e2}")
            raise ValueError("无法解析文件，请确保文件编码为 UTF-8 或 GBK。")
      
    # 解析新旧名称对应关系
    mapping = {}
    for line in mapping_data.splitlines():
        if "->" in line:
            old_name, new_name = line.split("->")
            mapping[old_name.strip()] = new_name.strip()

    # 创建一个内存中的 ZIP 文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for monster_file in monster_files:
            # 记录文件的编码
            encoding_used = "utf-8"
            try:
                monster_data = monster_file.get_bytes().decode("utf-8")
            except UnicodeDecodeError:
              try:
                monster_data = monster_file.get_bytes().decode("gbk")
                encoding_used = "gbk"
              except UnicodeDecodeError as e:
                print(f"{monster_file.name} decode error: {str(e)}")
                continue
    
            # 修改怪物文件中的装备名称
            # for old_name, new_name in mapping.items():
            #     monster_data = monster_data.replace(old_name, new_name)
          
            # 对 monster_data 的每行进行处理
            lines = monster_data.splitlines()
            updated_lines = []

            for line in lines:
                # 提取名字
                name_match = extract_name(line)
                # print("lind:", line)
                # print("name:", name_match)
            
                # 查找替换对应关系
                if name_match in mapping:
                    new_name = mapping[name_match]
                    line = line.replace(name_match, new_name)
            
                updated_lines.append(line)
            
            # 将更新后的行重新拼接
            monster_data = "\n".join(updated_lines)
    
            # 将修改后的内容写入 ZIP 文件
            renamed_file_name = f"{monster_file.name}"
            zip_file.writestr(renamed_file_name, monster_data.encode(encoding_used))

    # 创建一个 ZIP 文件供下载
    zip_buffer.seek(0)
    zip_media = anvil.BlobMedia("application/zip", zip_buffer.read(), name="Renamed_Files.zip")
    return zip_media

@anvil.server.callable
def merge_zip_files(zip_files):
    # 合并多个 ZIP 文件
    final_zip_buffer = BytesIO()
    with zipfile.ZipFile(final_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as final_zip:
        for zip_file in zip_files:
            with zipfile.ZipFile(BytesIO(zip_file.get_bytes()), 'r') as batch_zip:
                for file_name in batch_zip.namelist():
                    final_zip.writestr(file_name, batch_zip.read(file_name))
    final_zip_buffer.seek(0)
    return anvil.BlobMedia('application/zip', final_zip_buffer.read(), name='final_monsters.zip')
  
# 定义用于提取名字的正则表达式
def extract_name(line):
    # 去掉分数部分，如 "1/100" 或 "1/1"
    line = re.sub(r'\b\d+/\d+\b', '', line)
    # 去掉前置的独立整数，但保留中文字符
    line = re.sub(r'\b\d+\s*(?=\D)', '', line)
    # 去掉方括号、花括号中的内容
    line = re.sub(r'[\[\]\{\}\u300c\u300d\u300e\u300f][^\[\]\{\}\u300c\u300d\u300e\u300f]*[\[\]\{\}\u300c\u300d\u300e\u300f]', '', line)
    # 去掉等级标识，如 "Lv1", "Lv.2", "LvMAX"
    line = re.sub(r'Lv(?:\.?\d+|MAX)', '', line, flags=re.IGNORECASE)
    # 去掉多余的空格和可能残留的无效字符
    line = re.sub(r'^\s*|\s+$', '', line)
    # 去掉多余的连续空格
    line = re.sub(r'\s+', ' ', line)
    return line.strip()