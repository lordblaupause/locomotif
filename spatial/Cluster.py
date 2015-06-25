# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 12:48:16 2015

@author: maelicke
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from osgeo import ogr, osr
import spatial, voronoi

class Cluster(object):
    """
    The locomotif Cluster objects manages all imported (GPS) data and 
    offers interpolation and modelling functions. Results can be exported from
    this object.
    """
    def __init__(self, DataFrame=None, SpatialReference=None, geometry_column=None, debug=False):
        """
        DataFrame is a pandas.DataFrame including a column of OGR POINT geometries.
        This column can be identified by geometry_column, if None, the first 
        occurance of a column containg only OGR POINT Geometry objects will be used.
        SpatialReference has to be of Type osr.SpatialReference giving the correct 
        reference for the geometries. If None given, WGS84 (EPSG:4326) is assumed.
        This only works if GDAL_PATH is set in environment.
        The debug mod is used internal only. only in debug mode, a None DataFrame is allowed. 
        If the Cluster runs in debug mode, its functions can return all internal variables, 
        this creates HUGE overload and shall only be used during development 
        """
        # use default spatial reference
        if SpatialReference is None:
            self.SpatialReference = osr.SpatialReference()
            self.SpatialReference.ImportFromEPSG(4326)
            
        # check if SpatialReference is of type osr.SpatialReference
        elif isinstance(SpatialReference, osr.SpatialReference):
            self.SpatialReference = SpatialReference            
        else:
            raise TypeError("SpatialReference does not have a valid OSR spatial reference type.")
        
        # create a list of all datasets
        self.datasets = []
        
        ### DataFrame has to contain a column of OGR Point Geometries ###
        if isinstance(DataFrame, pd.DataFrame):
            ### no geometry_column ==> search it ### 
            if geometry_column is None:
                # parse the geometry column
                for column in DataFrame:
                    # check all items
                    if all([isinstance(item, ogr.Geometry) for item in DataFrame[column]]):
                        geometry_column = str(column)
                    
                # number of found geometry columns
                if geometry_column is None:
                    raise AttributeError("No geometry_column could be found. use geometry_column to pass column name.")
                    
            ### found geometry_column ###        
            elif isinstance(geometry_column, str):
                if not geometry_column in DataFrame.columns:
                    raise AttributeError("DatFrame does not contain a column {0}.".format(geometry_column))
            else:
                raise TypeError("geometry_column as to be a str or NoneType, found {0}".format(geometry_column.__class__))
            
            ### check all geometries to be points ###
            if not all([item.GetGeometryName() == 'POINT' for item in DataFrame[geometry_column]]):
                raise TypeError("The column {0} contains other Geometries than 'POINT'.".format(geometry_column))
            
            ### append all value columns ###
            # this should identy the geometry column
            for column in DataFrame:
                # if geometry column ==> continue
                if column == geometry_column:
                    continue
                else:
                    # set  a DataFrame for each found value column
                    setattr(self, column, pd.DataFrame({'geometry':DataFrame[geometry_column], 'value':DataFrame[column]}))
                    
                    # append name to dataset
                    self.datasets.append(column)
        elif DataFrame is None:
            if not debug:
                ### This option shall not be used, only by import functions ###
                raise Exception("DataFrame can only be of NoneType in debug mode.")
        else:
            raise TypeError("DataFrame has to be given as pandas.DataFrame, found {0}".format(DataFrame.__class__))
        if debug:
            self.debug = True
        else:
            self.debug = False
    
    
    def getSpatialReference(self, asWKT=False):
        """
        Returns the used SpatialReference. On default the osr.SpatialReference 
        object itself is returned, if asWKT is True, it will be retunred as WKT.
        """
        if asWKT:
            return self.SpatialReference.ExportToWkt()
        else:
            return self.SpatialReference

    
    def getDatasets(self, objects=False):
        """
        Returns all names of all datasets in this instance as list. If objects 
        is True, the DataFrames are also returned in a dict of 'name':DataFrame.
        """
        if objects:
            return {dataset:getattr(self, dataset) for dataset in self.datasets}
        else:
            return self.datasets
            
    def getDataset(self, name):
        """
        Return the DataFrame identified by name. This is the same as self.name.
        """
        try:
            dataset = getattr(self, name)
        except:
            raise AttributeError("This Cluster does not have a point cluster called '{0}'.".format(name))
        
        return dataset
        

    def dropDataset(self, name):
        """
        Returns and then drops the given dataset.
        """
        # check if dataset name is set
        try:
            dataset = getattr(self, name)
        except AttributeError as e:
            raise AttributeError(e.message)
        
        # delete the Attribute
        delattr(self, name)
        
        # remove the name from self.datasets
        self.datasets.remove(name)
            
        # return the deleted object
        return dataset
        
    def _setDataset(self, DataFrame, name):
        """
        Direct setting of Datasets. This is only enabled in debug mode.
        The DataFrame is NOT checked.
        """
        if not self.debug:
            raise Exception("Direct DataFrame setting is only available in debug mode.")
        
        # set Dataset
        setattr(self, name, DataFrame)
        
        # set name
        self.datasets.append(name)
        

    def model(self, func, clusters, as_list=True, inplace=False, **kwargs):
        """
        One or more cluster layer can be calculated to a new cluster layer using 
        the funciton given as func. The function result will be returned.
        This function has to accept the clusters and **kwargs, if set, as attributes.
        the clusters are passed either as list, or as **cluster, like:
        clustername=cluster.
        """
        # check if func is callable
        if not hasattr(func, '__call__'):
            raise AttributeError('func is not callable')
        
        # check if clusters is a str or list of str
        if isinstance(clusters, str):
            clusters = [clusters]
        if isinstance(clusters, list):
            if not all([isinstance(item, str) for item in clusters]):
                raise AttributeError("clsuters has to be either a string or list of strings identifying all cluster layers to be used.")
        
        # load all clusters
        if as_list:
            data = [self.getDataset(cluster) for cluster in clusters]
        else:
            data = {cluster:self.getDataset(cluster) for cluster in clusters}
        
        # call the function
        if as_list:
            out = func(data, **kwargs)
        else:
            attr = data.update(kwargs)
            out = func(**attr)
        
        if inplace:
            self.setDebug(True)
            self._setDataset(out, func.__name__)
            self.setDebug(False)
        else:
            return out

    
    def delaunay(self, cluster, func='mean'):
        """
        Delaunay triangulation is used to create a triangle connecting three 
        neighbouring points. For each triangle an interpolated value using 
        given func aggregation function is given. The geometries and values are 
        exported as pandas.DataFrame.
        This Dataframe has a 'geometry' column containing the OGR POLYGON 
        Geometry objects and a 'value' column containing the values.
        """
