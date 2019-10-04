from PyQt5 import QtCore, QtGui, QtWidgets
import queue
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from Worker import Worker
from keyboardShortcuts import keyboardShortcuts
import sys
import threading
import time
import copy

class Ui_MainWindow(object):
    def __init__(self):
        self.tableQueue = queue.Queue()
        self.keyBindQueue = queue.Queue()
        self.keyPressQueue = queue.Queue()
        self.apps = None

        QtCore.QThread.currentThread().setObjectName("MAIN")
        self.thread = QtCore.QThread()
        self.thread.name = "auto_refresh"
        self.worker = Worker(self.tableQueue)
        self.worker.moveToThread(self.thread)
        self.worker.update_table.connect(self.updateTable)



        self.threadTwo = QtCore.QThread()
        self.thread.name = "auto_refresh"
        self.keyboardShortcuts = keyboardShortcuts(self.keyBindQueue, self.keyPressQueue)
        self.keyboardShortcuts.moveToThread(self.thread)
        self.keyboardShortcuts.new_key_press.connect(self.ChangeVolume)
        self.session = []
        self.appKeyMap = {}
        self.worker.start()
        self.keyboardShortcuts.start()

    #TODO: this shouldn't really be in the GUI thread
    def ChangeVolume(self):
        pressedDict = self.keyPressQueue.get()

        modifier = (self.volume_spin.value() / 100)
        for bin in pressedDict:
            process = bin
            direction = pressedDict[bin]

            for session in self.session:
                if session.Process:
                    if session.Process.name() == process:
                        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                        currentVolume = volume.GetMasterVolume()
                        if direction == 'up':
                            newVolume = currentVolume + modifier
                            if newVolume > 1.0:
                                newVolume = 1.0
                        else:
                            newVolume = currentVolume - modifier
                            if newVolume < 0.0:
                                newVolume = 0.0

                        volume.SetMasterVolume(newVolume, None)

    #Gets called by the worker thread telling us that we have changes to the app table
    def updateTable(self):
        self.session = self.tableQueue.get()
        resyncKeys = False

        #get the curret list of processes
        tableHeight = self.tableWidget.rowCount()
        currentApps = []
        if(tableHeight != 0):
            for i in range(tableHeight):
                currentApps.append(self.tableWidget.item(i,0).text())

        AppsOpen = []
        currentTablePos = 0
        for session in self.session:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            level = volume.GetMasterVolume()
            if session.Process:
                if session.Process.name() not in AppsOpen:
                    if session.Process.name() not in currentApps:
                        #add it
                        resyncKeys = True
                        self.tableWidget.insertRow(tableHeight)
                        self.tableWidget.setItem(tableHeight, 0, QtWidgets.QTableWidgetItem(session.Process.name()))
                        self.tableWidget.setItem(tableHeight, 1, QtWidgets.QTableWidgetItem(str(int(level * 100))))
                        self.tableWidget.setItem(tableHeight, 2, QtWidgets.QTableWidgetItem(str(tableHeight)))
                        currentApps.append(session.Process.name())
                        self.appKeyMap[session.Process.name()] = str(tableHeight)
                        tableHeight += 1
                    else:
                        self.tableWidget.setItem(currentTablePos, 1, QtWidgets.QTableWidgetItem(str(int(level * 100))))
                        currentTablePos+=1
                    AppsOpen.append(session.Process.name())

        differences = list(set(currentApps) - set(AppsOpen))
        if len(differences) != 0:
            for value in reversed(differences):
                indexVal = currentApps.index(value)
                self.tableWidget.removeRow(indexVal)
                del self.appKeyMap[value]
                resyncKeys = True

        if(resyncKeys):
            self.keyBindQueue.put(self.appKeyMap)

    #user has pressed the updateBins button, notify the key handler to update it's binds
    def updateBinds(self):
        keysToUpdate = {}

        for key in self.appKeyMap:
            #find row with that key in app col
            for itr in range ((self.tableWidget.rowCount())):
                if self.tableWidget.item(itr,0).text() == key:
                    break
            if self.appKeyMap[key] != self.tableWidget.item(itr,2).text():
                keysToUpdate[key] = self.tableWidget.item(itr,2).text()
                self.appKeyMap[key] = self.tableWidget.item(itr,2).text()

        if keysToUpdate:
            #we have new keys so update
            self.keyBindQueue.put(keysToUpdate)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(422, 739)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.tableWidget = QtWidgets.QTableWidget(self.frame)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.volume_spin = QtWidgets.QSpinBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.volume_spin.sizePolicy().hasHeightForWidth())
        self.volume_spin.setSizePolicy(sizePolicy)
        self.volume_spin.setObjectName("volume_spin")
        self.volume_spin.setValue(10)
        self.horizontalLayout_2.addWidget(self.volume_spin)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.updateBindsBtn = QtWidgets.QPushButton(self.frame_2)
        self.updateBindsBtn.setObjectName("updateBindsBtn")
        self.horizontalLayout_3.addWidget(self.updateBindsBtn)
        self.verticalLayout.addWidget(self.frame_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 422, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "APP"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Current Vol"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Key bind"))
        self.label.setText(_translate("MainWindow", "Volume Step"))
        self.updateBindsBtn.setText(_translate("MainWindow", "Update Binds"))
        self.updateBindsBtn.clicked.connect(self.updateBinds)
