from flask import Flask
from flask import request
from flask import send_file
import psycopg2
import psycopg2.extras
import json
import multiprocessing
import base64, zipfile, sys
import cStringIO
import os.path
import random
import Image, ImageDraw, ImageFont
import cStringIO
import math
import sched, time
import datetime

dbcs = 'host=data.mapossum.org dbname=postgis user=postgres password=Geo5051'

maptypedic = {"subs":"states_prov", "counties":"counties","countries":"countries", "points": "", "watercolor": ""}
from flask.ext.cors import CORS

def getcallback(req):
    callback = req.args.get(']callback')
    if (callback == None):
        callback = request.args.get('callback')
    try:
        callback = callback.strip('/')
        return callback
    except:
        return "" 

def getvalue(req,key,default = None):
    try:
        if request.method == 'POST':
            tval = request.form[key]
        else:    
            tval = req.args.get(key)
            if (tval[-3:] == '/[?'):
                tval = tval[:-3]
    except:
        tval = default
    if (tval == None):
        raise Exception('No Default Specified', 'No value Found')
    #tval = tval.strip('/[?')
    return tval	

def wrapcallback(callback,outputdata):
    if (callback == ""):
     return json.dumps(outputdata)
    else:
         return callback + "(" + json.dumps(outputdata) + ")"  


application = Flask(__name__)
application.config['CORS_ALLOW_HEADERS'] = "Content-Type"
CORS(application)

@application.route("/")
def hello():
    f = open('/home/graber/mapossum/methods.html', 'r')
    m = f.read()
    return m
    
@application.route("/verify", methods=['GET', 'POST'])
def verify():
    callback = getcallback(request)
    try:
        username = getvalue(request,'email')
        password = getvalue(request,'password')
    except:
        return wrapcallback(callback,{"success":False, "message":"email and password all required inputs"})

    conn = psycopg2.connect(dbcs)
    #cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select last, first, userid, affiliation, username as email, ST_AsText(ST_Transform(location,4326)) as location from users where username = '" + username + "' and password = '" + password + "';")
    outq = cur.fetchone()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"email":"", "userid": -1, "message": "user not found"})
    
    return wrapcallback(callback,outq)

@application.route("/adduser", methods=['GET', 'POST'])
def adduser():
    callback = getcallback(request)
    try:
        email = getvalue(request,'email')
        password = getvalue(request,'password')
        affiliation = getvalue(request,'affiliation')
    #title = getvalue(request,'title')
        first = getvalue(request,'first')
        last = getvalue(request,'last')
        location = getvalue(request,'location', 'Point(-98.579404 39.828127)')
        if (location == ""):
             location = 'Point(-98.579404 39.828127)'
    except:
        return wrapcallback(callback,{"success":False, "message":"email (text), password(text), affiliation (text), first (text), last (text) and location (WKT in LAT LON - 4326) are all required inputs"})
    
    conn = psycopg2.connect(dbcs)
    #cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO users (first, last, affiliation, username, password, lastlogin, location) VALUES ('" + first + "', '" + last + "', '" + affiliation + "', '" + email + "', '" + password + "',  current_timestamp, ST_Transform(ST_SetSrid(ST_GeomFromText('" + location + "'), 4326),3857)) RETURNING last, first, userid, affiliation, username as email, ST_AsText(ST_Transform(location,4326)) as location;")
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,outq)

@application.route("/updateuser", methods=['GET', 'POST'])
def updateuser():
    callback = getcallback(request)
    try:
        email = getvalue(request,'email')
        password = getvalue(request,'password')
        affiliation = getvalue(request,'affiliation')
    #title = getvalue(request,'title')
        first = getvalue(request,'first')
        last = getvalue(request,'last')
        location = getvalue(request,'location')
        userid = getvalue(request,'userid')
    except:
        return wrapcallback(callback,{"success":False, "message":"userid, email (text), password(text), affiliation (text), first (text), last (text) and location (WKT in LAT LON - 4326) are all required inputs"})
    
    conn = psycopg2.connect(dbcs)
    #cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("UPDATE users set (first, last, affiliation, username, password, lastlogin, location) = ('" + first + "', '" + last + "', '" + affiliation + "', '" + email + "', '" + password + "',  current_timestamp, ST_Transform(ST_SetSrid(ST_GeomFromText('" + location + "'), 4326),3857)) where userid = " + userid + " RETURNING last, first, userid, affiliation, username as email, ST_AsText(ST_Transform(location,4326)) as location;")
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,outq)
    
    
@application.route("/addquestion", methods=['GET', 'POST'])
def addquestion():
    callback = getcallback(request)
    try:
        userid = getvalue(request,'userid')
        question = getvalue(request,'question')
        qtype = getvalue(request,'type', 'multiple')
        hashtag = getvalue(request, 'hashtag', '')
        explain = getvalue(request, 'explain', '')
    except:
        return wrapcallback(callback,{"success":False, "message":"userid, question (text) are all required inputs"})

    
    conn = psycopg2.connect(dbcs)
    #cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO questions (userid, question, type, hashtag, explain) VALUES (" + userid + ", '" + question + "', '" + qtype + "', '" + hashtag + "', '" + explain + "') RETURNING userid, question, type, hashtag, qid, explain;")
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,outq)
    
