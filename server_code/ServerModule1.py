import anvil.media
import pandas as pd
import zipfile
import random
import string
from io import BytesIO

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
def generate_names(old_names):
    # 生成新的名字，保持风格一致
    return ["EQ_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in old_names]

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
            # 修改怪物文件中的装备名称
            try:
                monster_data = monster_file.get_bytes().decode("utf-8")
            except UnicodeDecodeError:
                monster_data = monster_file.get_bytes().decode("gbk")

            for old_name, new_name in mapping.items():
                monster_data = monster_data.replace(old_name, new_name)

            # 将修改后的内容写入 ZIP 文件
            renamed_file_name = f"Renamed_{monster_file.name}"
            zip_file.writestr(renamed_file_name, monster_data)

    # 创建一个 ZIP 文件供下载
    zip_buffer.seek(0)
    zip_media = anvil.BlobMedia("application/zip", zip_buffer.read(), name="Renamed_Files.zip")
    return zip_media