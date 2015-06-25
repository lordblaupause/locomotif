# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 13:06:10 2015

@author: maelicke
"""

def polygon_intersect(clusters, only_polygon=True, no_lines=True, **kwargs):
    """
    Takes exactly two pandas.DataFrames containing a 'geometry' and 'value' 
    column. The polygons will be intersected and filled with the mean value
    of the two value fields. other aggregation can be passed.
    Result is returned as pandas.DataFrame.
    
    geometry has to contain OGR Polygon geometries
    value has to be of type int, float (or numpy ints, floats)
    
    **kwargs: func=np.XX pass function for intersection to be used over np.mean.
    """
    import pandas as pd
    
    if not isinstance(clusters, list):
        raise AttributeError('The input clusters have to be given as a list of DataFrames')
    
    #### DEVELOPMENT
    if not len(clusters) == 2:
        raise AttributeError('For now, only exactly two cluster layers can be processed, you passed {0}.'.format(len(clusters)))
    
    if not all([isinstance(cluster, pd.DataFrame) for cluster in clusters]):
        raise AttributeError('clusters has to contain exactly 2 pandas.DataFrames.\nFound other types.')
    
    # get the input data
    x = clusters[0]
    y = clusters[1]
    
    # ceck for the columns
    if not 'geometry' in x.columns and not 'value' in x.columns:
        raise AttributeError("The first cluster does not have a 'geometry' and 'value' column.")

    if not 'geometry' in y.columns and not 'value' in y.columns:
        raise AttributeError("The first cluster does not have a 'geometry' and 'value' column.")
    
    # check kwargs for other function
    if 'func' in kwargs:
        func = kwargs['func']
    else:
        import numpy as np
        func = np.mean      # default function
    
    ### now the data should be fine 
    ### intersect any feature of x with any feature of y
    ### the value will be the mean
    geometries = []
    values = []
    
    for i, item in x.iterrows():
        # get the geometry of x
        x_geom = item.geometry
        val = item.value
        
        for j, jtem in y.iterrows():
            # go for all y features
            # check for intersection
            if not x_geom.Intersects(jtem.geometry):
                continue
            intersect = x_geom.Intersection(jtem.geometry)
            
            if only_polygon:
                if not intersect.GetGeometryType() == 3:
                    # its not a polygon
                    continue
            
            if no_lines:
                if intersect.GetGeometryType() < 3:
                    # no points, no lines
                    continue
            
            geometries.append(x_geom.Intersection(jtem.geometry))
            values.append(func([val, jtem.value]))
    
    # create a DataFrame and return
    return pd.DataFrame({'geometry':geometries, 'value':values})
            
        
    
    