
import MOTS


# Test make path to config files instead of path to single config file 
print "Starting MOTS"  
application = MOTS.moWSGITileServer("/home/graber/mapossum/qidmaps")


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    from werkzeug.debug import DebuggedApplication
    app = DebuggedApplication(application, evalex=True)
    run_simple("0.0.0.0", 8080, app) 
