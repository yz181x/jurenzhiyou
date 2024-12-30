from ._anvil_designer import HomeTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server


class Home(HomeTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # 验证用户是否登录
    user = anvil.users.get_user()
    if not user:
        # 如果用户未登录，则弹出登录框
        anvil.users.login_with_form()      
    # Any code you write here will run before the form opens.

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('RenameEquipments')

  def button_2_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('RenameMonsters')