defaultColors = ['rgb(31,120,180)','rgb(51,160,44)','rgb(227,26,28)','rgb(255,127,0)','rgb(106,61,154)','rgb(177,89,40)','rgb(166,206,227)','rgb(178,223,138)','rgb(251,154,153)','rgb(253,191,111)','rgb(202,178,214)','rgb(255,255,153)']

def findcolor(qid, methods=['GET', 'POST']):
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select answerid from answers where qid = " + qid)
    outs = cur.fetchall()
    cur.close()
    conn.close()
    if (len(outs) < 13):
        outcolor = defaultColors[len(outs)]
    else:
        r = lambda: random.randint(0,255)
        outcolor = ('#%02X%02X%02X' % (r(),r(),r()))
    return outcolor
	

@application.route("/addanswer", methods=['GET', 'POST'])
def addanswer():
    callback = getcallback(request)
    try:
        qid = getvalue(request,'qid')
        answer = getvalue(request,'answer')

    except:
        return wrapcallback(callback,{"success":False, "message":"qid (Question ID) and answer are all required inputs"})

    link = color = getvalue(request,'link', "")
    color = getvalue(request,'color', "")
    #if (color == "-1"):
    #     color = findcolor(qid)
    
    
    conn = psycopg2.connect(dbcs)
    #cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO answers (qid, answer, color, link) VALUES (" + qid + ", '" + answer + "', '" + color + "', '" + link + "') RETURNING qid, answer, answerid, color, link")
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if (color == ""):
         setdefaultcolors(qid)
    
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,outq)


def findresponse(qid,answerid, methods=['GET', 'POST']):
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select * from answers where qid = " + qid + " and answerid = " + answerid)
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return ""
    return outq["answer"]
      
    
@application.route("/addresponse", methods=['GET', 'POST'])
def addresponse():
    callback = getcallback(request)
    try:
        qid = getvalue(request,'qid')
        answerid = getvalue(request,'answerid', "-1")
        uresponse = getvalue(request,'response', "")
        location = getvalue(request,'location')
        
    except:
        return wrapcallback(callback,{"success":False, "message":"qid and location are all required inputs, answerid and/or response are required"})
    
    if (uresponse == ""):
        uresponse = findresponse(qid,answerid)
    
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO responses (qid, answerid, response, location, locationwm) VALUES (" + qid + ", " + answerid + ", '" + uresponse + "', " + " ST_SetSrid(ST_GeomFromText('" + location + "'), 4326)" + ", ST_Transform(ST_SetSrid(ST_GeomFromText('" + location + "'), 4326),3857)) RETURNING qid, answerid, response, ST_AsText(ST_Transform(location,4326)) as location;")
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,outq)
    
@application.route("/getanswers", methods=['GET', 'POST'])
def getanswers():
    callback = getcallback(request)
    try:
        qid = getvalue(request,'qid')
        
    except:
        return wrapcallback(callback,{"success":False, "message":"qid is required"})
   
    
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    #cur.execute("select * from answers where qid = " + qid)
    cur.execute("select * from (select * from answers where qid = " + qid + ") as a full join (select response, count(response) from responses where qid = " + qid + " group by response, answerid) as b on a.answer = b.response")
    outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outdata = {}
    outdata['success'] = True
    outdata['data'] = outq
    return wrapcallback(callback,outdata)
    
    
