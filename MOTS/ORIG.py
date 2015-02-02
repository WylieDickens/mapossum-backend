
from TileStache import *


class moWSGITileServer(WSGITileServer):

    #MOTS wants config directory instead of config file, override orginal __init__ to achive this purpose
    def __init__(self, configsLocation):
        #WSGITileServer.__init__(self, config, True)
        self.autoreload = True
        self.configsLocation = configsLocation
        self.config_path = None
        self.config = None

    #modify TileStache method to get name of config file from URL at every call (request)
    #config file must be in specified MOTS configsLocation (above)
    def __call__(self, environ, start_response):
    	path_info = environ.get('PATH_INFO', None)
    	paths = path_info.strip(r"/").split(r"/")
    	config_file = paths[0]
    	environ['PATH_INFO'] =  (r"/").join(paths[1:])
        config_path = self.configsLocation + r"/" + config_file +".cfg"
        self.config_path = config_path
        
        #from here on we can use inherited __call__
        return WSGITileServer.__call__(self, environ, start_response)
      
        

#test it
if __name__ == '__main__':

    # Test make path to config files instead of path to single config file   
    application = moWSGITileServer("/home/graber/TileStache")
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 8080, application)
    
    
 