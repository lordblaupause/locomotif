# -*- coding: utf-8 -*-
"""
"""


def get_edges(df, margins=None, relative=True, geometry_column='geom'):
    """
    The surrounding edge points for given scatter points of longitude and 
    latitude pairs is given. These points can be used for creating an 
    overlaying raster. For enlarging the border use margin. You can pass a 
    single margin or a list of four [up, right, down, left]. If relative is True 
    margin will be interpreted as a relative number between 0 and 1 applied to 
    the length of each border. E.g. margin=0.1 and relative=True will enlarge 
    each border by 10%. If relative is False the marign will be interpreted as 
    absolute units in the dimension of lon and lat in the DataFrame. 
    Note: df needs the geometries in a column called 'geom' containing 
    osgeo.ogr.Geometry Point definitions. A different column name can be passed 
    using geometry_column argument.
    
    @todo: check class and content of geom. 
    @todo: accept column index for geometry_column
    """
    from pandas import DataFrame, Series
    # get the geometry column
    geom = getattr(df, geometry_column)    
    
    # find min and max for lon and lat
    # get a lon series
    lons = Series([x.GetPoint()[0] for x in geom])
    lats = Series([x.GetPoint()[1] for x in geom])
    
    # get edges
    minlon = lons.min()
    minlat = lats.min()
    maxlon = lons.max()
    maxlat = lats.max()
    
    # create the frame cutting the outermost points
    frame = DataFrame(data=[[maxlon, maxlat], [maxlon, minlat], [minlon, minlat], [minlon, maxlat]], columns=['lon', 'lat'], index=['ur', 'dr', 'dl', 'ul'])
    
    # create margin
    if margins is not None:
        # parse margins
        if margins.__class__ == list:
            if len(margins) == 4:
                # use margins as is
                mgn = margins
            elif len(margins) == 2:
                # only two values are given: horizontal, vertical
                mgn = [margins[0], margins[1], margins[0], margins[1]]
            else:
                raise TypeError('margins has to be on lengths 2 or 4, got %d' % len(margins))
            
        elif margins.__class__ == int or margins.__class__ == float:
            # margins are all equal
            mgn = 4 * [margins]
        else:
            raise TypeError('margins has to be of Type list, int or float, got %s' % margins.__class__)
    
        ## margins are now availible as mgn[4]
        # get side lengths
        up = down = maxlon - minlon
        right = left = maxlat - minlat
        
        if relative:
            mgn = [up * mgn[0], right * mgn[1], down * mgn[2], left * mgn[3]]
        
        # add margins to points:
        # add up margin to ur and ul
        frame.ix[0].lat += mgn[0]
        frame.ix[3].lat += mgn[0]
        
        # add right margin to ur and dr
        frame.ix[0].lon += mgn[1]
        frame.ix[1].lon += mgn[1]
        
        # add down margin to dr and dl
        frame.ix[1].lat -= mgn[2]
        frame.ix[2].lat -= mgn[2]
        
        # add left margin to dl and ul
        frame.ix[2].lon -= mgn[3]
        frame.ix[3].lon -= mgn[3]
    
    # return
    return frame


def dfToArray(DataFrame):
    """
    the DataFrame column 'geometry' will be converted to numpy.array
    
    @todo: include checks for data type, geometry type
    @todo: inlcude output options
    """
    import numpy as np
    
    return np.asarray([[item.GetPoint()[0], item.GetPoint()[1]] for item in DataFrame.geometry])

    
def ArrayToPolygon(Array):
    """
    A OGR POLYGON Geometry is build from the given np.ndarray.
    """
    import numpy as np
    from osgeo import ogr
    
    # check datatype
    if not isinstance(Array, np.ndarray):
        try:
            Array = np.asanyarray(Array)
        except:
            raise TypeError("Array is not of type numpy.ndarray and cannot be casted.\n Type: {0}".format(Array.__class__))

