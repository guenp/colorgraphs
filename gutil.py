import configparser,glob,os
import pyqtgraph as pg

__author__ = 'Guen P'

def get_mango():
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
  return _mango_clrmp

def get_image_path():
    _BASE_PATH = os.path.split(os.path.realpath(__file__))[0]
    return os.path.join(_BASE_PATH,'images')

def get_config():
    config = configparser.ConfigParser()
    if not glob.glob("*.conf"):
        # use default config
        configfile=os.path.join(os.path.dirname(__file__),'default.conf')
    else:
        configfile = os.path.join(os.getcwd(),glob.glob("*.conf")[0])
    config.read(configfile)
    return config