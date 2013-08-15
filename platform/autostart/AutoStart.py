from OpenWizzy.core.config import ConfigManagementItem, ItemSingleClass,ItemGroupClass
from OpenWizzy import o

class AutoStartItem(ConfigManagementItem):
    CONFIGTYPE = "autostart"
    DESCRIPTION = "Auto-start"
    SORT_PARAM = 'order'
    SORT_METHOD = ConfigManagementItem.SortMethod.INT_ASCENDING


    def ask(self):
        self.dialogMessage("Configure autostart. Please note that start-order is sorted ascending. Applications with the lowest order will be started first.")
        self.dialogAskString("command", "Enter start command")
        self.dialogAskInteger("order", "Enter the start-order for this application")

    def show(self):
        params = dict(itemname=self.itemname, **self.params)
        o.gui.dialog.message("%(order)d (%(itemname)s) - %(command)s" % params)

AutoStart = ItemGroupClass(AutoStartItem)