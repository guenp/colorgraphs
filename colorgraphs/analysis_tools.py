# analysis tools
__author__ = 'Guen P'
import pandas as pd
import numpy as np
from scipy.interpolate import griddata

def interpolate_y(x,y,z,numpoints=1000,method='nearest',fill_value=0):
	'''
	Take 2D array that is linear in x and nonlinear in y and return equally spaced grid
	Input: x,y,z (1D pandas Series), numpoints = number of points in y of new grid
	Output: xgrid,ygrid,zgrid (2D np arrays)
	'''
	# these are the 1D x and y arrays for the final grid
	xvals = x.unique()
	yvals = np.linspace(min(y), max(y), numpoints)
	ygrid,xgrid = np.meshgrid(yvals,xvals)

	nx = len(xvals)
	ny_ = int(np.floor(len(x)/nx)) #original number of points in y (before interpolation)
	ny = numpoints #num of points in y after interpolation

	if np.mean(np.diff(x[:ny_])) == 0: # x = step, y = sweep
		xgrid_ = x.reshape(nx,ny_)
		ygrid_ = y.reshape(nx,ny_)
		zgrid_ = z.reshape(nx,ny_)
	else: # x = sweep, y = step
		xgrid_ = x.reshape(ny_,nx).transpose()
		ygrid_ = y.reshape(ny_,nx).transpose()
		zgrid_ = z.reshape(ny_,nx).transpose()

	zgrid = []
	for yrow,zrow,i in zip(ygrid_,zgrid_,np.arange(0,len(zgrid_))):
		zgrid.append(griddata(yrow,zrow,yvals,method=method,fill_value=fill_value))
	
	return xgrid, ygrid, np.array(zgrid)