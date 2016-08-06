# -*- coding: latin1 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

#from archeo_tools import ArcheoToolsDialog
from ..gui.readcodes_dialog import ReadCodesToolDialog
from ..gui.readcodes_preview_meas import ReadCodesPreviewMeas

import re
import random
import string
import os

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
        self.prev_window = ReadCodesPreviewMeas()

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
        self.dlg.button_run_conversion.clicked.connect(self.run_conversion)

        self.dlg.button_prev_meas.clicked.connect(self.open_meas_prev)

    def run_conversion(self):
        data = self.all_codes
        epsg = self.epsg

        root = QgsProject.instance().layerTreeRoot()
        node_1 = root.insertGroup(0, self.measfile_name)

        #LOOP THROGUH ALL CODES AND ADD THEM TO SHP/CANVAS
        for codes in data:
            if codes["geometry"] == "POINT":

                print len(codes["coords"])

                # CREATE LAYER AND ADD COORDINATES
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
                    node_layer = node_1.addLayer(vl)

            elif codes["geometry"] == "POLYGON":

                #codes["coords"] contains all codes, coordinates as QPoint and heights
                #for all lines the fit the code previously
                if len(codes["coords"]) != 0:

                    # codes["groups"] contains all group ids that should indicate
                    # separate polygons; for each group we create a new dicitionary
                    # where add the groupid and the coordinates

                    for groups in codes["groups"]:
                        poly = []


                        poly_dict = dict.fromkeys(["name", "coords"])
                        poly_dict["name"] = groups
                        poly_dict["coords"] = []


                        group_start = int(codes["groupid"][0])
                        group_len = int(codes["groupid"][1])
                        group_end = group_start + group_len

                        #now we loop thorugh all coords and check if the code
                        #fits one of the groups; IF YES:
                        for coords in codes["coords"]:
                            if coords[0][group_start:group_end] == groups:

                                #get the id
                                coord_id = coords[0][group_end:]

                                #append the coordinates to the group specific dictionary
                                poly_dict["coords"].append(coords[1])

                        #after all coords that fitch the group are found at the newly
                        #created dictioanry to the codes["polygons"] dictionary
                        codes["polygons"].append(poly_dict)

                    #FOR EVERY CODE CREATE ONE SEPARATE LAYER:
                    vl = QgsVectorLayer("Polygon?crs=EPSG:%s" % epsg, codes["name"], "memory")
                    pr = vl.dataProvider()

                    vl.startEditing()
                    pr.addAttributes([QgsField("name", QVariant.String),QgsField("id", QVariant.String) ])#,QgsField("code", QVariant.String), QgsField("height", QVariant.Double)])

                    #LOOP THROUGH THE POLYGONS
                    for polys in codes["polygons"]:
                        fet = QgsFeature()
                        fet.setGeometry(QgsGeometry.fromPolygon([polys["coords"]]))
                        fet.setAttributes([codes["name"], polys["name"]])#, coords[0], coords[2]])
                        pr.addFeatures([fet])

                    # commit to stop editing the layer
                    vl.commitChanges()

                    # update layer's extent when new features have been added
                    # because change of extent in provider is not propagated to the layer
                    vl.updateExtents()

                    # add layer to the legend
                    QgsMapLayerRegistry.instance().addMapLayer(vl, False)
                    node_layer = node_1.addLayer(vl)

            # ==================================================================




    # ==========================================================================
    # SHOW PREVIEW OF MEASUREMENT FILE IN EXTERNAL WINDOW
    # ==========================================================================
    def open_meas_prev(self):
        all_lines = self.all_lines
        field_del = self.del_char

        #CODE POSITION: INDEX OF THE CODE FILE FOR EACH LINES
        code_pos = self.code_pos
        e_pos = self.e_pos
        n_pos = self.n_pos
        h_pos = self.h_pos

        for line in all_lines:

            #REDUCE NUMBER OF LINES CHECKED AS THEY SHOULD HAVE EXACLTY 4 ELEMENTS
            #THEREFORE ALL THE OVERHEAD (LOG) IS SKIPPED
            if len(line) == 4:

                #LOOP THROUGH ALL CODES AND CHECK WHICH CODE FITS THIS SPECIFIC LINE
                for codes in self.all_codes:
                    if codes["regex"].match(line[0]):

                        #ADD LINES TO PREVIEW
                        if codes["geometry"] == "POINT":
                            #if line contains code and coordinates add GREEN span tag before line and add everything to the txt_meas_preview txt_box
                            self.prev_window.txt_meas_preview.insertHtml('<span style="background-color: #9FF781"; display:inline-block>POINT</span>%s<br>' % ("  " + field_del.join(line)))
                        elif codes["geometry"] == "POLYGON":
                            #if line contains code and coordinates add GREEN span tag before line and add everything to the txt_meas_preview txt_box
                            self.prev_window.txt_meas_preview.insertHtml('<span style="background-color: #9FF781"; display:inline-block>POLY</span>%s<br>' % ("   " + field_del.join(line)))
                        elif codes["geometry"] == "POLYLINE":
                            #if line contains code and coordinates add GREEN span tag before line and add everything to the txt_meas_preview txt_box
                            self.prev_window.txt_meas_preview.insertHtml('<span style="background-color: #9FF781"; display:inline-block>LINE</span>%s<br>' % ("   " + field_del.join(line)))

            else:
                #if not add RED span tag before line and add everything to the txt_meas_preview txt_box
                self.prev_window.txt_meas_preview.insertHtml('<span style="background-color: #FA5858"; display:inline-block>NONE</span>  %s<br>' % (field_del.join(line)))

        #open the window
        self.prev_window.exec_()
    # ==========================================================================


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

        self.measfile_name = os.path.basename(meas_file_path).split(".")[0]

        #add all lines as list and strip line ending characters and split already
        self.all_lines = [line.rstrip('\n').rstrip("\r").split(field_del) for line in open(meas_file_path)]

        # ======================================================================
        # LOOP THROUGH ALLE LINES OF MEASUREMENT FILE AND ADD COORDINATES TO
        # DICITIONARY "COORDS"
        # ======================================================================

        for line in self.all_lines:

            #REDUCE NUMBER OF LINES CHECKED AS THEY SHOULD HAVE EXACLTY 4 ELEMENTS
            #THEREFORE ALL THE OVERHEAD (LOG) IS SKIPPED
            if len(line) == 4:

                #LOOP THROUGH ALL CODES AND CHECK WHICH CODE FITS THIS SPECIFIC LINE
                for codes in self.all_codes:
                    if codes["regex"].match(line[0]):
                        if codes["geometry"] != "POINT":
                            code = line[code_pos]
                            group_start = int(codes["groupid"][0])
                            group_len = int(codes["groupid"][1])
                            group_end = group_start + group_len

                            code_group = code[group_start:group_end]
                            codes["groups"].append(code_group)
                            codes["coords"].append([code, QgsPoint(float(line[e_pos]),float(line[n_pos])), line[h_pos]])

                        elif codes["geometry"] == "POINT":
                            code = line[code_pos]
                            codes["coords"].append([code, QgsPoint(float(line[e_pos]),float(line[n_pos])), line[h_pos]])

        #only leave distinct codes in the dictionary
        for codes in self.all_codes:
            if codes["geometry"] != "POINT":
                codes["groups"] = list(set(codes["groups"]))

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
                dict_code = dict.fromkeys(["name", "regex", "geometry", "groupby", "groupid", "polygon", "groups", "export", "coords"])
                dict_code["coords"] = []
                dict_code["groups"] = []
                dict_code["polygons"] = []
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
                    # ==========================================================


                    # GET EPSG CODE
                    if i == 2:
                        if "EPSG" in line:
                            epsg_code = line.split("#")[0].strip().split(":")[1]
                            self.epsg = epsg_code
                        else:
                            QMessageBox.information(None, "ERROR:", "NO EPSG CODE FOUND IN LINE %i..." % i)
                            return None
                    # ==========================================================


                    # ==========================================================
                    # ALL OTHER LINES CONTAIN CODE
                    # ==========================================================
                    if i > 2:
                        len_code = 0
                        len_before = 0
                        a = 0

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

                            #GET LENGTH OF STRING BEFORE GROUP BY CODE
                            for i in range(0, int(group_by)-1):
                                if code_parts[i].isdigit():
                                    len_code = int(code_parts[i])

                                elif '"' in code_parts[i]:
                                    raw_code = code_parts[i]
                                    code = raw_code.replace('"',"")
                                    len_code = len(code)

                                elif code_parts[i].isalpha():
                                    len_code = len(code_parts[i])

                                len_before += len_code
                            dict_code['groupid'] = [len_before]
                            #===============================================

                            for i in range(0,len(code_parts)):
                                digit_regex = None
                                char_regex = None
                                sep_regex = None

                                if code_parts[i].isdigit():
                                    # ==========================================
                                    # GET NUMBERS INDICATING NUMBER ranges
                                    # 1 --> [0 - 9]
                                    # 2 --> [00 - 99]
                                    # 3 --> [000 - 999]
                                    # 4 --> [0000 - 9999]
                                    # ==========================================
                                    nr_digits = code_parts[i]
                                    len_code = int(nr_digits)

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
                                    len_code = len(code)

                                    if len(code) == 1:
                                        sep = code
                                        sep_regex = re.compile(sep)
                                    else:
                                        sep = ""
                                        sep_regex = re.compile("")
                                # ==============================================

                                # ==============================================
                                # EXTRACT CODECS
                                # CAN BE ANY COMBINATION of lower and UPPER case
                                # ==============================================
                                elif code_parts[i].isalpha():
                                    char_regex = re.compile(code_parts[i])
                                    len_code = len(code_parts[i])
                                # ==============================================

                                # ==============================================
                                # GET LENGTH OF CODE THAT GROUPS POLYGONS
                                if i == int(group_by) - 1:
                                    if geom_type == "POLYGON" or geom_type == "POLYLINE":
                                        dict_code["groupid"].append(len_code)
                                    else:
                                        dict_code["groupid"] = None
                                # ==============================================


                                if char_regex != None:
                                    line_regex.append(char_regex.pattern)

                                elif digit_regex != None:
                                    line_regex.append(digit_regex.pattern)

                                elif sep_regex != None:
                                    line_regex.append(sep_regex.pattern)

                                #if geom_type == "POLYGON" or geom_type == "POLYLINE":

                                    #-1: in the CODES FILE the GROUP BY STARTS WITH 1
                                    #as we only need the places BEFORE the code we need

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
            name = codes["name"].replace('"', "")
            geom = codes["geometry"]
            out = '|'.join(codes["export"])

            if codes["geometry"] != "POINT":
                group = codes["groupid"]
            else:
                group = ""
            #self.dlg.txtbox_code_preview.insertHtml("%s %s %s %s<br>" % (name, geom, out, group))
            self.dlg.txtbox_code_preview.insertPlainText("%s\t%s\t%s\t%s\n" % (name, geom, out, group))

        # ======================================================================
        # SELECT CODES FILE FINISH
        # ======================================================================
