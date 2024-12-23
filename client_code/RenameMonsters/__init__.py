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
      zip_file = self.process_monster_files_in_batches()
      download(zip_file)
      alert("所有文件已重命名并打包下载！")

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
    final_zip = anvil.server.call("merge_zip_files", all_zip_files)
    return final_zip
  
  def link_1_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('Home')