# TODO: handle passed lists    
#    # check dimensions
#    if Array.ndim == 2:
#        Array = np.array(Array)
#    if Array.ndim != 3:
#        raise TypeError("Array hast to be of 2 or 3 dimensions, found {0}.".format(Array.ndim))
    
    # mindfuck
    strings = []
    # create point string in WKT style
    for obj in Array:
        strings.append(','.join(["{0} {1}".format(x[0], x[1]) for x in obj]))
            
    # create OGR POLYGON Geometry objects
    polys = [ogr.CreateGeometryFromWkt("POLYGON (({0}))".format(x)) for x in strings]
    
    if len(polys) == 1:
        return polys[0]
    else:
        return polys


#### FROM HERE ON, ANYTHING WILL BE DELETED AT PUBLISHING ####
#### THIS WAS DEVELOPMENT ONLY ####
def rect_grid(edges, nrows=None, ncols=None, len_x=None, len_y=None, as_geometry=True, as_midpoints=False):
    """
    An rectengular grid of 4-point polygons is created within the 4 given 
    edge points. You can either give the cell length on x (len_x) and y (len_y), 
    or the number of cells to be created on each axis. For lengths, the same 
    unit as edge points will be used. You can also mix, give number of cells 
    for one axis and a specific cell length for the other one.
    edges can be given as pandas.DataFrame holding 'ur', 'dr', 'dl', 'ul' 
    indexed points, a list or array of 'ur', 'dr', 'dl', 'ul'.
    if nrows and len_y or ncols and len_x is given, len_x and len_y will be 
    used over nrows and ncols. If both are not given, 10 cells will be created 
    along the missing axis.
    
    @depracted
    """
    from pandas import DataFrame
    import numpy as np
	
	### Get Edge Points ###
    # convert edges to pandas.DataFrame
    if edges.__class__ != DataFrame().__class__:
        edges = DataFrame(data=edges, index=['ur', 'dr', 'dl', 'ul'], columns=['lon', 'lat'])
    
    # get frame lengths
    up = edges['lon']['ur'] - edges['lon']['ul']
    right = edges['lat']['ur'] - edges['lat']['dr']
    
    
    ### Calculate nrows, ncols, len_y, len_x ###
    if nrows is not None:
        if nrows.__class__ not in [int, float]:
            raise ValueError("""nrows hast to be of type int or float, found: {0}""".format(nrows.__class__))
        # compute len_y
        len_y = right / nrows
    else:
        # nrows is not given, len_y has to be given
        if len_y is None:
            raise AttributeError("""Either nrows, or len_y has to be specified. Both are None""")
        else:
            # len_y is given
            if len_y.__class__ not in [int, float]:
                raise ValueError("""len_y hast to be of type int or float, found: {0}""".format(len_y.__class__))
            # calculate nrows and recalculate len_y if nrows does not result as int
            nrows = int(round(right / len_y))
            len_y = right / nrows				# now right / len_y is nrows and int
            
    
    if ncols is not None:
        if ncols.__class__ not in [int, float]:
            raise ValueError("""ncols hast to be of type int or float, found: {0}""".format(ncols.__class__))
        # compute len_x
        len_x = up / ncols
    else:
        #ncols is not given, len_x has to be given
        if len_x is None:
            raise AttributeError("""Either ncols, or len_x has to be specified. Both are None""")
        else:
            # len_x is given
            if len_x.__class__ not in [int, float]:
                raise ValueError("""len_x hast to be of type int or float, found: {0}""".format(len_x.__class__))
            # calculate ncols and recalculate len_x if ncols does not result as int
            ncols = int(round(up / len_x))
            len_x = up / ncols				# now up / len_x is ncols and int
    
    
    ### create grid ###

    # zero point for grid is dl
    zero = (edges['lon']['dl'], edges['lat']['dl'])
    
    # check if numpy arrays or ogr geometries shall be returned:
    if not as_geometry:
        # usage of numpy arrays, either giving polgon midpoint or edge points
        # iterate through all rows and columns, with i,j as indices
        if not as_midpoints:
            ### Create Grid Polygons ###
            #grid = np.array([])    # numpy array as container for the resulting polygons
            grid = np.ndarray((ncols * nrows,5,2))
            #grid = []
            
            for j in range(nrows):
                for i in range(ncols):
                    # create dl, dr, ur, ul, dl as polygon
                    poly = np.array([
                                    [zero[0] + i * len_x, zero[1] + j * len_y],
                                    [zero[0] + (i + 1) * len_x, zero[1] + j * len_y],
                                    [zero[0] + (i + 1) * len_x, zero[1] + (j + 1) * len_y],
                                    [zero[0] + i * len_x, zero[1] + (j + 1) * len_y],
                                    [zero[0] + i * len_x, zero[1] + j * len_y]
                                    ])
                    # append poly to grid
                    #grid = np.append(grid, poly)
                    # the actual cell as created by iteration
                    grid[(j * ncols + i),] = poly
                    #grid.append(poly)
    
                    
        else:
            ### Create Grid Midpoints ###
            grid = np.ndarray((ncols * nrows, 2))
            # create midpoints
            for j in range(nrows):
                for i in range(ncols):
                    # create midpoint
                    point = [zero[0] + i * len_x + 0.5 * len_x, 
                             zero[1] + j * len_y + 0.5 * len_y]
                    #grid.append(point)
                    grid[(j * ncols + i), ] = point

    else:
        ### Create OGR Geometry Polygons ###
        # load library
        from osgeo import ogr
        
        # create container
        #grid = np.ndarray(ncols * nrows)
        grid = []
        
        # go for all polygon edge points
        for j in range(nrows):
            for i in range(ncols):
                if not as_midpoints:
                    ### Create Grid Polygons ###
                    # create dl, dr, ur, ul, dl as polygon
                    wkt = "POLYGON (({0} {1}, {2} {3}, {4} {5}, {6} {7}, {8} {9}))".format(
                        zero[0] + i * len_x, zero[1] + j * len_y,
                        zero[0] + (i + 1) * len_x, zero[1] + j * len_y,
                        zero[0] + (i + 1) * len_x, zero[1] + (j + 1) * len_y,
                        zero[0] + i * len_x, zero[1] + (j + 1) * len_y,
                        zero[0] + i * len_x, zero[1] + j * len_y
                    )
                else:
                    ### Create Grid Midpoints ###
                    wkt = "POINT ({0} {1})".format(
                        zero[0] + i * len_x + 0.5 * len_x,
                        zero[1] + j * len_y + 0.5 * len_y
                    )
                
                # create and append the OGR geometry
                #grid[j * ncols + i] = ogr.CreateGeometryFromWkt(wkt)
                grid.append(ogr.CreateGeometryFromWkt(wkt))
        
                
    
    ### Return ###
    return grid