@application.route("/getquestions", methods=['GET', 'POST'])
def getquestions():
    callback = getcallback(request)
    try:
        count = getvalue(request,'count', "10")
        minutes = getvalue(request,'minutes', "2000000000")
        
        
    except:
        return wrapcallback(callback,{"success":False, "message":" is required"})
   
    logic = getvalue(request,'logic', "or")
    ha = getvalue(request,'hasanswers', "false")
    qids = getvalue(request,'qids', "")
    
    users = getvalue(request,'users', "")
    
    
    mins = long(minutes)
    if (mins > 2000000000):
         minutes = "2000000000"
    
    if (ha == "true"):
         ending = ' join (select count(qid), qid from answers group by qid) b on a.qid = b.qid'
    else:
         ending = ''
    
    if (qids != ""):
        qids = " " + logic + " qid in (" + qids + ")"
        
    if (users != ""):
        users = " " + logic + " userid in (" + users + ")"
     
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select * from (select userid, question, type, hashtag, qid, COALESCE(explain, '') as explain, to_char(created, 'YYYY-MM-DD HH24:MI:SS') as created from questions where (created > now() - interval '" + minutes + " minute' "+ qids + users + ")) a " + ending + " order by created DESC limit " + count + ";")
    outq = cur.fetchall()

#    if (qids != ""):
#         qidvals = qids.split(",")
#         for qid in qidvals:
#              print "select * from (select userid, question, type, hashtag, qid, to_char(created, 'YYYY-MM-DD HH24:MI:SS') as created from questions where created > now() - interval '" + minutes + " minute') a " + ending + " where qid = " + qid + ";"
#              cur.execute("select * from (select userid, question, type, hashtag, qid, to_char(created, 'YYYY-MM-DD HH24:MI:SS') as created from questions where qid = " + qid + ") a " + ending + " where a.qid = " + qid + ";")
#              outq2 = cur.fetchone()
#              if (outq2):
#                   outq.insert(0,outq2)
    
    conn.commit()
    cur.close()
    conn.close()
    
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outdata = {}
    outdata['success'] = True
    outdata['data'] = outq
    return wrapcallback(callback,outdata)

@application.route("/getextent/<qid>", methods=['GET', 'POST'])
@application.route("/getextent/<qid>/<maptype>", methods=['GET', 'POST'])
def getextent(qid,maptype = "points"):
    callback = getcallback(request)

    tablename = maptypedic[maptype]
    
    if (tablename == ""):
         SQLu = "SELECT ST_Extent(location) as extent FROM responses where qid = " + qid
    else:
         SQLu = "select Box2D(ST_transform(st_setSRID(ST_Extent( st_intersection(shape,st_transform(ST_SetSRID(ST_MakeBox2D(ST_Point(-170, -60), ST_Point(170, 60)),4326),3857)) ),3857),4326)) as extent from " + tablename + " join (select st_setSRID(st_extent(locationwm),3857) as res from responses where qid = " + qid + ") as allres on st_intersects(shape, allres.res)"
    
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute(SQLu)
    outq = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if (outq["extent"] == None):
        outq["extent"] = "BOX(-170 -60,170 70)"
    outs = outq["extent"].strip("BOX(").strip(")")
    out2 = outs.split(",")
    if (len(out2) == 1):
         out2 = [outs,outs]
 
    
    finalout = []
    for out in out2:
         finalout.append(map(float, out.split(" "))[::-1])
    
    if (outq == None):
         return wrapcallback(callback,{"success":False})
    outq['success'] = True
    return wrapcallback(callback,finalout)
    
    
