# -*- coding: utf-8 -*-
"""
Some fundamental function for settings and defaults for integrating mapsta 
openSource Arduino based GPS tracker and mapper (<http://gps.openhydro.org>) 
into LOCOMOTIF application (<http://locomotif.openhydro.org>).

@author: Mirko Maelicke <mirko@maelicke-online.de>
"""
__version__ = '0.1'
__author__ = 'Mirko Maelicke'

import json, bisect, os


def get_csv_options(version=100, module='mapsta'):
    """
    Import parameters for pandas.read_csv function are returned as dict.
    In the locomotif settings module a json file named mapsta_settings.json or 
    other module name instead of 'mapsta' is required. Then this module name, 
    without '_settings.json' shall be past as module. 
    The function will search all version informations in the file for the given 
    version or next smaller version. The saved parameters for this version is 
    returned as dictionary. The version number shall be given as at least 3-digit 
    integer, with major-minor-micro, eg.: 105 for 1.0.5 or 2400 for 24.0.0.
    """
    
    # check version type
    if version.__class__ != int:
        raise TypeError('version number has to be given as at least 3-digit integer, got %s.' % version.__class__)
        
    # get old working directory
    old_path = os.getcwd()
    
    # change path to file location
    os.chdir(os.path.dirname(__file__))
    
    options = json.loads(open('%s_settings.json' % module, 'r').read())
    
    # set old path again
    os.chdir(old_path)
    
    # get the version numbers
    versions = [int(x) for x in options.keys()]
    versions.sort()
    
    # get latest version parameters
    params = options['%d' % (versions[bisect.bisect(versions, version) - 1])]
    
    # return as dict or keywords
    return params
    
