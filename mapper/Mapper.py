# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 10:23:58 2015

@author: maelicke
"""
import os
import pandas as pd
from datetime import datetime as dt
from lxml import etree
try:
    import mapnik
except:
    raise ImportError("The module mapnik has to be present for mapping data.")

class Mapper(object):
    """
    """
    def __init__(self, Style=None, size=(1024, 768), datasource=None, out_path=None, **kwargs):
        """
        
        Style is the filename without path and .xml located in the styles 
        folder containing a valid mapnik Style definition in XML format.
        If this file cannot be found, Style will be interpreted as regular path
        including the .xml MIME.
        As datasource, a pandas.DataFrame containing OGR geometries or an 
        absolute file path to a Shapefile can be given.
        """
        # check file size attribute
        if not isinstance(size, tuple) or not len(size) == 2:
            raise AttributeError("Map size has to be given as tuple of width, height.\nFound {0} on length {1}".format(size.__class__), len(size))
        else:
            self.canvas = mapnik.Map(size[0], size[1])
        
        # check if a datasource was given
        # if yes load the datasource using style_path to self.canvas
        if datasource is not None:
            # if style was None, this will load the Default Style to the map
            styles = self.load_style(Style)
            # add a layer for the given datasource
            self.add_layer(self.canvas, styles=styles, datasource=self.load_datasource(datasource), inplace=True)
        
        # check if a zoom box was given as kwargs
        if 'zoom_box' in kwargs:
            zoom_box = kwargs['zoom_box']
        else:
            zoom_box = None
            
        # if out path was given, render the map
        if out_path is not None:
            self.render(self.canvas, out_path, zoom_box)
            
        
    
    def load_datasource(self, datasource, **kwargs):
        """
        """
        # check datasource class
        if isinstance(datasource, str):
            if datasource.endswith('.shp'):
                # this is a filepath for a Shapefile
                return mapnik.Shapefile(file=datasource)
            # elif TODO: more options here, like csv, 
            else:
                raise AttributeError("The string '{0}', was not understood.\nIt has to be a filepath to an ESRI Shapefile.")
        elif isinstance(datasource, pd.DataFrame):
            # the pandas dataframe needs a column called geometry, which will be used
            # check if a geometry=fff was passed, identifying the geometry column
            if 'geometry' in kwargs:
                geometry = kwargs['geometry']
            else:
                geometry = 'geometry'
                
            if not geometry in datasource.columns:
                raise AttributeError("The given pandas.DataFrame does not have a geometry column called '{0}'.".format(geometry))
            
            # create a memory datasource
            out = mapnik.MemoryDatasource()
            # context for the features
            context = mapnik.Context()
            # add all columns not beeing a geometry column
            [context.push(str(item)) for item in datasource.columns if not item == geometry]
            
            for i, item in datasource.iterrows():
                # i is index, item is the pandas row object
                feature = mapnik.Feature(context, int(i))
                
                # add geometry
                feature.add_geometries_from_wkt(datasource[geometry].ix[i].ExportToWkt())
                
                for col in datasource.columns:
                    if not col == geometry:
                        # numpy dtype conversion
                        val = datasource[str(col)].ix[i]
                        try:
                            val = val.item()
                        except:
                            pass
                        feature[str(col)] = val
                
                # append feature to datasource
                out.add_feature(feature)
            
            #return datasource
            return out
                
            
            
    def load_style(self, Style=None):
        """
        """
        # check if Style is None, then use Default style
        if Style is None:
            Style = "Default"
            
        # build the path
        style_path = "{0}/styles/{1}.xml".format(os.path.dirname(__file__), Style)
        
        if not os.path.exists(style_path):
            if os.path.exists(Style):
                style_path = Style
            else:
                raise AttributeError("The attribute Style either has to identify a predifend style in the styles folder or contain a absolute path to a mapnik style XML file.\nStyle content: '{0}'".format(Style))
        
        # style path is valid, load style definitions to self.canvas
        mapnik.load_map(self.canvas, style_path)
        
        # return the names of all loaded styles
        try:
            values = etree.parse(style_path).find('Style').values()
        except AttributeError:
            # No <Style> objects found in XML file --> use empty list
            values = []
        return values
                

    
    def add_layer(self, canvas, styles, datasource, inplace=False):
        """
        The datasource has to be loaded and the Map builded. Then for any field
        in the datasource which has its own Style (name attribute is the same as
        the datasource field name) a layer will be included. All Styles prefixed
        by default_ or called Default will always be appended to the datasource.
        """
        # check availabe style names
        if isinstance(styles, str):
            styles = [styles]
        if not isinstance(styles, list):
            raise AttributeError("styles has to be list of all available styles, found {0}.".format(styles.__class__))
        
        # check if datasource is a mapnik Datasource
        if not isinstance(datasource, mapnik._mapnik.Datasource):
            raise AttributeError("The datasource has to be a loaded mapnik Datasource, found {0}.\n Use Mapper.load_datasource function or mapnik's loading functions to load such.".format(datasource.__class__))
            
        # load fields and styles
        fields = datasource.fields()
        
        # get all default styles
        def_styles = [style for style in styles if style.lower() == 'default' or style.lower().startswith('default_')]
        
        # create main layer and add all default styles
        layer = mapnik.Layer('Main')
        layer.datasource = datasource
        # add all styles
        for style in def_styles:
            layer.styles.append(style)
        
        # add layer to styles
        canvas.layers.append(layer)
        
        # add a layer for each field
        for field in fields:
            if field.lower() in styles:
                # create layer for this field
                layer = mapnik.Layer(field)
                layer.datasource = datasource
                # add specific style
                layer.styles.append(field)
                #add to map
                canvas.layers.append(layer)
        
        # if inplace, replace self.canvas, else return
        if inplace:
            self.canvas = canvas
        else:
            return canvas
                
                
    def render(self, canvas, out_path, zoom_box=None):
        """
        Renders the given mapnik.Map object to the given out_path.
        """
        if not isinstance(canvas, mapnik.Map):
            raise AttributeError("canvas has to be a mapnik.Map object, found {0}".format(canvas.__class__))
        
        if len(canvas.layers) == 0:
            raise AttributeError("Cannot render a map without a Layer.")
        
        # zoom map to the layer, if no zoom box is given
        if zoom_box is None:
            zoom_box = canvas.layers[0].envelope()
        elif isinstance(zoom_box, str):
            layer_list = [l.name for l in canvas.layers]
            if zoom_box in layer_list:
                zoom_box = [l for l in canvas.layers if l.name == zoom_box].pop().envelope()
            else:
                raise NameError("The Map does not have a layer '{0}'.\nAvailible layers: {1}".format(zoom_box, layer_list))
        
        # check zoom_box class
        if not isinstance(zoom_box, mapnik.Box2d):
            if isinstance(zoom_box, list):
                try:
                    zoom_box = mapnik.Box2d(*zoom_box)
                except:
                    raise AttributeError("zoom_box was given as list, but could not be converted to a mapnik.Box2d.")
            else:
                raise AttributeError("zoom_box can only be given as mapnik.Box2d or list containing the min/max edge values (4 values).")                
                            
        # zoom
        canvas.zoom_to_box(zoom_box)
        
        # check the file ending of out_map
        if out_path.lower().endswith('.png'):
            # render the map as png
            mapnik.render_to_file(canvas, out_path)
        elif out_path.lower().endswith('.jpg') or out_path.lower().endswith('jpeg'):
            # render the map as jpeg
            mapnik.render_to_file(canvas, out_path, 'jpeg')
        elif out_path.lower().endswith('.pdf'):
            # render the map as pdf
            mapnik.render_to_file(canvas, out_path, 'pdf')
        elif out_path.lower().endswith('.svc'):
            # render the map as SVG:
            mapnik.render_to_file(canvas, out_path, 'svc')
        elif out_path == '::memory::':
            # render the file to memory,
            # can be used like imageData = image.tostring('png')
            # with image returned
            image = mapnik.Image(canvas.width, canvas.height)
            mapnik.render(canvas, image)
            return image
        else:
            raise AttributeError("The file format '{0}' is not supported as output format.\n Use .png, .svc, .jpg, .pdf or ::memory::.".format(out_path.split('.')[1]))
        
        # if this is executed, all should be finde
        return True
        
        
        