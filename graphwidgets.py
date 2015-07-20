import pyqtgraph as pg
import pandas as pd
import numpy as np
import sys,time,os
from .gutil import get_image_path

_labels = {
    'Bpar': ('Bpar','T'),
    'Bpary': ('Bpary','T'),
    'Bperp': ('Bperp','T'),
    'X_current': ('Iac','A'),
    'X_voltage2': ('Vac','V'),
    'backgate': ('Vbg','V'),
    'current': ('Idc','A'),
    'dc_source_voltage': ('Vsd_a','V'),
    'temperature': ('T','K'),
    'timer': ('t','s'),
    'topgate': ('Vtg','V'),
    'voltage2': ('Vsd','V')
}

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
from .gutil import get_config
config = get_config()
pg.setConfigOption('background', config.get('Style','BackgroundColor'))
pg.setConfigOption('foreground', config.get('Style','ForegroundColor'))

def get_instance():
    if not pg.QtGui.QApplication.instance():
        return pg.QtGui.QApplication([])
    else:
        return pg.QtGui.QApplication.instance()

class BasePlotWidget():
    widgetlist = []
    def __init__(self, xlabel=('x',), ylabel=('y',)):
        self.label = None
        self.parametric = False
        self.snap_to_datapoints = False
        self.crosshair = False
        self.labels = (xlabel, ylabel) if len(xlabel)>1 else ((xlabel[0],''), (ylabel[0],''))

        crosshair_icon = pg.QtGui.QIcon(os.path.join(get_image_path(),'crosshair.png'))
        crosshair_button = pg.QtGui.QPushButton(crosshair_icon, '', self)
        crosshair_button.clicked.connect(self.toggle_crosshair)
        crosshair_button.setGeometry(0, 0, 20, 20)
        crosshair_button.raise_()
        self.widgetlist.append(self)

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
        if not self.label:
            self.label = pg.LabelItem(justify="right")
            item = self.view if type(self)==Plot2DWidget else self.getPlotItem()
            item.layout.addItem(self.label, 4, 1)
        scene = self.scene() if callable(self.scene) else self.scene
        scene.sigMouseMoved.connect(self.move_crosshair)
        scene = self.scene() if callable(self.scene) else self.scene
        scene.sigMouseClicked.connect(self.toggle_move_crosshair)

    def remove_crosshair(self):
        self.removeItem(self.h_line)
        self.removeItem(self.v_line)
        if self.move_crosshair_on:
            scene = self.scene() if callable(self.scene) else self.scene
            scene.sigMouseMoved.disconnect()
            self.move_crosshair_on = False

    def move_crosshair(self, mouse_event):
        item = self.view if type(self)==Plot2DWidget else self.getPlotItem()
        vb = item.getViewBox()
        view_coords = vb.mapSceneToView(mouse_event)
        view_x, view_y = view_coords.x(), view_coords.y()

        if self.snap_to_datapoints:
            best_guesses = []
            for data_item in item.items:
                if isinstance(data_item, pg.PlotDataItem):
                    xdata, ydata = data_item.xData, data_item.yData
                    index_distance = lambda i: (xdata[i]-view_x)**2 + (ydata[i] - view_y)**2
                    if self.parametric:
                        index = min(range(len(xdata)), key=index_distance)
                    else:
                        index = min(np.searchsorted(xdata, view_x), len(xdata)-1)
                        if index and xdata[index] - view_x > view_x - xdata[index - 1]:
                            index -= 1
                    pt_x, pt_y = xdata[index], ydata[index]
                    best_guesses.append(((pt_x, pt_y), index_distance(index)))

            if not best_guesses:
                return

            (pt_x, pt_y), _ = min(best_guesses, key=lambda x: x[1])
        else:
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
    def __init__(self,x=[],y=[],title='Graph',xlabel=('x',), ylabel=('y',), d=None):
        if type(d)==pd.DataFrame:
            xlabel,ylabel = d.x.label, d.y.label
            x = d.x.reshape(d.meta['shape'])
            y = d.y.reshape(d.meta['shape'])
            title = d.meta['name']

        pg.PlotWidget.__init__(self,title=title)
        BasePlotWidget.__init__(self, xlabel, ylabel)
        self.plot(x,y)
        self.setLabels(bottom=xlabel, left=ylabel)

class Plot2DWidget(pg.ImageView, BasePlotWidget):
    def __init__(self,x=[],y=[],z=[],title='Graph',xlabel=('x',), ylabel=('y',), d=None):
        if type(d)==pd.DataFrame:
            xlabel,ylabel,zlabel = d.x.label, d.y.label, d.z.label
            x = d.x.reshape(d.meta['shape'])
            y = d.y.reshape(d.meta['shape'])
            z = d.z.reshape(d.meta['shape'])
            title = d.meta['name']

        plt = (pg.PlotItem(title=title, labels={'bottom': xlabel,'left': ylabel}))
        pg.ImageView.__init__(self,view=plt)
        BasePlotWidget.__init__(self, xlabel, ylabel)

        xvals = x.unique() if type(x)==pd.Series else pd.Series(x.flatten()).unique()
        yvals = y[0]

        pos = (xvals[0],yvals[0])
        scale = (np.mean(np.diff(xvals)), np.mean(np.diff(yvals)))

        self.ui.histogram.gradient.setColorMap(_mango_clrmp)
        self.setImage(z, pos=pos, scale=scale)
        self.view.setAspectLocked(False)
        self.view.invertY(False)
        self.autoRange()
        self.ui.roiBtn.hide() # Hide the ROI button on display
        self.ui.menuBtn.hide() # Hide the Norm button on display

def plot(d):
    '''
    Create plot widget and plot data in dataframe d
    '''
    s = d.meta['shape']
    x,y,z = d.x.reshape(s),d.y.reshape(s),d.z.reshape(s)
    w = Plot2DWidget(x,y,z,d.meta['name'],d.x.label,d.y.label)
    w.show()