@application.route("/setupmaps" , methods=['GET', 'POST'])
def setupmaps():
    callback = getcallback(request)
    try:
        qid = getvalue(request,'qid')
    except:
        return wrapcallback(callback,{"success":False, "qid":" is required"})
     
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select * from answers where qid = " + qid + ";")
    outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    
    directory = "/home/graber/mapossum/qidmaps/" + qid
    
    if (len(outq) > 0):
    
         f = open('/home/graber/mapossum/qidmaps/template.cfg', 'r')
         m = f.read()
         f.close()
         m = m.replace("%%qid%%", qid)
         
         f = open('/home/graber/mapossum/qidmaps/' + qid + '.cfg', 'w')
         f.write(m)
         f.close()
         
         if not os.path.exists(directory):
              os.makedirs(directory)

         f = open('/home/graber/mapossum/qidmaps/markers/markertemplate.xml', 'r')
         mt = f.read()
         f.close()
            
         symbolstring = '<Style name="responsesSYM" filter-mode="first" >\n'
         psymbolstring = symbolstring
         msymbolstring = symbolstring
         for sym in outq:
              im = drawp(sym["color"])
              imageloc = "/home/graber/mapossum/qidmaps/markers/" + sym["color"] + ".png"
              im.save(imageloc)
              cmt = mt.replace("%%responsetext%%", sym["answer"]).replace("%%responsecolor%%", imageloc)
              msymbolstring = msymbolstring + cmt
              symbolstring = symbolstring + "  <Rule>\n"
              psymbolstring = psymbolstring + "  <Rule>\n"
              symbolstring = symbolstring + "    <Filter>([response] = '" + sym["answer"] + "')</Filter>\n"
              psymbolstring = psymbolstring + "    <Filter>([response] = '" + sym["answer"] + "')</Filter>\n"
              symbolstring = symbolstring + '    <PolygonSymbolizer fill="' + sym["color"] +'" />\n'
              psymbolstring = psymbolstring + '    <MarkersSymbolizer fill="' + sym["color"] +'" width="8" height="8" />\n'  
              symbolstring = symbolstring + "  </Rule>\n" 
              psymbolstring = psymbolstring + "  </Rule>\n"  
         symbolstring = symbolstring + '</Style>\n' 
         psymbolstring = psymbolstring + '</Style>\n'
         msymbolstring = msymbolstring + '</Style>\n' 
         
         maptypes = []              
         for file in os.listdir("/home/graber/mapossum/qidmaps/templates"):
              if (file[0:2] != "._"):
                   print file
                   f = open('/home/graber/mapossum/qidmaps/templates/' + file, 'r')
                   m = f.read()
                   f.close()
                   m = m.replace("%%markersymbol%%", psymbolstring)
                   m = m.replace("%%symbol%%", symbolstring)
                   m = m.replace("%%wmarkersymbol%%", msymbolstring)
                   m = m.replace("%%qid%%", qid)
         
                   f = open('/home/graber/mapossum/qidmaps/' + qid + "/" + file, 'w')
                   f.write(m)
                   f.close()
                   
                   maptypes.append(file.replace(".xml",""))
            
                          
    else:
         return wrapcallback(callback,{"success":False, message:"currently only multiple choice questions with answers are supported"})
    if (outq == None):
         return wrapcallback(callback,{"success":False}) 

    outdata = {}
    outdata['success'] = True
    outdata['data'] = outq
    outdata['maps'] = maptypes
    
    outdata['baseurl'] = "http://maps.mapossum.org/" + qid
    
    return wrapcallback(callback,outdata)

@application.route("/identify/<qid>/<maptype>", methods=['GET', 'POST'])
def identify(qid,maptype):
    callback = getcallback(request)
    try:
        point = getvalue(request,'point')
    except:
        return wrapcallback(callback,{"success":False, "message":"point is required"})
        
        
    buffer = getvalue(request,'buffer', "1")
    
    tablename = maptypedic[maptype]
    
    if (tablename == ""):
         middlepart = "(select * from (select st_buffer(st_transform(st_geomfromtext('" + point + "',4326),3857)," + buffer + ") as shape, 'buffer of clicked point'::name) as poo) as roi"
    else:
         middlepart = "(select * from " + tablename + " where st_intersects(shape,st_buffer(st_transform(st_geomfromtext('" + point + "',4326),3857)," + buffer + "))) as roi"
    
    firstpart = "select * from (select * from answers where qid = " + qid + ") as a join (select response, count(response), foo.name from (select * from (select * from (select response, answerid, locationwm from responses where qid = " + qid + ") as res join "
    lastpart = " on res.locationwm && roi.shape) as pointsin) as foo group by response, foo.name) as b on a.answer = b.response order by name, answer;"
    
    outsql = firstpart + middlepart + lastpart
    #print outsql
    
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    #cur.execute("select * from answers where qid = " + qid)
    cur.execute(outsql)
    outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    
    if (outq == None):
         return wrapcallback(callback,{"success":False})

    outdata = {}
    outdata['success'] = True
    outdata['data'] = outq
    
    return wrapcallback(callback,outdata)  
    
	