#        try:
#            data = getattr(self, cluster)
#        except:
#            raise AttributeError("This Cluster does not have a point cluster called '{0}'.".format(cluster))
        data = self.getDataset(cluster)
        
        # create Delaunay object
        delaunayObject = Delaunay(spatial.dfToArray(data))
        
        # get the triangle points
        tri = delaunayObject.points[delaunayObject.simplices]
        
        ### the tri does only contain the edges points, for converting to 
        # polygons, the first point has to be appended to close the structure
        # TODO: translate into pure numpy , maybe use insert or concat
        triangle = np.asarray([[x[0], x[1], x[2], x[0]] for x in tri.tolist()])
        
#        # mindfuck
#        strings = []
#        for obj in triangle:
#            strings.append(','.join(["{0} {1}".format(x[0], x[1]) for x in obj]))
#            
#        # create OGR POLYGON Geometry objects
#        polys = [ogr.CreateGeometryFromWkt("POLYGON (({0}))".format(x)) for x in strings]
        #create OGR Geomteries
        polys = spatial.ArrayToPolygon(triangle)
        
        #delaunayObject.simplices stores the indices of correct points
        values = [data.value[x].mean() for x in delaunayObject.simplices]
        
        return pd.DataFrame({'geometry':polys, 'value':values}), self.getSpatialReference()
    
    
    def voronoi(self, cluster, frame=None, debug=False):
        """
        Voronoi Polygons are created around each point. All edge points out of 
        bounds and at infinity are calculated to the intersection with bounds.
        The used function in locomotif.spatial.voronoi are from neothemachine (GitHub) at:
        https://gist.github.com/neothemachine/8803860
        The outer Polygons exceeding the point cluster dimensions are clipped by 
        frame. This can be of any closed polygon shape. As a numpy.ndarray of four 
        points is given, the bouding box will be created of this. If frame is None,
        the boundary will be computed from the Point cluster. 
        If debug is True and the Cluster instance is in debug mode, this function
        will return [frame, vor, out,  raw, polys, value]. Do only use if you 
        know what this means
        """
        ### Process Data ###
        # get the clsuter
        data = self.getDataset(cluster)
        
        ### Check Input Data ###
        # frame is an Geometry, check if its a Polygon
        if isinstance(frame, ogr.Geometry):
            if frame.GetGeometryName() != 'POLYGON':
                raise TypeError("frame has to be of Geometry type 'POLYGON', but is {0}.".format(frame.GetGeometryName()))
        else:
            # get the Envelope of all Points
            if frame is None:
                geocollection = ogr.Geometry(ogr.wkbGeometryCollection)
                # add all points
                [geocollection.AddGeometry(point) for point in data.geometry]
                
                # create edge points
                e = geocollection.GetEnvelope()
                # envelope returns [minX, maxX, minY, maxY]
            
            # frame is a list of maximum points
            elif isinstance(frame, list):
                if len(frame) != 4:
                    raise TypeError("If frame is a list, give [minX, maxX, minY, maxY]")
                else:
                    e = frame
            else:
                raise TypeError("frame has to be a POLYGON, list or None, found {0}.".format(frame.__class__))
            
            # create the frame
            frame = ogr.CreateGeometryFromWkt("POLYGON (({0} {1}, {2} {3}, {4} {5}, {6} {7}, {8} {9}))".format(
                e[0], e[2], e[1], e[2], e[1], e[3], e[0], e[3], e[0], e[2]))
        
        try:
            vor = voronoi.polygons(spatial.dfToArray(data))
        except AssertionError:
            raise Exception("The Points are maybe too close together for Voronoi Polygons. Use Delaunay or transform your points.")

        if not len(vor) == len(data.value):
            raise Exception("For some reason number of points and polygons do not match.\nFound:\n points:\t{0}\n polygons:{1}".format(len(data.value), len(vor)))
        
        ### the vor does only contain the edges points, for converting to 
        # polygons, the first point has to be appended to close the structure
        out = []        
        for obj in vor:
            x = obj.tolist()
            x.append(x[0])
            out.append(np.asarray(x))
        
        raw = spatial.ArrayToPolygon(out)
        
        # intersect all polygons with frame
        polys = [poly.Intersection(frame) for poly in raw]
        
        ### debug mode output ###
        if debug and self.debug:
            return [frame, vor, out,  raw, polys, data.value]

        return pd.DataFrame({'geometry':polys, 'value':data.value}), self.getSpatialReference()
    
    
    def setDebug(self, boolean=None):
        """
        Changes the debug mode to boolean. If None self.debug is returned
        """
        if boolean is None:
            return self.debug            
        else:
            self.debug = bool(boolean)
        
            
