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

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QLocalServer
from pyqtgraph.dockarea import DockArea, Dock

from .gutil import get_config
from .data import load_multiple, analyse, get, _ANALYSIS_FOLDER, _DATA_FOLDER

__author__ = 'Guen'

config = get_config()

logging.root.setLevel(logging.DEBUG)
pg.setConfigOption('background', config.get('Style','BackgroundColor'))
pg.setConfigOption('foreground', config.get('Style','ForegroundColor'))
_DOCK_POSITION = config.get('Graphs','NewGraphPosition')
_MAIN_WINDOW_SIZE = eval(config.get('Graphs','MainWindowSize')) if type(eval(config.get('Graphs','MainWindowSize')))==tuple else (500,500)
_BASE_PATH = os.path.split(os.path.realpath(__file__))[0]
_IMG_PATH = os.path.join(_BASE_PATH,'images')
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

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.white)
        
        self.setPalette(palette)

        loadAction = QtGui.QAction(QtGui.QIcon(os.path.join(_IMG_PATH,'load.png')), '&Load', self)
        loadAction.setShortcut('Ctr+O')
        loadAction.setStatusTip('Load dataset')
        loadAction.triggered.connect(load_action)

        saveAction = QtGui.QAction(QtGui.QIcon(os.path.join(_IMG_PATH,'save.png')), '&Save', self)
        saveAction.setShortcut('Ctr+S')
        saveAction.setStatusTip('Save dataset')
        saveAction.triggered.connect(save_action)

        self.statusBar()

        toolbar = self.addToolBar('Load')
        toolbar.addAction(loadAction)
        toolbar.addAction(saveAction)

    def create_dock(self, name=''):
        if name == '':
            name = 'Graph%s' %len(self.docklist)
        if name in [dock.name() for dock in self.docklist]:
            dock = {dock.name(): dock for dock in self.docklist}[name]
            dock.close()
            self.docklist.remove(dock)
        dock = Dock(name)
        self.dockarea.addDock(dock,_DOCK_POSITION)
        Main.docklist.append(dock)
        return dock

def load_action():
    fileDialog = QtGui.QFileDialog()
    filepaths = fileDialog.getOpenFileNames(directory = _DATA_FOLDER)
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
        yvals = y[0]
        pos = (xvals[0],yvals[0])
        scale = (np.mean(np.diff(xvals)), np.mean(np.diff(yvals)))
        plt = (pg.PlotItem(title=name, labels={'bottom': xlabel,'left': ylabel}))
        w = pg.ImageView(view=plt)
        w.ui.histogram.gradient.setColorMap(_mango_clrmp)
        w.setImage(z, pos=pos, scale=scale)
        w.view.setAspectLocked(False)
        w.view.invertY(False)
        w.autoRange()
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

def save_data(d, filepath = None, name=None):
    '''
    Save Z column of dataset in .dat file (gnuplot format)
    '''
    zmatrix = d.z.reshape(d.meta['shape'])
    zlabel, xlabel, xmin, xmax, ylabel, ymin, ymax = d.z.label, d.x.label, d.x.min(), d.x.max(), d.y.label, d.y.min(), d.y.max()
    if not name:
        name = d.meta['name']

    if not filepath:
        fileDialog = QtGui.QFileDialog()
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
        filepath = fileDialog.getSaveFileName(directory = _ANALYSIS_FOLDER + '%s_%s.dat' %(timestamp, name))
    
    open(filepath,'w').close()
    open(filepath.replace('.dat','.txt'),'w').close()

    with open (filepath,'a') as proc_seqf:
        for c_row in zmatrix:
            for c in c_row:
                proc_seqf.write(("{}\n").format(c))
            proc_seqf.write("\n\n")
    with open (filepath.replace('.dat','.txt'),'a') as proc_seqf:
        proc_seqf.write(("{}\n{}\n{}\n{}\n").format(len(zmatrix[0]),xmin,xmax,xlabel))
        proc_seqf.write(("{}\n{}\n{}\n{}\n").format(len(zmatrix),ymin,ymax,ylabel))
        proc_seqf.write(("1\n{}\n").format(zlabel))

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
        app.is_running = False
        app.mw = Main()
        app.mw.show()

    # d = get('20150713_022632')
    # d1 = d[d.Bpar<3.5]
    # d1.meta = d.meta
    # d2 = analyse(d1)
    # plot(d2)
    # if app.is_running:
    #     app.send_message(sys.argv)
    return app