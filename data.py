# data loading
__author__ = 'Guen'

import sys,os,glob,fnmatch
import configparser, logging
import numpy as np
import pandas as pd
import json
from .gutil import get_config
from PyQt4 import QtGui
import imp
config = get_config()

_DATA_FOLDER = config.get('Data','DataFolder')
_ANALYSIS_FOLDER = config.get('Analysis', 'AnalysisFolder')
sys.path.append(_ANALYSIS_FOLDER)
_analysis_module = __import__(config.get('Analysis', 'AnalysisModule'))

def analyse(stamp, analysis_module = _analysis_module):
	'''
	Perform module_name.do_analyse function on d (pandas dataframe) and return result
	'''
	d = get(stamp)
	m=imp.reload(_analysis_module)
	return m.do_analyse(d)

def load():
	'''
	Open file dialog and load .dat or .csv
	Return pandas dataframe with bonus attributes .filepath, .stamp and .meta (from meta/json file)
	'''
	if not QtGui.QApplication.instance():
		QtGui.QApplication(sys.argv)
	fileDialog = QtGui.QFileDialog()
	filepath = fileDialog.getOpenFileName(directory = _DATA_FOLDER)
	extension = filepath[-4:]
	if '.dat' in filepath:
		d = pd.read_csv(filepath,sep='\t')
	elif '.csv' in filepath:
		d = pd.read_csv(filepath)
	else:
		raise Warning("Can't load data. Please supply a .dat or .csv file.")
		d = pd.DataFrame()
	jsonfile = os.path.join(os.path.join(os.path.split(filepath)[0],'meta'),os.path.split(filepath)[1].replace(extension,'.json'))
	d.meta = json.load(open(jsonfile)) if os.path.exists(jsonfile) else {}
	d.meta['filepath'] = filepath
	d.meta['stamp'] = os.path.split(filepath)[1][:15]
	d.meta['name'] = os.path.split(filepath)[1][:-4]
	return d

def load_multiple():
	'''
	Open file dialog and load .dat or .csv
	Return pandas dataframe with bonus attributes .filepath, .stamp and .meta (from meta/json file)
	'''
	if not QtGui.QApplication.instance():
		QtGui.QApplication(sys.argv)
	fileDialog = QtGui.QFileDialog()
	filepaths = fileDialog.getOpenFileNames(directory = _DATA_FOLDER)
	dlist = []
	for filepath in filepaths:
		extension = filepath[-4:]
		if '.dat' in filepath:
			d = pd.read_csv(filepath,sep='\t')
		elif '.csv' in filepath:
			d = pd.read_csv(filepath)
		else:
			raise Warning("Can't load data. Please supply a .dat or .csv file.")
			d = pd.DataFrame()
		jsonfile = os.path.join(os.path.join(os.path.split(filepath)[0],'meta'),os.path.split(filepath)[1].replace(extension,'.json'))
		d.meta = json.load(open(jsonfile)) if os.path.exists(jsonfile) else {}
		d.meta['filepath'] = filepath
		d.meta['stamp'] = os.path.split(filepath)[1][:15]
		d.meta['name'] = os.path.split(filepath)[1][:-4]
		dlist.append(d)
	return dlist

def get(stamp):
	'''
	Get data with given stamp (str), format date_time, found in _DATA_FOLDER
	Return pandas dataframe with bonus attributes .filepath, .stamp and .meta (from meta/json file)
	'''
	if type(stamp)==str:
		filepath, jsonfile = find_datafiles(stamp)
		if '.dat' in filepath:
			d = pd.read_csv(filepath, sep='\t')
		elif '.csv' in filepath:
			d = pd.read_csv(filepath)
		else:
			raise Warning('Extension not .dat or .csv.')
			d = pd.DataFrame()
		d.meta = json.load(open(jsonfile)) if jsonfile else {}
		d.meta['filepath'] = filepath
		d.meta['stamp'] = stamp
		d.meta['name'] = os.path.split(filepath)[1][:-4]
	elif type(stamp)==pd.DataFrame:
		d = stamp
	return d

def find_datafiles(stamp):
	'''
	Return *.dat or *.csv and *.json file matches (list) for given stamp (str), format date_time, found in _DATA_FOLDER
	'''
	data_matches = []
	json_matches = []
	for root, dirnames, filenames in os.walk(_DATA_FOLDER):
		for filename in fnmatch.filter(filenames, '%s*.dat' %stamp):
			data_matches.append(os.path.join(root, filename))
		for filename in fnmatch.filter(filenames, '%s*.csv' %stamp):
			data_matches.append(os.path.join(root, filename))
		for filename in fnmatch.filter(filenames, '%s*.json' %stamp):
			json_matches.append(os.path.join(root, filename))
	if len(data_matches)>1:
		raise Warning('Multiple datafiles found with stamp.')
	return data_matches[0], json_matches[0]