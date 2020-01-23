#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehumancommunity.org/

**Github Code Home Page:**    https://github.com/makehumancommunity/

**Authors:**           Marc Flerackers, Jonas Hauquier, Thomas Larsson

**Copyright(c):**      MakeHuman Team 2001-2019

**Licensing:**         AGPL3

    This file is part of MakeHuman (www.makehumancommunity.org).

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Abstract
--------

Clothes library.
"""

import proxychooser

import gui3d
import gui
import log


#
#   Clothes
#

class ClothesTaskView(proxychooser.ProxyChooserTaskView):

    def __init__(self, category):
        super(ClothesTaskView, self).__init__(category, 'clothes', multiProxy = True, tagFilter = True)

        self.faceHidingTggl = self.optionsBox.addWidget(FaceHideCheckbox("Hide faces under %s"  % self.proxyName))
        @self.faceHidingTggl.mhEvent
        def onClicked(event):
            self.updateFaceMasks(self.faceHidingTggl.selected)
        @self.faceHidingTggl.mhEvent
        def onMouseEntered(event):
            self.visualizeFaceMasks(True)
        @self.faceHidingTggl.mhEvent
        def onMouseExited(event):
            self.visualizeFaceMasks(False)
        self.faceHidingTggl.setSelected(True)

        self.oldPxyMats = {}
        self.blockFaceMasking = False

    def createFileChooser(self):
        self.optionsBox = self.addLeftWidget(gui.GroupBox('Options'))
        super(ClothesTaskView, self).createFileChooser()

    def getObjectLayer(self):
        return 10

    def proxySelected(self, pxy):
        self.human.addClothesProxy(pxy)
        self.updateFaceMasks(self.faceHidingTggl.selected)

    def proxyDeselected(self, pxy, suppressSignal = False):
        uuid = pxy.uuid
        self.human.removeClothesProxy(uuid)
        if not suppressSignal:
            self.updateFaceMasks(self.faceHidingTggl.selected)

    def resetSelection(self):
        super(ClothesTaskView, self).resetSelection()
        self.updateFaceMasks(self.faceHidingTggl.selected)

    def onShow(self, event):
        super(ClothesTaskView, self).onShow(event)
        if gui3d.app.getSetting('cameraAutoZoom'):
            gui3d.app.setGlobalCamera()

    def onHide(self, event):
        super(ClothesTaskView, self).onHide(event)
        self.visualizeFaceMasks(False)

    def loadHandler(self, human, values, strict):
        #TODO: get this optimization to all the proxychoosers
        if values[0] == 'status':
            if values[1] == 'started':
                # Don't update face masks during loading (optimization)
                self.blockFaceMasking = True
            elif values[1] == 'finished':
                # When loading ends, update face masks
                self.blockFaceMasking = False
                self.updateFaceMasks(self.faceHidingTggl.selected)
            return

        if values[0] == 'clothesHideFaces':
            enabled = values[1].lower() in ['true', 'yes']
            self.faceHidingTggl.setChecked(enabled)
            return

        super(ClothesTaskView, self).loadHandler(human, values, strict)

    def onHumanChanged(self, event):
        super(ClothesTaskView, self).onHumanChanged(event)
        if event.change == 'reset':
            self.faceHidingTggl.setSelected(True)  # TODO super already reapplies masking before this is reset

    def saveHandler(self, human, file):
        super(ClothesTaskView, self).saveHandler(human, file)
        file.write('clothesHideFaces %s\n' % str(self.faceHidingTggl.selected))

    def registerLoadSaveHandlers(self):
        super(ClothesTaskView, self).registerLoadSaveHandlers()
        gui3d.app.addLoadHandler('clothesHideFaces', self.loadHandler)

    def visualizeFaceMasks(self, enabled):
        import material
        import getpath
        if enabled:
            self.oldPxyMats = dict()
            xray_mat = material.fromFile(getpath.getSysDataPath('materials/xray.mhmat'))
            for pxy in self.human.getProxies(includeHumanProxy=False):
                if pxy.type == 'Eyes':
                    # Don't X-ray the eyes, it looks weird
                    continue
                self.oldPxyMats[pxy.uuid] = pxy.object.material.clone()
                pxy.object.material = xray_mat
        else:
            for pxy in self.human.getProxies(includeHumanProxy=False):
                if pxy.uuid in self.oldPxyMats:
                    pxy.object.material = self.oldPxyMats[pxy.uuid]

class FaceHideCheckbox(gui.CheckBox):
    def enterEvent(self, event):
        self.callEvent("onMouseEntered", None)

    def leaveEvent(self, event):
        self.callEvent("onMouseExited", None)


# TODO: consider generalizing moving everything below to proxychooser

# This method is called when the plugin is loaded into makehuman
# The app reference is passed so that a plugin can attach a new category, task, or other GUI elements

taskview = None

def load(app):
    global taskview

    category = app.getCategory('Geometries')
    taskview = ClothesTaskView(category)
    taskview.sortOrder = 0
    category.addTask(taskview)

    taskview.registerLoadSaveHandlers()

# This method is called when the plugin is unloaded from makehuman
# At the moment this is not used, but in the future it will remove the added GUI elements


def unload(app):
    taskview.onUnload()

