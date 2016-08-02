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

        # clear all txtboxes from any input
        self.dlg.txtbox_input_meas.clear()
        self.dlg.txtbox_input_codes.clear()
        self.dlg.txtbox_code_preview.clear()

        self.dlg.txtbox_code_preview.setReadOnly(True)

        # set size of txtbox
        txtbox_code_preview_font = QFont()
        txtbox_code_preview_font.setPointSize(10)
        self.dlg.txtbox_code_preview.setFont(txtbox_code_preview_font)

        # connect buttons with theire actions if clicked
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
        #DELIMITER FOR THE SINGLE FIELDS OF THE MEASUREMENT FILE
        field_del = self.del_char

        #CODE POSITION: INDEX OF THE CODE FILE FOR EACH LINES
        code_pos = self.code_pos
        e_pos = self.e_pos
        n_pos = self.n_pos
        h_pos = self.h_pos

        #GET EPSG CODE
        epsg = self.epsg

        #store file path to measruement file and show text in txtbox
        meas_file_path = QFileDialog.getOpenFileName(self.dlg, "Select inpute file ","", '*.txt')
        self.dlg.txtbox_input_meas.setText(meas_file_path)

        #add all lines as list and strip line ending characters and split already
        all_lines = [line.rstrip('\n').rstrip("\r").split(field_del) for line in open(meas_file_path)]

        # ======================================================================
        # LOOP THROUGH ALLE LINES OF MEASUREMENT FILE AND ADD COORDINATES TO
        # DICITIONARY "COORDS"
        # ======================================================================
        for line in all_lines:
            #REDUCE NUMBER OF LINES CHECKED AS THEY SHOULD HAVE EXACLTY 4 ELEMENTS
            #THEREFORE ALL THE OVERHEAD (LOG) IS SKIPPED
            if len(line) == 4:

                #LOOP THROUGH ALL CODES AND CHECK WHICH CODE FITS THIS SPECIFIC LINE
                for codes in self.all_codes:
                    if codes["regex"].match(line[0]):
                        codes["coords"].append([line[code_pos], QgsPoint(float(line[e_pos]),float(line[n_pos])), line[h_pos]])

        for codes in self.all_codes:
            if codes["geometry"] == "POINT":
                # create layer
                if len(codes["coords"]) != 0:
                    vl = QgsVectorLayer("Point?crs=EPSG:%s" % epsg, codes["name"], "memory")
                    pr = vl.dataProvider()

                    vl.startEditing()
                    pr.addAttributes([QgsField("name", QVariant.String),QgsField("code", QVariant.String), QgsField("height", QVariant.Double)])

                    for coords in codes["coords"]:
                        fet = QgsFeature()
                        fet.setGeometry(QgsGeometry.fromPoint(coords[1]))
                        fet.setAttributes([codes["name"], coords[0], coords[2]])
                        pr.addFeatures([fet])

                    # commit to stop editing the layer
                    vl.commitChanges()

                    # update layer's extent when new features have been added
                    # because change of extent in provider is not propagated to the layer
                    vl.updateExtents()
                    # add layer to the legend
                    QgsMapLayerRegistry.instance().addMapLayer(vl)
            elif codes["geometry"] == "POLYGON":
                # create layer
                if len(codes["coords"]) != 0:
                    pass

        # ======================================================================
        # LOOP THROUGH ALL COORDINATES AND PROCESS GEOMETRY
        # ======================================================================

    def select_codes_file(self):
        self.all_codes = []

        codes_file_path = QFileDialog.getOpenFileName(self.dlg, "Select inpute file ","", '*.txt *.csv')
        self.dlg.txtbox_input_codes.setText(codes_file_path)

        # ======================================================================
        # START PARSING THE CODES file
        # ======================================================================
        with open(codes_file_path, 'rb') as codes_file:
            for i, line in enumerate(codes_file):

                #create empty dicitionary that will be filled for each line
                dict_code = dict.fromkeys(["name", "regex", "geometry", "groupby", "export", "coords"])
                dict_code["coords"] = []
                #check if line is commented; if not continue:
                if line[0] == '#':
                    if i == 2:
                        QMessageBox.information(None, "ERROR:", "NO EPSG CODE FOUND IN LINE %i..." % i)
                        return None
                    else:
                        pass
                else:
                    line_regex = []

                    # ==========================================================
                    # FIRST LINE CONTAINS SEPARATOR USED IN MEASUREMENT FILE
                    # ==========================================================
                    if i == 0:
                        line = line.replace("\n","").replace("\r","")
                        del_char = line.split("#")[0].strip()

                        if del_char == "SPACE":
                            del_char = " "
                            self.del_char = del_char
                        else:
                            self.del_char = del_char

                        # ======================================================
                        # SHOW WARNING DIALOG IF LENGTH OF SEPARATOR != 1
                        # ======================================================
                        if len(del_char) != 1:
                            QMessageBox.information(None, "ERROR:", "NOT A VALID SEPARATOR CHARACTER...")
                            return None

                    # ==========================================================
                    # SECOND LINE CONTAINS ORDER OF ATTRIBUTES IN MEASUREMENT FILE
                    # ==========================================================
                    if i == 1:
                        line = line.replace("\n","").replace("\r","")
                        field_order_str = line.split("#")[0]
                        field_order =line.split("#")[0].split(del_char)

                        #GET POSITION OF CODE IN MEASUREMENT FILE
                        code_pos = field_order.index("CODE")
                        self.code_pos = code_pos

                        # GET ORDER OF COORDINATES; CAN BE EITHER ENH OR XYZ
                        if "E" in line:
                            if "N" in line:
                                if "H" in line:
                                    e_pos = field_order.index("E")
                                    n_pos = field_order.index("N")
                                    h_pos = field_order.index("H")

                        if "X" in line:
                            if "Y" in line:
                                if "Z" in line:
                                    e_pos = field_order.index("X")
                                    n_pos = field_order.index("Y")
                                    h_pos = field_order.index("Z")

                        self.e_pos = e_pos
                        self.n_pos = n_pos
                        self.h_pos = h_pos

                    #GET EPSG CODE
                    if i == 2:
                        if "EPSG" in line:
                            epsg_code = line.split("#")[0].strip().split(":")[1]
                            self.epsg = epsg_code
                        else:
                            QMessageBox.information(None, "ERROR:", "NO EPSG CODE FOUND IN LINE %i..." % i)
                            return None


                    # ==========================================================
                    # ALL OTHER LINES CONTAIN CODE
                    # ==========================================================
                    if i > 2:
                        #remove line feed character; \n unix; \r mac; \n\r windows
                        line = line.replace("\n","").replace("\r","")

                        #ignore everything after comment tag and remove trailing spaces
                        line = line.split("#")[0].strip()

                        #if there is nothin in front of the # else continue
                        if line == "":
                            pass

                        else:
                            #get geometry type of code
                            if "MULTI" in line:
                                print "No MULTI geometries are supported (yet)...change geometry in line %i" % (i)
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

                            #codes are separated by ,
                            line = line.split(",")

                            #last attribute must be a name
                            name = line[-1]
                            dict_code['name'] = name

                            #get position of geometry tag in line
                            geom_index = line.index(geom_type)

                            #if geom == POINT: after geom_index output formats are given
                            #everything before geom_index are parts of the code
                            #extract supported output formats and store them as a list
                            if geom_type == "POINT":
                                out_formats = line[geom_index+1].replace("[","").replace("]","").split("/")
                                dict_code['export'] = out_formats
                                dict_code['groupby'] = None
                            else:
                                group_by = line[geom_index+1]
                                out_formats = line[geom_index+2].replace("[","").replace("]","").split("/")
                                dict_code['export'] = out_formats
                                dict_code['groupby'] = group_by

                            # ==================================================
                            # LOOP THROUGH ALL CODE PARTS AND EXTRACT information
                            # ==================================================
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
                                        digit_regex_str = "[0-9]"
                                        #print digit_regex.match('0').groups()

                                    elif nr_digits == '2':
                                        #match all numbers from 00 to 99
                                        digit_regex = re.compile("[0-9][0-9]")
                                        digit_regex_str = "[00-99]"
                                        #print digit_regex.match('00').groups()

                                    elif nr_digits == '3':
                                        #match all numbers from 000 to 999
                                        digit_regex = re.compile("[0-9][0-9][0-9]")
                                        digit_regex_str = "[000-999]"
                                        #print digit_regex.match('000').groups()

                                    elif nr_digits == '4':
                                        #match all numbers from 0000 to 9999
                                        digit_regex = re.compile("[0-9][0-9][0-9][0-9]")
                                        digit_regex_str = "[0000-9999]"
                                        #print digit_regex.match('0000').groups()

                                    elif nr_digits == '5':
                                        #match all numbers from 0000 to 9999
                                        digit_regex = re.compile("[0-9][0-9][0-9][0-9][0-9]")
                                        digit_regex_str = "[00000-99999]"
                                        #print digit_regex.match('0000').groups()
                                # ======================================================

                                # ======================================================
                                # GET SEPARATERS; THEY ARE INDICATED BY USING ""
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

                            # ==================================================
                            # COMBINE ALL PARTS OF THE CODE
                            # ==================================================

                            line_regex_str = ""
                            for parts in line_regex:
                                if parts != "":
                                    if parts != line_regex[-1]:
                                        line_regex_str += parts #+ "|"
                                    else:
                                        line_regex_str += parts

                            final_regex = "(" + line_regex_str + ")"

                            #save regex as compiled object in dictionary
                            dict_code['regex'] = re.compile(final_regex)

                        # ADD DICT CONTAINING CODE SCHEMA FOR THE LINE TO LIST
                        self.all_codes.append(dict_code)

        # ======================================================================
        # WRITING TO txtbox_code_preview
        # ======================================================================
        #if delimieter is " " for nicer printing print SPACE to preview box
        if del_char == " ":
            del_char_prev = "SPACE"
        else:
            del_char_prev = del_char

        self.dlg.txtbox_code_preview.insertHtml("<b>DELIMITER: </b>%s<br>" % (del_char_prev))
        self.dlg.txtbox_code_preview.insertHtml("<b>FIELD ORDER IN MEASUREMENT FILE: </b>%s<br>" % (field_order_str))
        self.dlg.txtbox_code_preview.insertHtml("<b>COORDINATE SYSTEM: </b>EPSG:%s<br>" % (epsg_code))
        self.dlg.txtbox_code_preview.insertHtml("<br>")
        self.dlg.txtbox_code_preview.insertHtml("<b>NUMBER OF CODES: %i</b><br>" % len(self.all_codes))

        #["name", "regex", "geometry", "groupby", "export", "coordinates"]
        for codes in self.all_codes:
            name = codes["name"]
            geom = codes["geometry"]
            out = codes["export"]
            self.dlg.txtbox_code_preview.insertHtml("%s %s %s<br>" % (name, geom, out))

        # ======================================================================
        # SELECT CODES FILE FINISH
        # ======================================================================
