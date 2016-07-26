# -*- coding: latin1 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

class HarrisMatrix():
    def __init__(self, iface, toolBar):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.act_harris= QAction(QIcon(":/plugins/ArcheoTool/icons/harris_matrix.png"), QCoreApplication.translate("ArcheoTool", "Harris Matrix Composer"), self.iface.mainWindow())
        self.act_harris.setCheckable(True)

        toolBar.addAction(self.act_harris)

        self.act_harris.triggered.connect(self.onClick_Icon)


    def onClick_Icon(self):
        if self.act_harris.isChecked():
            print "create"
        else:
            print "stopped"
