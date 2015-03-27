# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:45:06 2015

@author: maelicke
"""
import os, shutil

def saveCluster(Cluster, path, xml=False, overwrite=False):
    """
    The given Cluster instance is saved to path. For each Cluster Dataframe, 
    a pickle is saved with attribute name as filename. The Spatial Reference is 
    saved as ref.txt containing a WKT. Im XML is True, reference is saved as 
    ref.xml in xml format.
    If overwrite is True, the given folder at path will RECURSIVLY deleted.
    Do only set this option to True, if you didn't check the path. Twice.
    @depracted
    @ will be converted to a file creating tarballs. files are created as file-like-objects
    """
    if os.path.exists(path):
        if overwrite:
            # remove folder recursivley
            shutil.rmtree(path)
        else:
            raise AttributeError("The folder {0} at {1} already exists.".format(os.path.basename(path), os.path.dirname(path)))
    
    # Create folder at path
    os.mkdir(path)
    
    ### Save all data ###
    # get all datasets with objects
    datasets = Cluster.getDatasets(True)
    
    for dataset in datasets:
        namepath = path + "/" + dataset + ".pickle"
        datasets[dataset].to_pickle(namepath)
    
    ### Save Spatial reference ###
    ref = Cluster.getSpatialReference()
    
    if xml:
        filepath = path + "/ref.xml"
        filecontent = ref.ExportToXML()
    else:
        filepath = path + "/ref.wkt"
        filecontent = ref.ExportToWkt()
    
    fs = open(filepath, "w")
    fs.write(filecontent)
    fs.close()
    
    
def ExportShp(Dataframe, SpatialReference, **kwargs):
    """
    """
    pass
