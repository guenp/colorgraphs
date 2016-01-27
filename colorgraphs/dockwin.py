# main graphing ui and server interface
__author__ = 'Guen P'

import sys,os,logging
import pyqtgraph as pg
import numpy as np
import signal
import json
from scipy.interpolate import griddata
import pandas as pd
import datetime, time
import re
from IPython.display import display

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QLocalServer
from pyqtgraph.dockarea import DockArea, Dock

from .graphwidgets import plot as plotwidget
from .gutil import get_config
from .data import load_multiple, analyse, get, save_data, _ANALYSIS_FOLDER, _DATA_FOLDER

__author__ = 'Guen'

config = get_config()

logging.root.setLevel(logging.DEBUG)
pg.setConfigOption('background', config.get('Style','BackgroundColor'))
pg.setConfigOption('foreground', config.get('Style','ForegroundColor'))
_MAIN_WINDOW_SIZE = eval(config.get('Graphs','MainWindowSize')) if type(eval(config.get('Graphs','MainWindowSize')))==tuple else (500,500)
_BASE_PATH = os.path.split(os.path.realpath(__file__))[0]
_IMG_PATH = os.path.join(_BASE_PATH,'images')

# Create a class for our main window
class DockWin(QtGui.QMainWindow):
    docklist = []
    def __init__(self):
        logging.debug('Creating main window.')
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("colorgraphs dock")
        self.dockarea = DockArea()
        self.setCentralWidget(self.dockarea)
        self.resize(*_MAIN_WINDOW_SIZE)
        self.initUI()
        self.show()
        self.raise_()

    def initUI(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.white)
        
        self.setPalette(palette)
        # loadAction = QtGui.QAction(QtGui.QIcon(os.path.join(_IMG_PATH,'load.png')), '&Load', self)
        # loadAction.setShortcut('Ctr+O')
        # loadAction.setStatusTip('Load dataset')
        # loadAction.triggered.connect(load_action)

        # saveAction = QtGui.QAction(QtGui.QIcon(os.path.join(_IMG_PATH,'save.png')), '&Save', self)
        # saveAction.setShortcut('Ctr+S')
        # saveAction.setStatusTip('Save dataset')
        # saveAction.triggered.connect(save_action)

        # self.statusBar()

        # toolbar = self.addToolBar('Load')
        # toolbar.addAction(loadAction)
        # toolbar.addAction(saveAction)

    def create_dock(self, name='', loc='right', widget=None):
        if name == '':
            name = 'Graph%s' %len(self.docklist)
        if name in [dock.name() for dock in self.docklist]:
            dock = {dock.name(): dock for dock in self.docklist}[name]
            dock.close()
            self.docklist.remove(dock)
        dock = Dock(name)
        if widget:
            self.dockarea.addDock(dock, loc, widget)
        else:
            self.dockarea.addDock(dock, loc)
        DockWin.docklist.append(dock)
        return dock

    def add_widget(self, w, loc='right'):
        '''
        Add widget to the dock.
        w = widget, loc = location ('right', 'left', 'behind', etc.)
        '''
        dock = self.create_dock(w.name, loc)
        dock.addWidget(w)
        w.show()

    def add_widgets(self, wlist):
        '''
        Add a number of widgets to the dock.
        Spread evenly.
        '''
        for w in wlist:
            dock = self.create_dock(w.name, loc)
        for dock in docklist:
            dock.addWidget(w)

    def close_all(self):
        docklist = self.docklist
        for dock in docklist:
            dock.close()
            docklist.remove(dock)
            del(dock)

    def plot(self, *args, **kwargs):
        w = plotwidget(*args, **kwargs)
        self.add_widget(w)

    def _repr_png_(self):
        for d in self.dockarea.docks.values():
            display(d.widgets[0])

    def close(self):
        logging.debug('Close')

# def plot1d(x, y, name='', xlabel=('',), ylabel=('',)):
#     '''
#     Lineplot
#     x,y (np.array)
#     '''
#     app = get_instance()
#     if not hasattr(app,'is_running'):
#         app.mw.create_1dplot(x, y, title=name, xlabel=xlabel, ylabel=ylabel)
#     else:
#         data = (x,y)
#         message = {'name': name, 'labels': (xlabel, ylabel)}
#         app.send_data(data, message)

