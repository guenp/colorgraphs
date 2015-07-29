import pyqtgraph as pg
import pandas as pd
import numpy as np
import sys,time,os
from pyqtgraph.exporters import ImageExporter, SVGExporter
from PyQt4 import QtGui, QtCore
from PyQt4.Qt import QImage, QPainter, QBuffer, QIODevice, QByteArray, SIGNAL
from IPython.core.display import SVG
from IPython.html import widgets
from IPython.display import display, clear_output
import pyqtgraph.functions as fn
from pyqtgraph.Point import *
import signal

from .gutil import get_image_path, get_config, _mango_clrmp

__author__ = 'Guen P'

config = get_config()
_window_size = eval(config.get('Graphs','WidgetSize'))
pg.setConfigOption('background', config.get('Style','BackgroundColor'))
pg.setConfigOption('foreground', config.get('Style','ForegroundColor'))

def get_instance():
    '''
    Get QApplication instance, if doesn't exist create one
    '''
    if not pg.QtGui.QApplication.instance():
        return pg.QtGui.QApplication([])
    else:
        return pg.QtGui.QApplication.instance()

class BasePlotWidget():
    '''
    Base widget for Plot1DWidget and Plot2DWidget
    Creates close and crosshair buttons
    '''
    widgetlist = []
    def __init__(self, title, xlabel=('x',), ylabel=('y',), window_size=_window_size):
        self.label = None
        self.parametric = False
        self.snap_to_datapoints = False
        self.crosshair = False
        self.labels = (xlabel, ylabel) if len(xlabel)>1 else ((xlabel[0],''), (ylabel[0],''))

        style = QtGui.QStyleFactory().create("windows")
        close_icon = style.standardIcon(QtGui.QStyle.SP_TitleBarCloseButton)
        self.close_button = QtGui.QPushButton(close_icon, "", self)
        self.close_button.clicked.connect(self.closeAction)
        self.close_button.setGeometry(0, 0, 20, 20)
        self.close_button.raise_()

        crosshair_icon = pg.QtGui.QIcon(os.path.join(get_image_path(),'crosshair.png'))
        self.crosshair_button = pg.QtGui.QPushButton(crosshair_icon, '', self)
        self.crosshair_button.clicked.connect(self.toggle_crosshair)
        self.crosshair_button.setGeometry(20, 0, 20, 20)
        self.crosshair_button.raise_()

        self.widgetlist.append(self)
        self.setWindowTitle(title)
        self.name = title
        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.connect(self, SIGNAL('triggered()'), self.closeAction)
        signal.signal(signal.SIGINT, self.closeAction)

        self.resize(*window_size)

        def func(btn):
            if self.in_dock():
                self.show()
                self.window().show()
                self.window().raise_()
            else:
                self.show()
                self.raise_()

        self.btn = widgets.Button(description="Open graph")
        self.btn.on_click(func)
        self.btn.visible = False

    def in_dock(self):
        try:
            return self.window()!=self
        except:
            return False

    def closeAction(self,event):
        clear_output(wait=True)
        display(self)
        self.hide()

    def toggle_crosshair(self):
        if not self.crosshair:
            self.add_crosshair()
            self.crosshair = True
        else:
            self.remove_crosshair()
            self.crosshair = False

    def add_crosshair(self):
        self.crosshair = True
        self.move_crosshair_on = True
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.addItem(self.h_line, ignoreBounds=False)
        self.addItem(self.v_line, ignoreBounds=False)
        item = self.view if type(self)==Plot2DWidget else self.getPlotItem()
        if not self.label:
            self.label = pg.LabelItem(justify="right")
        else:
            self.label.show()
        item.layout.addItem(self.label, 4, 1)
        scene = self.scene() if callable(self.scene) else self.scene
        scene.sigMouseMoved.connect(self.move_crosshair)
        scene = self.scene() if callable(self.scene) else self.scene
        scene.sigMouseClicked.connect(self.toggle_move_crosshair)

    def remove_crosshair(self):
        self.removeItem(self.h_line)
        self.removeItem(self.v_line)
        self.label.hide()
        item = self.view if type(self)==Plot2DWidget else self.getPlotItem()
        item.layout.removeItem(self.label)
        if self.move_crosshair_on:
            scene = self.scene() if callable(self.scene) else self.scene
            scene.sigMouseMoved.disconnect()
            self.move_crosshair_on = False

    def move_crosshair(self, mouse_event):
        item = self.view if type(self)==Plot2DWidget else self.getPlotItem()
        vb = item.getViewBox()
        view_coords = vb.mapSceneToView(mouse_event)
        view_x, view_y = view_coords.x(), view_coords.y()
        (pt_x, pt_y) = (view_x, view_y)
        self.v_line.setPos(pt_x)
        self.h_line.setPos(pt_y)
        self.label.setText("%s=%.2e %s, %s=%.2e %s" % (self.labels[0][0], pt_x, self.labels[0][1], self.labels[1][0],pt_y, self.labels[1][1]))

    def toggle_move_crosshair(self, mouse_event):
        if self.move_crosshair_on:
            scene = self.scene() if callable(self.scene) else self.scene
            scene.sigMouseMoved.disconnect()
            self.move_crosshair_on = False
        else:
            scene = self.scene() if callable(self.scene) else self.scene
            scene.sigMouseMoved.connect(self.move_crosshair)
            self.move_crosshair_on = True

