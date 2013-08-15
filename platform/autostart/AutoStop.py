from OpenWizzy.core.config import ConfigManagementItem, ItemSingleClass,ItemGroupClass
from OpenWizzy import o

class AutoStopItem(ConfigManagementItem):
    CONFIGTYPE = "autostop"
    DESCRIPTION = "Auto-stop"
    SORT_PARAM = 'order'
    SORT_METHOD = ConfigManagementItem.SortMethod.INT_DESCENDING

    def ask(self):
        self.dialogMessage("Configure autostop. Please note that stop-order is sorted descending. Applications with the highest order will be stopped first.")
        self.dialogAskString("command", "Enter stop command")
        self.dialogAskInteger("order", "Enter the stop-order for this application.")

    def show(self):
        params = dict(itemname=self.itemname, **self.params)
        o.gui.dialog.message("%(order)d (%(itemname)s) - %(command)s" % params)

AutoStop = ItemGroupClass(AutoStopItem)