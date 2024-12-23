from ._anvil_designer import RenameEquipmentsTemplate
from anvil import *
import anvil.server
import anvil


class RenameEquipments(RenameEquipmentsTemplate):
  def __init__(self, **properties):
      self.init_components(**properties)
      self.uploaded_file = None  # 用于存储上传的文件
      self.equipment_names = []  # 用于存储提取的装备名称

  def file_loader_change(self, file, **event_args):
      # 文件上传时触发
      self.uploaded_file = file
      alert("文件已上传！")

  def extract_names_button_click(self, **event_args):
      # 提取装备名称
      if self.uploaded_file:
          self.equipment_names = anvil.server.call("extract_names", self.uploaded_file)
          self.repeating_panel_1.items = [{"old_name": name, "new_name": ""} for name in self.equipment_names]
      else:
          alert("请先上传文件！")

  def generate_names_button_click(self, **event_args):     
      # 为装备重新生成名字
      if self.equipment_names:          
          try:         
              # 调用服务端函数
              result = anvil.server.call("generate_names_with_dify", self.equipment_names)

              print("result:", result)
              if not result["success"]:
                  # 如果失败，弹出提示框
                  anvil.alert("重命名失败, 请重试。", title="失败", large=True)
              else:
                  # 如果成功，获取新名字
                  new_names = result["new_names"]
                  for item, new_name in zip(self.repeating_panel_1.items, new_names):
                      item["new_name"] = new_name
                  self.repeating_panel_1.items = self.repeating_panel_1.items  # 刷新显示
          except Exception as e:
              anvil.alert(f"重命名发生错误, 请重试: {str(e)}", title="错误", large=True)
      else:
          alert("请先提取装备名称！")

  def save_updated_file_button_click(self, **event_args):
      # 保存新的装备表
      if self.repeating_panel_1.items:
          updated_file = anvil.server.call("save_updated_file", self.repeating_panel_1.items, self.uploaded_file)
          download(updated_file)
      else:
          alert("没有可保存的数据！")

  def save_mapping_file_button_click(self, **event_args):
      # 保存新旧名字对应关系
      if self.repeating_panel_1.items:
          mapping_file = anvil.server.call("save_mapping_file", self.repeating_panel_1.items)
          download(mapping_file)
      else:
          alert("没有可保存的映射数据！")

  def link_1_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('Home')

