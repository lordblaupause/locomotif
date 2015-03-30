# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:51:31 2015

@author: maelicke
"""

from osgeo import ogr, osr
from datetime import datetime as dt
import pandas as pd
import os

class FileHandler(object):
    """
    """
    def __init__(self, path, DataFrame=None, SpatialReference=None, driver="ESRI Shapefile", **kwds):
        """
        Create the Folder at path for initialization and load Driver
        """
        # if path does not exsist -> create it
        if not os.path.exists(path):
            # create
            os.mkdir(path)
        
        # check if directory or file was given
        if os.path.isdir(path):
            self.path = path
        elif os.path.isfile(path):
            self.path = os.path.dirname(path)
        
        # append the slash to path
        if not path.endswith("/"):
            self.path = self.path + "/"
        
        # check if name was given and is the same as path basename
        # if not create it
        if 'name' in kwds:
            if os.path.basename(os.path.normpath(self.path)) != kwds['name']:
                # create a new folder
                self.path = self.path + kwds['name']
                if not os.path.exists(self.path):
                    os.mkdir(self.path)
                self.path = self.path + "/"
                
        

        
            
        # check SpatialReference
        if SpatialReference is None or not isinstance(SpatialReference, osr.SpatialReference):
            self.ref = osr.SpatialReference()
            self.ref.ImportFromEPSG(4326)
        else:
            self.ref = SpatialReference
        
        # create Shapefile driver
        try:
            self.driver = ogr.GetDriverByName(driver)
        except:
            raise TypeError("The driver '{0}' cannot be loaded. Make sure this is a valid OGR driver name and GDAL_DATA is set as environment variable.".format(driver))
        
        # pass DataFrame if given
        if DataFrame is not None:
            if 'name' in kwds:
                name = kwds['name']
            else: 
                name = None
            self.createFromDataFrame(DataFrame, name)
            
        
        
    def createFromDataFrame(self, DataFrame, name=None, width=20, precision=5):
        """
        create ESRI Shapefile from DataFrame. Check the DataFrame for having 
        an geometry column and various amount of data columns. Name is used as 
        shp filename.
        The values are created as a OFTReal field with width and precision
        """
        # handle file name
        if name is None:
            name = 'loc{0.year}{0.month}{0.day}{0.hour}{0.minute}{0.second}.shp'.format(dt.now())
        elif not name.endswith('.shp'):
            name = name + ".shp"
         
        # check DataFrame class
        if not isinstance(DataFrame, pd.DataFrame):
            raise TypeError("DataFrame has to be an pandas:DataFrame, found {0}".format(DataFrame.__class__))
        
        if not 'geometry' in DataFrame.columns or 'geom' in DataFrame.columns:
            raise TypeError("The DataFrame needs a column called 'geom' or 'geometry' for storing OGR Geometries")
        

        ### create file ###
        shpfile = self.driver.CreateDataSource(self.path + name)
        # create layer use name as layername
        layer = shpfile.CreateLayer(name.split('.')[0], self.ref)
        
        ### create a field for each column, which is not a geometry column ###
        for col in DataFrame.columns:
            if col not in ('geometry', 'geom'):
                field = ogr.FieldDefn(col, ogr.OFTReal)
                # width of
                field.SetWidth(width)
                field.SetPrecision(precision)
                # create
                layer.CreateField(field)
        
        # get the geometry column
        try:
            geometry = DataFrame.geom
        except:
            geometry = DataFrame.geometry
        
        # Create Features
        for i in range(len(geometry)):
            # create feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # set geometry
            feature.SetGeometry(geometry[i])
            
            # set all values
            for col in DataFrame.columns:
                if col not in ('geometry', 'geom'):
                    feature.SetField(col, float(DataFrame[col][i]))
            
            # add feature to layer
            layer.CreateFeature(feature)
            feature.Destroy()
            
            numberOfFeatures = i
        
        # close the Shapefile
        shpfile.Destroy()
        
        return numberOfFeatures