class Plot1DWidget(pg.PlotWidget, BasePlotWidget):
    '''
    Widget for 1D plotting
    x,y: 1D numpy arrays
    title: str
    xlabel,ylabel: tuple ('label', 'unit')
    window_size: tuple (width,height)
    '''
    def __init__(self,x=[],y=[],title='Graph',xlabel=('x',), ylabel=('y',), window_size=_window_size):
        pg.PlotWidget.__init__(self,title=title)
        BasePlotWidget.__init__(self, title, xlabel, ylabel, window_size)
        self.plot(x,y)
        self.setLabels(bottom=xlabel, left=ylabel)

    def _repr_png_(self):
        self.show()
        self.hide()
        if not self.btn.visible:
            display(self.btn)
            self.btn.visible = True

        mainExp = ImageExporter(self.plotItem)
        self.image = mainExp.export(toBytes=True)

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.ReadWrite)
        self.image.save(buffer, 'PNG')
        buffer.close()

        return bytes(byte_array)

class Plot2DWidget(pg.ImageView, BasePlotWidget):
    '''
    Widget for 1D plotting
    x,y,z: 2D numpy arrays, square data
    title: str
    xlabel,ylabel: tuple ('label', 'unit')
    window_size: tuple (width,height)
    '''
    def __init__(self,x=[],y=[],z=[],title='Graph',xlabel=('x',), ylabel=('y',), window_size=_window_size):

        plt = (pg.PlotItem(title=title, labels={'bottom': xlabel,'left': ylabel}))
        pg.ImageView.__init__(self,view=plt)
        BasePlotWidget.__init__(self, title, xlabel, ylabel, window_size)

        xvals = x.unique() if type(x)==pd.Series else pd.Series(x.flatten()).unique()
        yvals = y.unique() if type(y)==pd.Series else pd.Series(y.flatten()).unique()

        pos = (xvals[0],yvals[0])
        scale = (np.mean(np.diff(xvals)), np.mean(np.diff(yvals)))

        self.ui.histogram.gradient.setColorMap(_mango_clrmp)
        self.setImage(z, pos=pos, scale=scale)
        self.view.setAspectLocked(False)
        self.view.invertY(False)
        self.view.autoRange(padding=0)
        self.ui.roiBtn.hide() # Hide the ROI button on display
        self.ui.menuBtn.hide() # Hide the Norm button on display

        roi_icon = pg.QtGui.QIcon(os.path.join(get_image_path(),'roi.png'))
        self.roi_button = pg.QtGui.QPushButton(roi_icon, '', self)
        self.roi_button.clicked.connect(self.toggle_roi)
        self.roi_button.setGeometry(40, 0, 20, 20)
        self.roi_button.raise_()
        self.line_roi = pg.LineSegmentROI([[min(xvals)+(max(xvals)-min(xvals))*.25,min(yvals)+(max(yvals)-min(yvals))*.25], [min(xvals)+(max(xvals)-min(xvals))*.75,min(yvals)+(max(yvals)-min(yvals))*.75]], pen='r')
        self.line_roi.sigRegionChanged.connect(self.update_roi)
        self.xdata,self.ydata,self.zdata = x,y,z

        signal.signal(signal.SIGINT, self.closeEvent)

    def update_roi(self):
        axes=(0,1)
        # self.line_data = self.line_roi.getArrayRegion(self.zdata, self.imageItem, axes=(0,1))
        img = self.imageItem
        imgPts = [self.line_roi.mapToItem(img, h['item'].pos()) for h in self.line_roi.handles]
        d = Point(imgPts[1] - imgPts[0])
        o = Point(imgPts[0])
        z = fn.affineSlice(self.zdata, shape=(int(d.length()),), vectors=[Point(d.norm())], origin=o, axes=axes, order=1)
        x = fn.affineSlice(self.xdata, shape=(int(d.length()),), vectors=[Point(d.norm())], origin=o, axes=axes, order=1)
        y = fn.affineSlice(self.ydata, shape=(int(d.length()),), vectors=[Point(d.norm())], origin=o, axes=axes, order=1)
        self.line_data = (x,y,z)

    def toggle_roi(self):
        if self.line_roi in self.view.items:
            self.removeItem(self.line_roi)
        else:
            self.addItem(self.line_roi)

    def getQImage(self, resX=None,resY=None):
        #zoom the the chosen colorrange:
        r = self.ui.histogram.region.getRegion()
        self.ui.histogram.vb.setYRange(*r)
        #create ImageExporters:
        mainExp = ImageExporter(self.view)
        colorAxisExp = ImageExporter(self.ui.histogram.axis)
        colorBarExp = ImageExporter(self.ui.histogram.gradient)

        if resX or resY:
            #get size-x:
            mainW = mainExp.getTargetRect().width()
            colorAxisW = colorAxisExp.getTargetRect().width()
            colorBarW = colorBarExp.getTargetRect().width()

            #all parts have the same height:
            mainExp.parameters()['height'] = resY
            colorAxisExp.parameters()['height'] = resY
            colorBarExp.parameters()['height'] = resY
            #size x is proportional:
            sumWidth = mainW + colorAxisW + colorBarW
            mainExp.parameters()['width'] = resX * mainW / sumWidth
            colorAxisExp.parameters()['width'] = resX * colorAxisW / sumWidth
            colorBarExp.parameters()['width'] = resX * colorBarW / sumWidth
        #create QImages:
        main =mainExp.export(toBytes=True)
        colorAxis =colorAxisExp.export(toBytes=True)
        colorBar = colorBarExp.export(toBytes=True)
        #define the size:
        x = main.width() + colorAxis.width() + colorBar.width()
        y = main.height()
        #to get everything in the same height:
        yOffs = [0,0.5*(y-colorAxis.height()),0.5*(y-colorBar.height())]
        result = QtGui.QImage(x, y ,QtGui.QImage.Format_RGB32)

        #the colorbar is a bit smaller that the rest. to exclude black lines paint all white:

        result.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(result)
        posX = 0
        for img,y in zip((main,colorAxis,colorBar),yOffs):
            #draw every part in different positions:
            painter.drawImage(posX, y, img)
            posX += img.width()
        painter.end()
        return result

    def _repr_png_(self):
        if not self.in_dock():
            self.show()
            self.hide()
        else:
            self.window().show()
            self.window().hide()

        if not self.btn.visible:
            display(self.btn)
            self.btn.visible = True

        QtGui.QApplication.processEvents()
        
        self.image = self.getQImage()

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.ReadWrite)
        self.image.save(buffer, 'PNG')
        buffer.close()
        return bytes(byte_array)

def plot(x=[], y=[], z=[], title='Graph', xlabel='x', ylabel='y', clabel='', window_size=_window_size):
    '''
    Create 1D or 2D plot widget
    '''
    if pg.QtGui.QApplication.instance():
        if len(z)>0:
            if type(x)==pd.Series:
                xlabel = x.name
                ylabel = y.name
                title = '%s vs %s' %(xlabel, ylabel)
                s = (len(y.unique()),len(x.unique()))
                x = x.reshape(s)
                y = y.reshape(s)
                z = z.reshape(s).transpose()
            else:
                w = Plot2DWidget(x,y,z,title,xlabel,ylabel,window_size)
        else:
            if len(y)>0:
                w = Plot1DWidget(x,y,title,xlabel,ylabel,window_size)
            elif len(x)>0:
                w = Plot1DWidget(np.arange(0,len(x)),x,title,xlabel,ylabel,window_size)
        return w