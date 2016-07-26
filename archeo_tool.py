# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ArcheoTool
                                 A QGIS plugin
 Collection of tools for archaeologists
                              -------------------
        begin                : 2016-07-26
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Martin Fera, Sebastian Floery
        email                : s.floery@gmx.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
#from archeo_tool_dialog import ArcheoToolDialog
import os.path

#Import own tools
from tools.codes2geom import Codes2Geom
from tools.harris_matrix import HarrisMatrix


class ArcheoTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        print self.plugin_dir
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ArcheoTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        # Declare instance attributes
        #self.actions = []
        #self.menu = self.tr(u'&Archeo Tool')
        # TODO: We are going to let the user set this up in a future
        self.toolbar = self.iface.addToolBar(u'ArcheoTool')
        self.toolbar.setObjectName(u'ArcheoTool')

        # Get the tools
        self.codes2geom = Codes2Geom(self.iface, self.toolbar)
        self.harris_matrix = HarrisMatrix(self.iface, self.toolbar)

    def unload(self):
        del self.toolbar
