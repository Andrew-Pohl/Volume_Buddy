from PyQt5 import QtCore, QtGui, QtWidgets
import queue
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import sys
import threading
import time

#thread looks to see if any new applications have been opened or old one closed
#it signals the GUI class to update it's table if an app is added or removed or a volume has changed
class Worker(QtCore.QThread):
    update_table = QtCore.pyqtSignal()

    def __init__(self, tableQueue, parent=None):
        self.tableQueue = tableQueue
        self.currentSession = []
        sessions = AudioUtilities.GetAllSessions()
        self.volumes = []
        QtCore.QThread.__init__(self)

    def run(self):
        while(True):
            updateList = False
            sessions = AudioUtilities.GetAllSessions()
            if(len(sessions) != len(self.currentSession)):
                self.volumes = []
                for session in sessions:
                    if session.Process:
                        volumeOld = session._ctl.QueryInterface(ISimpleAudioVolume)
                        self.volumes.append(volumeOld.GetMasterVolume())
                updateList = True
            else:
                #loop and check each element
                loopItr = 0
                for session in sessions:
                    if session.Process:
                        volumeOld = session._ctl.QueryInterface(ISimpleAudioVolume)
                        levelOld = volumeOld.GetMasterVolume()
                        if(levelOld != self.volumes[loopItr]):
                            updateList = True
                            self.volumes[loopItr] = levelOld
                        loopItr+=1

            if updateList:
                self.tableQueue.put(sessions)
                self.currentSession = (sessions)
                self.update_table.emit()
            time.sleep(1)