from __future__ import print_function
from GUI import Ui_MainWindow
import windowStyle.styles
import windowStyle.window
from PyQt5 import QtWidgets
import sys


def main():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    windowStyle.styles.dark(app)
    mw = windowStyle.window.ModernWindow(MainWindow)

    mw.show()

    app.exec_()

if __name__ == "__main__":
    main()