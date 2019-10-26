from PyQt5 import QtCore
import time
import keyboard

#Thread responsible for creating new hotkeys and 'listing' for keypresses
class keyboardShortcuts(QtCore.QThread):
    new_key_press = QtCore.pyqtSignal()

    def __init__(self, keybindQueue, keyPressQueue):
        self.keyBindQueue = keybindQueue
        self.keyPressQueue = keyPressQueue
        self.binds = {}
        QtCore.QThread.__init__(self)

    def volumeUp(self,app,direction):
        volumeChangeDict = {}
        volumeChangeDict[app] = direction
        self.keyPressQueue.put(volumeChangeDict)
        self.new_key_press.emit()


    def run(self):
        while(True):
            if (self.keyBindQueue.qsize() != 0):
                #update binds
                newBinds = self.keyBindQueue.get()
                for bind in newBinds:
                    if bind in self.binds:
                        keyboard.remove_hotkey(self.binds[bind]['hotkeyUP'])
                        keyboard.remove_hotkey(self.binds[bind]['hotkeyDOWN'])
                    strUp = 'shift+page up+'+newBinds[bind]
                    strDown = 'shift+page down+' + newBinds[bind]
                    self.binds[bind] = {}
                    self.binds[bind]['value'] = newBinds[bind]
                    self.binds[bind]['hotkeyUP'] = keyboard.add_hotkey(strUp,self.volumeUp,args=[bind, 'up'], suppress = True)
                    self.binds[bind]['hotkeyDOWN'] = keyboard.add_hotkey(strDown, self.volumeUp, args=[bind, 'down'], suppress = True)

            time.sleep(1)