@application.route("/legend/<qid>", methods=['GET', 'POST'])
def legend(qid):
    callback = getcallback(request)
    
    bgcolor = getvalue(request,'bgcolor', "white")
    color = getvalue(request,'color', "black")
    opacity = getvalue(request,'opacity', "1")
    
    trans = int(255.0 * (float(opacity)))
    
    if (bgcolor[0:4] == "rgb("):
        bgcolor = eval(bgcolor[3:])
        bgcolor = rgb_to_hex(bgcolor)
        
    if (color[0:4] == "rgb("):
        color = eval(color[3:])
        color = rgb_to_hex(color)

    qid = qid.replace(".png","")
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    #cur.execute("select * from answers where qid = " + qid)
    cur.execute("select * from answers where qid = " + qid)
    outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    font = ImageFont.truetype("/home/graber/mapossum/fonts/trebuchet.ttf", 35)
    im = Image.new("RGBA", (2,2), "white")
    draw = ImageDraw.Draw(im)
	
    c = len(outq)	
    maxl = 0
    for q in outq:
        cz = draw.textsize(q['answer'] , font=font)
        if (cz[0] > maxl):
           maxl = cz[0]
    #print maxl
		
    img = Image.new("RGBA", (maxl + 90, (c * 50) + 10), bgcolor)
    
    pixdata = img.load()
    
    for y in xrange(img.size[1]):
    	for x in xrange(img.size[0]):
             if pixdata[x, y][3] == 255:
                  pixdata[x, y] = (pixdata[x, y][0],pixdata[x, y][1],pixdata[x, y][2],trans)

    draw = ImageDraw.Draw(img)

	
    cc = 0
    for q in outq:
        #print q["color"], q['answer']
        miny = (cc * 50) + 10
        draw.rectangle((10,miny,70,miny + 40), fill=q["color"])
        draw.text((82,miny + 0),  q['answer'], fill=color, font=font)
        cc = cc + 1
		
    #return wrapcallback(callback,outdata)

    return serve_pil_image(img)
		
def serve_pil_image(pil_img):
    img_io = cStringIO.StringIO()
    pil_img.save(img_io, 'PNG', quality=90)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
    

@application.route("/defaultcolors/<qid>", methods=['GET', 'POST'])
def defaultcolors(qid):
    callback = getcallback(request)
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("update answers as an set color = c.color from (select * from (select row_number() over (PARTITION by qid order by answerid) as id, qid, answer, answerid from answers order by qid, answerid) as a join colors as b on a.id = b.id) as c where an.answerid = c.answerid and an.qid = " + qid + ";")
    #outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    #if (outq == None):
    #     return wrapcallback(callback,{"success":False})
    outdata = {}
    outdata['success'] = True
    outdata['message'] = "colors returned to default" 
    return wrapcallback(callback,outdata)  
 
def setdefaultcolors(qid):
  
    conn = psycopg2.connect(dbcs)
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("update answers as an set color = c.color from (select * from (select row_number() over (PARTITION by qid order by answerid) as id, qid, answer, answerid from answers order by qid, answerid) as a join colors as b on a.id = b.id) as c where an.answerid = c.answerid and an.qid = " + qid + " and an.color = ''")
    #outq = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    #if (outq == None):
    #     return wrapcallback(callback,{"success":False})
    outdata = {}
    outdata['success'] = True
    outdata['message'] = "colors returned to default"   


@application.route("/drawpoint/<color>")
def drawpoint(color):
    dc = "#" + color.replace(".png","")
    im = drawp(dc)
    return serve_pil_image(im)

    
def drawp(color):
    if (color[0:3] == "rgb"):
        color = eval(color[3:])
        color = rgb_to_hex(color)

    img = Image.new("RGBA", (51, 51), color)
    gradient = Image.new('L', (51,51))
    for x in range(0,50):
        for y in range(0,50):
             dfc = math.sqrt((25-x) * (25-x) + (25-y) * (25-y))
             NewValue = 150 - ((((dfc - 0) * (150 - 0)) / (25 - 0)) + 0)
             gradient.putpixel((x,y),NewValue)
    img.putalpha(gradient)
    return img


def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb


scheduler = sched.scheduler(time.time, time.sleep)

def refreshSite(name):
    print 'EVENT:', midnightSecs(), name
    scheduler.enter(20, 1, refreshSite, ('first',))
    scheduler.run()
    
def midnightSecs():
    tomorrow = datetime.date.today() + datetime.timedelta(1)
    midnight = datetime.datetime.combine(tomorrow, datetime.time())
    now = datetime.datetime.now()
    return (midnight - now).seconds

