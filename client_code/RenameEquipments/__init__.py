from ._anvil_designer import RenameEquipmentsTemplate
from anvil import *
import anvil.server
import anvil


class RenameEquipments(RenameEquipmentsTemplate):
  def __init__(self, **properties):
      self.init_components(**properties)
      self.uploaded_files = None  # 用于存储上传的文件
      self.equipment_names = []  # 用于存储提取的装备名称

  def file_loader_change(self, files, **event_args):
      # 文件上传时触发
      self.uploaded_files = files
      alert("文件已上传！")

  def extract_names_button_click(self, **event_args):
      # 提取装备名称
      if self.uploaded_files:  # 修改为处理多个文件
          all_names = set()  # 使用集合去重
          for uploaded_file in self.uploaded_files:  # 遍历所有上传的文件
              extracted_names = anvil.server.call("extract_names_with_filter", uploaded_file)
              all_names.update(extracted_names)  # 将提取的名称加入集合，去重
          
          self.equipment_names = list(all_names)  # 转换为列表          
          self.repeating_panel_1.items = [{"old_name": name, "new_name": ""} for name in self.equipment_names]
          if len(self.equipment_names) > 0:
            alert(f'一共{len(self.equipment_names)}个名称', title="", large=True)
          # print(f"一共{len(self.equipment_names)}个名称")
      else:
          alert("请先上传文件！")

  def generate_names_button_click(self, **event_args):     
    # 为装备重新生成名字
    if self.equipment_names:          
        try:
            all_new_names = []  # 存储所有新名字
            
            # 将名字分批，每批100个
            batch_size = 100
            batches = [self.equipment_names[i:i + batch_size] for i in range(0, len(self.equipment_names), batch_size)]
            
            for batch in batches:
                # 调用服务端函数
                result = anvil.server.call("generate_names_with_dify", batch)
                print("batch result:", result)
                
                if not result["success"]:
                    # 如果任意批次失败，弹出提示框并终止
                    anvil.alert("重命名失败, 请重试。", title="失败", large=True)
                    return
                
                # 添加当前批次的新名字到总列表
                all_new_names.extend(result["new_names"])
            
            # 更新RepeatingPanel显示
            for item, new_name in zip(self.repeating_panel_1.items, all_new_names):
                item["new_name"] = new_name
            self.repeating_panel_1.items = self.repeating_panel_1.items  # 刷新显示
            
        except Exception as e:
            # 捕获并提示错误
            anvil.alert(f"重命名发生错误, 请重试: {str(e)}", title="错误", large=True)
    else:
        anvil.alert("请先提取装备名称！", title="提示", large=True)

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

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('RenameMonsters')

