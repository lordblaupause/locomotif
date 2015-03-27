# -*- coding: utf-8 -*-
"""
"""

import pandas as pd
import numpy as np
from osgeo import osr, ogr
import spatial

class Grid(object):
    """
    """
    def __init__(self, data, SpatialReference):
        """
        """
        
        # check if SpatialReference is of type osr.SpatialReference
        if SpatialReference.__class__ != osr.SpatialReference().__class__:
            raise TypeError("SpatialReference does not have a valid OSR spatial reference type.")
        else:
            self.SpatialReference = SpatialReference
        
        
        if data.__class__ == list:
            # check all elements
            if not all(isinstance(geom, ogr.Geometry) for geom in data):
                # check for beeing list of OGR geometries
                raise TypeError("data is a list but does not only contain osgeo.Geometry objects.")
            else:
                self.data = data
        else:
            # check if data is nested in two dimensions
            try:
                self.data = np.array(data)
                
                if self.data.ndim != 2 and self.data.ndim != 3:
                    raise TypeError("data has to be a two dimensional list containing the grid cells, found {0} dimnesions".format(self.data.ndim))
            except TypeError:
                raise TypeError("data has to be of type (or castable into) numpy.array. Failed on found type: {0}.".format(data.__class__))
        
    
    def getSpatialReference(self, asWKT=False):
        """
        Returns the used SpatialReference. On default the osr.SpatialReference 
        object itself is returned, if asWKT is True, it will be retunred as WKT.
        """
        if asWKT:
            return self.SpatialReference.ExportToWkt()
        else:
            return self.SpatialReference

    
    def setCluster(self, DataFrame, geometry_column=None, parse_geometry=True):
        """
        Set a new point cluster for the Grid. This contains a point cloud of 
        OGR geometries and one or more value columns, linking attributes to 
        these sample points. for each value column, a DataFrame of geometry value 
        combinations is created and set as Grid attribute, where the attribute 
        name is the former value column name. 
        By this, an Grid object can handle a various amount of point clusters.
        """
#        import pandas as pd
        from osgeo import ogr
        
        # check DataFrame class
        if DataFrame.__class__ != pd.DataFrame().__class__:
            raise TypeError("The pandas DataFrame is of invlalid type {0}.".format(DataFrame.__class__))
        
        # find geometry column
        if geometry_column is not None:
            pass
        else:
            # shall it be parsed
            if parse_geometry:
                # check any column for containing OGR Geometries
                for column in DataFrame:
                    if all([item.__class__ == ogr.Geometry().__class__ for item in DataFrame[column]]):
                        # if all item contain an OGR Geometries => use this column
                        geometry_column = str(column)
                # check if an geometry column was found
                if geometry_column is None:
                    # TODO: insert a locomotif exception here?
                    raise Exception('No geometry column could be found')
            else:
                raise AttributeError('If the geometry column shall not be parsed, give the geometry_column.')
        
        ### geometry column is known now ###
        # go for all other column and create Cluster DataFrames
        for column in DataFrame:
            # check this column not to be the geometry column
            if column == geometry_column:
                continue
            else:
                setattr(self, column, pd.DataFrame({'geometry':DataFrame[geometry_column], 'value':DataFrame[column]}))
    
                
    
    def voronoi(self, cluster,  SpatialReference=None, wgs84=True, as_array=False, inplace=False):
        """
        An Voronoi diagram is computed from the given point cloud. These points 
        should be included in the underlying grid, otherwise this function might 
        lead to undefined behaviour. The point cloud cluster is identified by 
        its name and had to be set beforehand using Grid.setCluster.
        SpatialReference shall be given for the points in the cluster, otherwise 
        they will be transformed to the grid spatial reference system. At this 
        stage this tranformation is not supported yet.
        The distances for each cell are computed as geodetic distances on the 
        basis of EPSG:4326.
        If Spatial Reference is none and wgs84 is True, WGS84, EPSG 4326 will 
        be used by default.
        
        """
        from osgeo import osr
        import pandas as pd
                    
        # check SpatialReference
        if SpatialReference is None and wgs84:
            # Use EPSG: 4326 (WGS84) as default
            SpatialReference = osr.SpatialReference()
            SpatialReference.ImportFromEPSG(4326)
            
        if SpatialReference.__class__ != osr.SpatialReference().__class__:
            raise TypeError("SpatialReference is not a valid. Found type {0}.".format(SpatialReference.__class__))

#        if not self.SpatialReference.IsSame(SpatialReference):
#            raise Warning('At this stage only operations within the same SpatialReference are supported.')

        # check if given cluster exists
        try:
            layer = getattr(self, cluster)
        except AttributeError:
            raise AttributeError('This Grid has no point cluster of name {0}. Initialize using Grid.setCluster'.format(cluster))
        
        if layer.__class__ != pd.DataFrame().__class__:
            raise AttributeError('The point cluster {0} is corrupted. Type pandas.DataFrame is needed, found {1}'.format(cluster, layer.__class__))
        
        ### now, cluster is a list of points and spatial reference is the same ###

        # container for the voroni areas
        # it has to have the same length of 1st dim of self.data
        # one value per cell        
        voronoi = np.ndarray(len(self.data))  
        
        ### create a distance map for all grid cells ###
        # for each cell, all distances to each point in the cluster is calculated
        # the value of minimum
        
        # iterate data
        for i, cell in enumerate(self.data):
            # get midpoint as OGR Geometry
#            mid = spatial.rect_midpoint(cell, True)
            mid = cell.Centroid()
            
            # get all distances
            # TODO: ref_x and ref_y have to be given aswell as soon as geodesic_distance will convert correctly
            distance_map = layer['geometry'].apply(spatial.geodesic_distance, y=mid, ref_x=self.getSpatialReference(), ref_y=SpatialReference)
            
            # get the value of minimum
            idx = distance_map.idxmin()
            voronoi[i] = layer.value[idx]
        
        
        result = pd.DataFrame({cluster:voronoi, 'geom':self.data})
        # TODO: try to speed up this function
        return result, self.getSpatialReference()
    