#refreshSite("test")

@application.route("/pl/<lat>/<lon>")
def pl(lat,lon):
    callback = getcallback(request)
    gm = GlobalMercator()
    
    mc = gm.LatLonToMeters(float(lat),float(lon))
    print mc
    tc = gm.MetersToTile(mc[0], mc[1], 2)
    print tc
    gc = gm.GoogleTile(tc[0],tc[1], 2)
    
    return wrapcallback(callback,{"tile":gc})   


class GlobalMercator(object):

    def __init__(self, tileSize=256):
        "Initialize the TMS Global Mercator pyramid"
        self.tileSize = tileSize
        self.initialResolution = 2 * math.pi * 6378137 / self.tileSize
        # 156543.03392804062 for tileSize 256 pixels
        self.originShift = 2 * math.pi * 6378137 / 2.0
        # 20037508.342789244

    def LatLonToMeters(self, lat, lon ):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        mx = lon * self.originShift / 180.0
        my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)

        my = my * self.originShift / 180.0
        return mx, my

    def MetersToLatLon(self, mx, my ):
        "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

        lon = (mx / self.originShift) * 180.0
        lat = (my / self.originShift) * 180.0

        lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
        return lat, lon

    def PixelsToMeters(self, px, py, zoom):
        "Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

        res = self.Resolution( zoom )
        mx = px * res - self.originShift
        my = py * res - self.originShift
        return mx, my

    def MetersToPixels(self, mx, my, zoom):
        "Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"

        res = self.Resolution( zoom )
        px = (mx + self.originShift) / res
        py = (my + self.originShift) / res
        return px, py

    def PixelsToTile(self, px, py):
        "Returns a tile covering region in given pixel coordinates"

        tx = int( math.ceil( px / float(self.tileSize) ) - 1 )
        ty = int( math.ceil( py / float(self.tileSize) ) - 1 )
        return tx, ty

    def PixelsToRaster(self, px, py, zoom):
        "Move the origin of pixel coordinates to top-left corner"

        mapSize = self.tileSize << zoom
        return px, mapSize - py

    def MetersToTile(self, mx, my, zoom):
        "Returns tile for given mercator coordinates"

        px, py = self.MetersToPixels( mx, my, zoom)
        return self.PixelsToTile( px, py)

    def TileBounds(self, tx, ty, zoom):
        "Returns bounds of the given tile in EPSG:900913 coordinates"

        minx, miny = self.PixelsToMeters( tx*self.tileSize, ty*self.tileSize, zoom )
        maxx, maxy = self.PixelsToMeters( (tx+1)*self.tileSize, (ty+1)*self.tileSize, zoom )
        return ( minx, miny, maxx, maxy )

    def TileLatLonBounds(self, tx, ty, zoom ):
        "Returns bounds of the given tile in latutude/longitude using WGS84 datum"

        bounds = self.TileBounds( tx, ty, zoom)
        minLat, minLon = self.MetersToLatLon(bounds[0], bounds[1])
        maxLat, maxLon = self.MetersToLatLon(bounds[2], bounds[3])

        return ( minLat, minLon, maxLat, maxLon )

    def Resolution(self, zoom ):
        "Resolution (meters/pixel) for given zoom level (measured at Equator)"

        # return (2 * math.pi * 6378137) / (self.tileSize * 2**zoom)
        return self.initialResolution / (2**zoom)

    def ZoomForPixelSize(self, pixelSize ):
        "Maximal scaledown zoom of the pyramid closest to the pixelSize."

        for i in range(30):
            if pixelSize > self.Resolution(i):
                return i-1 if i!=0 else 0 # We don't want to scale up

    def GoogleTile(self, tx, ty, zoom):
        "Converts TMS tile coordinates to Google Tile coordinates"

        # coordinate origin is moved from bottom-left to top-left corner of the extent
        return tx, (2**zoom - 1) - ty

    def QuadTree(self, tx, ty, zoom ):
        "Converts TMS tile coordinates to Microsoft QuadTree"

        quadKey = ""
        ty = (2**zoom - 1) - ty
        for i in range(zoom, 0, -1):
            digit = 0
            mask = 1 << (i-1)
            if (tx & mask) != 0:
                digit += 1
            if (ty & mask) != 0:
                digit += 2
            quadKey += str(digit)

        return quadKey
	
if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080, debug=True)
