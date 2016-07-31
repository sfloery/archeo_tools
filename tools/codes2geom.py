# -*- coding: latin1 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

#from archeo_tools import ArcheoToolsDialog
from ..gui.readcodes_dialog import ReadCodesToolDialog
import re
import random
import string

def random_string(size):
    char_set = string.ascii_uppercase + string.ascii_lowercase

    return ''.join(random.choice(char_set) for _ in range(size))


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

        self.dlg.txtbox_input_meas.clear()
        self.dlg.txtbox_input_codes.clear()

        self.dlg.button_load_meas.clicked.connect(self.select_meas_file)
        self.dlg.button_load_codes.clicked.connect(self.select_codes_file)

    def onClick_Icon(self):
        if self.act_codes.isChecked():
            #show the dialog
            self.dlg.show()
            #print "create"
        else:
            pass
            #print "stopped"

    def select_meas_file(self):

        codes_regex = []

        meas_file_path = QFileDialog.getOpenFileName(self.dlg, "Select inpute file ","", '*.txt')
        self.dlg.txtbox_input_meas.setText(meas_file_path)

        all_lines = [line.rstrip('\n').rstrip("\r").split(" ") for line in open(meas_file_path)]

        coords_lines = []

        for lines in all_lines:
            if len(lines) == 4:
                coords_lines.append(lines)

        for coords in coords_lines:
            for regex in self.all_codes:
                if re.compile(regex).match(coords[0]):
                    print coords

        # with open(meas_file_path, 'rb') as meas_file:
        #     for i,line in enumerate(meas_file):
        #
        #         #remove line feed character; \n unix; \r mac; \n\r windows
        #         line = line.replace("\n","").replace("\r","")
        #
        #         line_parts = line.split(" ")
        #         if len(line_parts) == 4:
        #
        #             code = line_parts[0].strip()
        #
        #             for regex in codes_regex:
        #                 if regex.match(code):
        #                     print line


    def select_codes_file(self):
        self.all_codes = []

        dict_code = dict.fromkeys(["name", "regex", "geometry", "groupby", "export"])

        codes_file_path = QFileDialog.getOpenFileName(self.dlg, "Select inpute file ","", '*.txt')
        self.dlg.txtbox_input_codes.setText(codes_file_path)

        with open(codes_file_path, 'rb') as codes_file:
            for i, line in enumerate(codes_file):

                #check if line is commented; if not continue:
                if line[0] == '#':
                    pass
                else:

                    line_regex = []

                    #first line contains delimiter for coords
                    if i == 0:
                        line = line.replace("\n","").replace("\r","")
                        del_char = line.split("#")[0].strip()

                        if len(del_char) != 1:
                            #print "Only one character is allowed..."
                            QMessageBox.information(None, "ERROR:", "Only one character allowed as delimiter...")
                            return None

                    #second line contains order of coordinates
                    if i == 1:
                        line = line.replace("\n","").replace("\r","")
                        field_order =line.split("#")[0].split(del_char)

                    #all the other lines contain codes
                    if i > 1:
                        #remove line feed character; \n unix; \r mac; \n\r windows
                        line = line.replace("\n","").replace("\r","")

                        #ignore everything after comment tag and remove trailing spaces
                        line = line.split("#")[0].strip()

                        #if there is nothin in front of the # else continue
                        if line == "":
                            print "Empty line..."
                        else:
                            #get geometry type of code
                            if "MULTI" in line:
                                print "No MULTI geometries are supported (yet)...change geometry in line %i" % (i)
                                #QMessageBox.information(None, "ERROR:", "No MULTI geometries are supported...")
                                pass
                            else:
                                if "POINT" in line:
                                    geom_type = "POINT"
                                    dict_code['geometry'] = "POINT"
                                elif "POLYLINE" in line:
                                    geom_type = "POLYLINE"
                                    dict_code['geometry'] = "POLYLINE"
                                elif "POLYGON" in line:
                                    geom_type = "POLYGON"
                                    dict_code['geometry'] = "POLYGON"
                                else:
                                    print "No supported geometry found in line %i..." %(i)
                                    #QMessageBox.information(None, "ERROR:", "No supported geometry found...")
                                    pass

                            #split line into its parts:
                            line = line.split(",")

                            #get codes name:
                            name = line[-1]
                            dict_code['name'] = name

                            #get position of geometry tag in line
                            geom_index = line.index(geom_type)

                            #if geom == POINT: after geom_index output formats are given
                            #everything bevery geom_index are parts of the code

                            #extract supported output formats and store them as a list
                            if geom_type == "POINT":
                                out_formats = line[geom_index+1].replace("[","").replace("]","").split("/")
                            else:
                                out_formats = line[geom_index+2].replace("[","").replace("]","").split("/")

                            dict_code['export'] = out_formats

                            # ==========================================================
                            # LOOP THROUGH ALL CODE PARTS AND EXTRACT information
                            # ==========================================================
                            code_parts = line[:geom_index]
                            for i in range(0,len(code_parts)):
                                digit_regex = None
                                char_regex = None
                                sep_regex = None

                                # ======================================================
                                # GET NUMBERS INDICATING NUMBER ranges
                                # 1 --> [0 - 9]
                                # 2 --> [00 - 99]
                                # 3 --> [000 - 999]
                                # 4 --> [0000 - 9999]
                                # ======================================================
                                if code_parts[i].isdigit():

                                    nr_digits = code_parts[i]

                                    if nr_digits == '1':
                                        #match all numbers from 0 to 9
                                        digit_regex = re.compile("[0-9]")
                                        #print digit_regex.match('0').groups()

                                    elif nr_digits == '2':
                                        #match all numbers from 00 to 99
                                        digit_regex = re.compile("[0-9][0-9]")
                                        #print digit_regex.match('00').groups()

                                    elif nr_digits == '3':
                                        #match all numbers from 000 to 999
                                        digit_regex = re.compile("[0-9][0-9][0-9]")
                                        #print digit_regex.match('000').groups()

                                    elif nr_digits == '4':
                                        #match all numbers from 0000 to 9999
                                        digit_regex = re.compile("[0-9][0-9][0-9][0-9]")
                                        #print digit_regex.match('0000').groups()

                                    elif nr_digits == '5':
                                        #match all numbers from 0000 to 9999
                                        digit_regex = re.compile("[0-9][0-9][0-9][0-9][0-9]")
                                        #print digit_regex.match('0000').groups()
                                # ======================================================

                                # ======================================================
                                # GET SEPARATERS
                                # ======================================================
                                elif '"' in code_parts[i]:
                                    raw_code = code_parts[i]
                                    code = raw_code.replace('"',"")

                                    if len(code) == 1:
                                        sep = code
                                        sep_regex = re.compile(sep)
                                    else:
                                        sep = ""
                                        sep_regex = re.compile("")
                                # ======================================================

                                # ======================================================
                                # EXTRACT CODECS
                                # CAN BE ANY COMBINATION of lower and UPPER case
                                # ======================================================
                                elif code_parts[i].isalpha():
                                    char_regex = re.compile(code_parts[i])


                                if char_regex != None:
                                    line_regex.append(char_regex.pattern)
                                elif digit_regex != None:
                                    line_regex.append(digit_regex.pattern)
                                elif sep_regex != None:
                                    line_regex.append(sep_regex.pattern)

                            line_regex_str = ""
                            for parts in line_regex:
                                if parts != "":
                                    if parts != line_regex[-1]:
                                        line_regex_str += parts #+ "|"
                                    else:
                                        line_regex_str += parts

                            final_regex = "(" + line_regex_str + ")"
                            self.all_codes.append(final_regex)

                            #dict_code['regex'] = final_regex

                            #self.all_codes.append(dict_code)