def rect_midpoint(rect, as_geometry=False):
    """
    Retruns the geometric midpoint of an given rectangle. The rectangle has to 
    be given as numpy.ndarray of lists containg x and y for the dl, dr, up, ul 
    and dl edge points. 
    The midpoint is returned as tuple or OGR geometry.
    
    @depracted
    """
    import numpy as np
    
    # check rect type
    if rect.__class__ != np.ndarray([]).__class__ and rect.__class__ != list:
        raise TypeError("Rectangle has to be given as numpy.array or list, got {0}.".format(rect.__class__))
        
    # get the neccessary points
    dl = rect[0]
    dr = rect[1]
    ul = rect[3]
    
    # x-axis midpoint
    x = dl[0] + ((dr[0] - dl[0]) / 2)
    # y-axis midpoint
    y = dl[1] + ((ul[1] - dl[1]) / 2)
    
    if as_geometry:
        from osgeo import ogr
        return ogr.CreateGeometryFromWkt("POINT ({0} {1})".format(x,y))
    else:
        # return as tuple
        return (x, y)


def geodesic_distance(x, y, ref_x=None, ref_y=None, unit='m'):
    """
    The geodesic distance (on the earth surface) is computed using the 
    haversine function. If ref_x and/or ref_y are None, EPSG:4326 is assumed, 
    otherwise x and y will be transformed to EPSG:4326. Distance is returned in 
    [m], other possible values for unit are 'mi' for miles or 'ft' for 'feet'. 
    The default unit is kilometers if unit is anything else than 'm', 'mi' or 'ft'.
    """
    from osgeo import ogr, osr
    import numpy as np
    
    # check classes of x and y
    # if neccessary transform to OGR point geometry
    # x
    if x.__class__ != ogr.Geometry().__class__:
        try:
            x = ogr.CreateGeometryFromWkt("POINT ({0} {1})".format(x[0], x[1]))
        except:
            raise TypeError("x has to be of type tuple or OGR Geometry, found {0}.".format(x.__class__))
    # y
    if y.__class__ != ogr.Geometry().__class__:
        try:
            y = ogr.CreateGeometryFromWkt("POINT ({0} {1})".format(y[0], y[1]))
        except:
            raise TypeError("x has to be of type tuple or OGR Geometry, found {0}.".format(y.__class__))
    
    ### now, both points are OGR Geometries ###
    
    # check references
    # create target reference system
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    
    ### transform objects ###
    if ref_x is not None:
        if ref_x.__class__ == osr.SpatialReference().__class__:
            transform_x = osr.CoordinateTransformation(ref_x, target)
            x.Transform(transform_x)
        else:
            raise TypeError('ref_x has to be a valid OSR spatial reference, found type {0}.'.format(ref_x.__class__))

    if ref_y is not None:
        if ref_y.__class__ == osr.SpatialReference().__class__:
            transform_y = osr.CoordinateTransformation(ref_y, target)
            y.Transform(transform_y)
        else:
            raise TypeError('ref_y has to be a valid OSR spatial reference, found type {0}.'.format(ref_y.__class__))
                
    ### now, both points are in EPSG:4326 coordinate system ###
    # calculate the distance by using Haversine formula
    # z is not used here, but served by .GetPoint()
    x_lat, x_lon, z = x.GetPoint()
    y_lat, y_lon, z = y.GetPoint()
    
    # get the difference in radians
    dlon = np.radians(np.abs(y_lon - x_lon))
    dlat = np.radians(np.abs(y_lat - x_lat))
    
    # convert all degrees to radians
    x_lat = np.radians(x_lat)    
    y_lat = np.radians(y_lat)    
    x_lon = np.radians(x_lon)    
    y_lon = np.radians(y_lon)  
    
    # haversine
    a = np.power(np.sin(dlat / 2), 2) + np.cos(x_lat) * np.cos(y_lat) * np.power(np.sin(dlon / 2), 2)
    c = 2 * np.arcsin(np.min([1, np.sqrt(a)]))
    
    # get the earth radius
    R = 6371   
    #hier den genauen in abhängigkeit von lat ausrechenen und alles testen    
    
    d = R * c
    
    # return distance in [m]
    if unit == 'm':
        return d * 1000
    elif unit == 'mi':
        return d * 0.621371192
    elif unit == 'ft':
        return d * 3280.8399
    else:
        # return km
        return d
    


def ogrPointToTuple(point):
    """
    The OGR Geometry is parsed by its JSON representation and checked for beeing 
    a POINT Geometry. On success the coordinates are returned as tuple.
    """
    from osgeo import ogr
    import json
    
    if point.__class__ != ogr.Geometry().__class__:
        raise TypeError("The given point has to be an OGR Geometry, found {0}.".format(point.__class__))
    
    # parse point
    jpoint = json.loads(point.ExportToJson())
    
    # check geometry
    if jpoint['type'] != "Point":
        raise TypeError("The given Geometry is {0} but Point is needed".format(jpoint['type']))
    
    # no errors found: export coordinates
    return tuple(jpoint['coordinates'])
