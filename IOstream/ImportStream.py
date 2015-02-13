# -*- coding: utf-8 -*-
"""
"""

def read_csv(path, column_mapping=None, parse_ogr=False, **kwds):
    """
    Function wrapper for pandas.read_csv. path and kwds are passed to read_csv 
    and the resulting DataFrame will be returned. 
    If the csv-like file do not contain a 'lon' and 'lat' column, column_mapping 
    dict can be passed to rename all columns. Then 'lon' and 'lat' have to be 
    mapped onto the correct column keys. 
    In case mapsta_version is set and gives the Mapsta GPS tracker version as 
    at least 3-digit integer, all kwds will be overwritten in order to import 
    the GPS tracker file automatically according to locomotif.settings.mapsta 
    module.
    If parse_ogr is True, the lon and lat column will be replaced by a geom 
    column containing the OGR Geometry representing a point. This is needed in 
    case the df will be used as Cluster in an locomotif.Grid object.
    """
    import pandas as pd

    # check if a predefined mapsta version was given
    # this would replace all other kwds
    try:
        if kwds['mapsta_version'].__class__ == int:
            # a mapsta version number is given, overwrite kwds
            from locomotif.settings.mapsta import get_csv_options
            kwds = get_csv_options(kwds['mapsta_version'])
            
        # delete mapsta_versions before passing it to pd.read_csv
        del kwds['mapsta_version']
    except KeyError:
        # kwds['mapsta_version was not set']
        pass
    
    # read the csv file at path
    df = pd.read_csv(path, **kwds)            
    
    # in case lon and lat are not specified so far, column_mapping 
    # shall be used for renaming the columns
    if column_mapping is not None:
        df.rename(column_mapping)
        try:
            df[['lon', 'lat']]
        except KeyError:
            raise KeyError('The files has to contain a lon and a lat coulmn, or they have to be mapped using column_mapping keword.')
    
    if parse_ogr:
        # TODO: this will be converted into an parsing function

        # extract coordinates as numpy array and convert to wkt string
        wkt = ["POINT ({0} {1})".format(x,y) for x,y in df[['lon', 'lat']].values]
        
        # copy df without lon and lat column
        df1 = df.drop('lon', 1).drop('lat', 1)
        
        # import ogr
        from osgeo import ogr
        
        # convert wkt to OGR.Geometry
        geom = [ogr.CreateGeometryFromWkt(string) for string in wkt]
        
        # set as column in df1
        df1['geom'] = geom
        
        # return
        return df1
    else:
        return df