# def plot2d(x, y, z, name='', xlabel=('',), ylabel=('',), zlabel=('',)):
#     '''
#     Plot 2d colorplot
#     x,y,z (np.array): equally spaced grid data
#     '''
#     app = get_instance()
#     if not hasattr(app,'is_running'):
#         app.mw.create_2dplot(x, y, z, name=name, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel)
#     else:
#         data = (x,y,z)
#         message = {'name': name, 'labels': (xlabel, ylabel, zlabel)}
#         app.send_data(data, message)

# def plot(d):
#     '''
#     Plot contents of analysed dataframe
#     '''
#     name = d.meta['name']
#     xlabel = d.x.label
#     ylabel = d.y.label
#     x,y = d.x.reshape(d.meta['shape']),d.y.reshape(d.meta['shape'])
#     if len(d.keys())==3:
#         zlabel = d.z.label
#         z = d.z.reshape(d.meta['shape'])
#         plot2d(x,y,z,name,xlabel,ylabel,zlabel)
#     elif len(d.keys())==2:
#         plot1d(x,y,name,xlabel,ylabel)

def get_filepaths():
    fileDialog = QtGui.QFileDialog()
    filepaths = fileDialog.getOpenFileNames(directory = _DATA_FOLDER)
    return filepaths

def load_action():
    filepaths = get_filepaths()
    if '.json' in filepaths[0]:
        load_state(filepaths[0])
    elif filepaths:
        dlist = load_multiple(filepaths)
        for d in dlist:
            plot(analyse(d))

def save_action():
    fileDialog = QtGui.QFileDialog()
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
    filepath = fileDialog.getSaveFileName(directory = os.path.join(_ANALYSIS_FOLDER, '%s.json' %timestamp))
    if filepath:
        save_state(filepath)

def save_state(filepath):
    # get current state properties
    state_json, stamps, names, levels, colormaps = get_current_state()
    state_json['levels'] = levels
    state_json['colormaps'] = colormaps
    # save to json file
    with open(filepath, 'w') as json_file:
        json_file.write(json.dumps(state_json, indent='\t'))
    return state_json, stamps, names, filepath

def load_state(filepath):
    # get state_json from file
    with open(filepath, 'r') as json_file:
        state_json = json.load(json_file)
    levels = state_json.pop('levels')
    colormaps = state_json.pop('colormaps')
    names = levels.keys()
    stamps = [name[:15] for name in names]

    for stamp in stamps:
        plot(analyse(stamp))
    get_instance().mw.dockarea.restoreState(state_json)

    for dock in get_instance().mw.docklist:
        w = dock.widgets[0]
        w.setLevels(*levels[dock.name()])
        w.ui.histogram.gradient.setColorMap(pg.ColorMap(*colormaps[dock.name()]))

def get_current_state():
    state_json = get_instance().mw.dockarea.saveState()
    stamps = re.findall(r'[0-9]+_[0-9]+',json.dumps(state_json))
    names = re.findall(r'[0-9]+_[0-9]+_[a-zA-Z0-9 _=]+',json.dumps(state_json))
    levels = {dock.name(): dock.widgets[0].ui.histogram.item.getLevels() for dock in get_instance().mw.docklist}
    colormaps = {dock.name(): (dock.widgets[0].ui.histogram.gradient.colorMap().pos.tolist(),dock.widgets[0].ui.histogram.gradient.colorMap().color.tolist()) for dock in get_instance().mw.docklist}
    return state_json, stamps, names, levels, colormaps

def save_all():
    state, stamps, names, filepath = save_state()
    filepath = filepath.replace('.json','')

    if not os.path.exists(filepath):
        os.mkdir(filepath)

    for stamp,name in zip(stamps,names):
        d = analyse(stamp)
        save_data(d, filepath=os.path.join(filepath,'%s.dat' %name))

def close_all():
    docklist = get_instance().mw.docklist
    for dock in docklist:
        dock.close()
        docklist.remove(dock)

def get_instance():
    if not QApplication.instance():
        return main()
    else:
        return QApplication.instance()

def show():
    get_instance().mw.show()

def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
        app.mw = DockWin()
        app.mw.show()
    return app