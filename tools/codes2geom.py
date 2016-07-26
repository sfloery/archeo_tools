# -*- coding: latin1 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

#from archeo_tools import ArcheoToolsDialog
from ..gui.readcodes_dialog import ReadCodesToolDialog

class Codes2Geom():
    def __init__(self, iface, toolBar):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.act_codes= QAction(QIcon(":/plugins/ArcheoTool/icons/codes2geom.png"), QCoreApplication.translate("ArcheoTool", "Read Codes"), self.iface.mainWindow())
        self.act_codes.setCheckable(True)

        toolBar.addAction(self.act_codes)

        self.act_codes.triggered.connect(self.onClick_Icon)

        # Create the dialog (after translation) and keep reference
        self.dlg = ReadCodesToolDialog()
        self.dlg.txtbox_input_file.clear()
        self.dlg.button_load_file.clicked.connect(self.select_input_file)

    def onClick_Icon(self):
        if self.act_codes.isChecked():
            #show the dialog
            self.dlg.show()

            print "create"
        else:
            print "stopped"

    def select_input_file(self):

        selected_file = QFileDialog.getOpenFileName(self.dlg, "Select inpute file ","", '*.txt')
        self.dlg.txtbox_input_file.setText(selected_file)

        input_file = open(selected_file, 'rb')

        nr_lines = len(input_file.readlines())

        self.dlg.table_preview.setRowCount(nr_lines)
        self.dlg.table_preview.setColumnCount(5)

        self.dlg.table_preview.setItem(0,1, QTableWidgetItem("Hello"))

        self.dlg.txtbox_input_file.clear()
