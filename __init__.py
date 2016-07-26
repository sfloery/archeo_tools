# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ArcheoTool
                                 A QGIS plugin
 Collection of tools for archaeologists
                             -------------------
        begin                : 2016-07-26
        copyright            : (C) 2016 by Martin Fera, Sebastian Floery
        email                : s.floery@gmx.at
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ArcheoTool class from file ArcheoTool.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .archeo_tool import ArcheoTool
    return ArcheoTool(iface)
