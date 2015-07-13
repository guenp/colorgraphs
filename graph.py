# main graphing ui and server interface
__author__ = 'Guen P'

import sys,os,logging
import pyqtgraph as pg
import numpy as np
import signal
import json
from scipy.interpolate import griddata
import pandas as pd

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QLocalServer
from pyqtgraph.dockarea import DockArea, Dock

from .singleton import SingletonApp
from .gutil import get_config
from .data import load_multiple, analyse
from .graphserver import GraphServer

__author__ = 'Guen'

config = get_config()

logging.root.setLevel(logging.DEBUG)
pg.setConfigOption('background', config.get('Style','BackgroundColor'))
pg.setConfigOption('foreground', config.get('Style','ForegroundColor'))
_DOCK_POSITION = config.get('Graphs','NewGraphPosition')
_MAIN_WINDOW_SIZE = eval(config.get('Graphs','MainWindowSize')) if type(eval(config.get('Graphs','MainWindowSize')))==tuple else (500,500)

_mango = {'mode': 'rgb',
 'ticks': [(0.0, (0, 0, 0, 255)),
  (0.23091904761904761, (8, 136, 255, 255)),
  (0.42976190476190479, (69, 203, 89, 255)),
  (0.60945714285714281, (255, 208, 17, 255)),
  (0.794047619047619, (255, 163, 71, 255)),
  (1.0, (255, 255, 255, 255))]}

_predefColormaps = pg.graphicsItems.GradientEditorItem.Gradients
_predefColormaps['mango'] = _mango

_mango_clrmp = pg.ColorMap([ticks[0] for ticks in _mango['ticks']],[ticks[1] for ticks in _mango['ticks']])

# Create a class for our main window
class Main(QtGui.QMainWindow):
    docklist = []
    def __init__(self):
        logging.debug('Creating main window.')
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Colorgraphs")
        self.dockarea = DockArea()
        self.setCentralWidget(self.dockarea)
        self.resize(*_MAIN_WINDOW_SIZE)
        self.initUI()

    def initUI(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)

        loadAction = QtGui.QAction(QtGui.QIcon('graphite.png'), '&Load', self)
        loadAction.setShortcut('Ctr+O')
        loadAction.setStatusTip('Load dataset')
        loadAction.triggered.connect(load_analyse_plot)

        self.statusBar()

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)
        toolbar.addAction(loadAction)

    def create_dock(self, name=''):
        if name == '':
            name = 'Graph%s' %len(self.docklist)
        dock = Dock(name)
        self.dockarea.addDock(dock,_DOCK_POSITION)
        Main.docklist.append(dock)
        return dock

def load_analyse_plot():
    dlist = load_multiple()
    for d in dlist:
        plot(analyse(d))

def plot1d(x, y, name='', xlabel=('',), ylabel=('',)):
    '''
    Lineplot
    x,y (np.array)
    '''
    app = get_instance()
    if not app.is_running:
        dock = app.mw.create_dock(name)
        w = pg.PlotWidget(title=name)
        w.plot(x,y)
        w.setLabels(bottom=xlabel, left=ylabel)
        w.setWindowTitle(name)
        dock.addWidget(w)
    else:
        data = (x,y)
        message = {'name': name, 'labels': (xlabel, ylabel)}
        app.send_data(data, message)

def plot2d(x, y, z, name='', xlabel=('',), ylabel=('',), zlabel=('',)):
    '''
    Plot 2d colorplot
    x,y,z (np.array): equally spaced grid data
    '''
    app = get_instance()
    if not app.is_running:
        dock = app.mw.create_dock(name)
        xvals = pd.Series(x.flatten()).unique()
        yvals = pd.Series(y.flatten()).unique()
        pos = (xvals[0],yvals[0])
        scale = (np.mean(np.diff(xvals)), np.mean(np.diff(yvals)))
        plt = (pg.PlotItem(title=name, labels={'bottom': xlabel,'left': ylabel}))
        w = pg.ImageView(view=plt)
        w.ui.histogram.gradient.setColorMap(_mango_clrmp)
        w.setImage(z, pos=pos, scale=scale)
        w.ui.roiBtn.hide() # Hide the ROI button on display
        w.ui.menuBtn.hide() # Hide the Norm button on display
        dock.addWidget(w)
    else:
        data = (x,y,z)
        message = {'name': name, 'labels': (xlabel, ylabel, zlabel)}
        app.send_data(data, message)

def plot(d):
    '''
    Plot contents of analysed dataframe
    '''
    name = d.meta['name']
    xlabel = (d.x.label,d.x.units)
    ylabel = (d.y.label,d.y.units)
    x,y = d.x.reshape(d.meta['shape']),d.y.reshape(d.meta['shape'])
    if len(d.keys())==3:
        zlabel = (d.z.label,d.z.units)
        z = d.z.reshape(d.meta['shape'])
        plot2d(x,y,z,name,xlabel,ylabel,zlabel)
    elif len(d.keys())==2:
        plot1d(x,y,name,xlabel,ylabel)

def get_instance():
    if not QApplication.instance():
        return GraphServer()
    else:
        return QApplication.instance()

def main():
    app = QApplication(sys.argv)
    app.is_running = False
    app.mw = Main()
    app.mw.show()
    # if app.is_running:
    #     app.send_message(sys.argv)
    return app