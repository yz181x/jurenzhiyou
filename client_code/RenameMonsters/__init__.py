from ._anvil_designer import RenameMonstersTemplate
from anvil import *
import anvil.server

class RenameMonsters(RenameMonstersTemplate):
  def __init__(self, **properties):
      self.init_components(**properties)
      self.name_mapping_file = None  # 用于存储新旧名称对应关系表
      self.monster_files = []       # 用于存储需要修改的怪物文件

  def name_mapping_loader_change(self, file, **event_args):
      # 上传新旧名称对应关系表
      self.name_mapping_file = file
      alert("新旧名称对应关系表已上传！")

  def monster_files_loader_change(self, files, **event_args):
      # 上传怪物文件（多选）      
      if (len(files) > 1000):
        self.monster_files = []
        alert("一次改名文件不要超过1000个，请重新选择。")
        open_form('RenameMonsters')
      else:
        self.monster_files = files
        alert(f"已上传 {len(files)} 个怪物文件！")

  def rename_monster_equipment_button_click(self, **event_args):
      # 修改怪物爆出的装备名称
      if not self.name_mapping_file:
          alert("请先上传新旧名称对应关系表！")
          return
      if not self.monster_files:
          alert("请上传至少一个怪物文件！")
          return

      # 调用服务器端函数
      # zip_file = anvil.server.call("rename_monster_equipment", self.name_mapping_file, self.monster_files)
      self.zip_monster_file = self.process_monster_files_in_batches()
      alert("所有怪物文件已完成改名！")

  def process_monster_files_in_batches(self):
    batch_size = 100
    all_zip_files = []
    
    # 分批处理 monster_files
    for i in range(0, len(self.monster_files), batch_size):
        # print(f"rename from {i+1} to {i+1 + batch_size}")
        batch = self.monster_files[i:i + batch_size]
        zip_file = anvil.server.call("rename_monster_equipment", self.name_mapping_file, batch)
        all_zip_files.append(zip_file)
    
    # 合并 ZIP 文件在服务端完成
    final_zip = anvil.server.call("merge_zip_files", all_zip_files, "monsters")
    return final_zip
  
  def link_1_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('Home')

  def download_monters_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    download(self.zip_monster_file)

  def db_files_loader_change(self, files, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    # 上传数据库文件（多选）      
    if (len(files) > 1000):
      self.db_files = []
      alert("一次改名文件不要超过1000个，请重新选择。")
      open_form('RenameMonsters')
    else:
      self.db_files = files
      alert(f"已上传 {len(files)} 个数据库文件！")

  def download_db_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    download(self.zip_db_file)

  def rename_db_equipment_button_click(self, **event_args):
      # 修改怪物爆出的装备名称
      if not self.name_mapping_file:
          alert("请先上传新旧名称对应关系表！")
          return
      if not self.db_files:
          alert("请上传至少一个数据库文件！")
          return

      # 调用服务器端函数
      # zip_file = anvil.server.call("rename_monster_equipment", self.name_mapping_file, self.monster_files)
      self.zip_db_file = self.process_db_files_in_batches()
      alert("所有数据库文件已完成改名！")

  def process_db_files_in_batches(self):
    batch_size = 100
    all_zip_files = []
    
    # 分批处理 monster_files
    for i in range(0, len(self.db_files), batch_size):
        # print(f"rename from {i+1} to {i+1 + batch_size}")
        batch = self.db_files[i:i + batch_size]
        zip_file = anvil.server.call("rename_db_equipment", self.name_mapping_file, batch)
        all_zip_files.append(zip_file)
    
    # 合并 ZIP 文件在服务端完成
    final_zip = anvil.server.call("merge_zip_files", all_zip_files, "dbs")
    return final_zip