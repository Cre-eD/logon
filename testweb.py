import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
import datetime
import argparse
import os
import sys
from lxml import etree
from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view
from py2neo import Graph, Node, Relationship

def to_lxml(record_xml):
    rep_xml = record_xml.replace("xmlns=\"http://schemas.microsoft.com/win/2004/08/events/event\"", "")
    rep_xml = rep_xml.replace("xmlns=\"Event_NS\"", "")
    set_xml = "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\" ?>%s" % rep_xml
    fin_xml = set_xml.encode("utf-8")

    parser = etree.XMLParser(resolve_entities=False)
    return etree.fromstring(fin_xml, parser)


def xml_records(filename):
    with Evtx(filename) as evtx:
        for xml, record in evtx_file_xml_view(evtx.get_file_header()):
            try:
                yield to_lxml(xml), None
            except etree.XMLSyntaxError as e:
                yield xml, e

def parse_evtx(evtx_list):
    NEO4J_USER = 'neo4j'

    NEO4J_PASSWORD = 'password'

    NEO4J_SERVER = '127.0.0.1'

    WEB_PORT = '8080'

    NEO4J_PORT = "7474"

    graph_http = "http://" + NEO4J_USER + ":" + NEO4J_PASSWORD + "@" + NEO4J_SERVER + ":" + NEO4J_PORT + "/db/data/"
    GRAPH = Graph(graph_http)
    tx = GRAPH.begin()
    GRAPH.run("MATCH (n) DETACH DELETE n")
    for evtx_file in evtx_list:
        for node, err in xml_records(evtx_file):
            event_data = node.xpath("/Event/EventData/Data")
            event_id = int(node.xpath("/Event/System/EventID")[0].text)
            username = '-'
            sesid = '-'
            srcip = '-'
            logontype = '-'
            if event_id in [21, 22, 23, 24, 25, 39, 40, 1149, 4624, 4625, 4647, 4778, 4779]:
                
                logtime = node.xpath("/Event/System/TimeCreated")[0].get("SystemTime")
                logtime = datetime.datetime.strptime(logtime.split(".")[0], "%Y-%m-%d %H:%M:%S")
               
                if event_id in [21, 22, 24, 25]:
                    if int(node.xpath("/Event/System/Task")[0].text) == 32:
                        pass
                    else:
                        try: 
                            username = node.xpath("/Event/UserData/EventXML/User")[0].text
                            username = username.split('\\')[-1]
                            username = username.lower()
                            sesid = str(node.xpath("/Event/UserData/EventXML/SessionID")[0].text)
                            srcip = str(node.xpath("/Event/UserData/EventXML/Address")[0].text)
                            event_id = str(event_id)
                            tmstmp = int(datetime.datetime.timestamp(logtime))
                            logtime = str(logtime)
                            tmstmp = str(tmstmp)
                            node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                            GRAPH.create(node)
                        except:
                            print('something goes wrong in 21')
                            print('')

                elif event_id == 23:
                    try: 
                        #username = str(node.xpath("/Event/UserData/EventXML/User")[0].text)
                        username = node.xpath("/Event/UserData/EventXML/User")[0].text
                        username = username.split('\\')[-1]
                        username = username.lower()
                        sesid = str(node.xpath("/Event/UserData/EventXML/SessionID")[0].text)
                        event_id = str(event_id)
                        tmstmp = int(datetime.datetime.timestamp(logtime))
                        logtime = str(logtime)
                        tmstmp = str(tmstmp)
                        node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                        GRAPH.create(node)
                    except:
                        print('something goes wrong in 23')
                        print('')

                elif event_id == 1149:
                    try:
                        #userfqdn = str(node.xpath("/Event/UserData/EventXML/Param2")[0].text)+'\\'+str(node.xpath("/Event/UserData/EventXML/Param1")[0].text)
                        username = str(node.xpath("/Event/UserData/EventXML/Param1")[0].text)
                        username = username.lower()
                        srcip = str(node.xpath("/Event/UserData/EventXML/Param3")[0].text)
                        event_id = str(event_id)
                        tmstmp = int(datetime.datetime.timestamp(logtime))
                        logtime = str(logtime)
                        tmstmp = str(tmstmp)
                        node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                        GRAPH.create(node)
                    except:
                         print('something goes wrong in 1149')
                         print('')
    
                elif event_id in [4624, 4625]:
                    try: 
                        for data in event_data:
                            if data.get("Name") in "LogonType" and data.text in ['7', '10']:
                                logontype = data.text.split(".")[0]
                                for data in event_data:
                                    if data.get("Name") in "TargetUserName" and data.text is not None:
                                        username = data.text.split("@")[0]
                                        if username[-1:] not in "$":
                                            username = username.lower()
                                            for data in event_data:
                                                if data.get("Name") in "LogonGuid" and data.text not in ["{00000000-0000-0000-0000-000000000000}"]:
                                                    #for data in event_data:
                                                       #if data.get("Name") in "TargetDomainName" and data.text is not None:
                                                        # domain = data.text.split(".")[0]
                                                    event_id = str(event_id)
                                                    tmstmp = int(datetime.datetime.timestamp(logtime))
                                                    logtime = str(logtime)
                                                    tmstmp = str(tmstmp)
                                                    node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                                                    GRAPH.create(node)
                                                else:
                                                    pass
                                        else:
                                            pass
                                    else:
                                        pass
                            else:
                                pass
                    except:
                        print('something goes wrong in 4624')
                        print('')

                elif event_id == 4647:
                    try: 
                        for data in event_data:
                             if data.get("Name") in "TargetUserName" and data.text is not None:
                                username = data.text.split("@")[0]
                                if username[-1:] not in "$":
                                    username = username.lower()
                                    for data in event_data:
                                       if data.get("Name") in "TargetDomainName" and data.text is not None:
                                         domain = data.text.split(".")[0]
                                    event_id = str(event_id)
                                    tmstmp = int(datetime.datetime.timestamp(logtime))
                                    logtime = str(logtime)
                                    tmstmp = str(tmstmp)
                                    node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                                    GRAPH.create(node)
                                else:
                                    pass
                    except:
                        print('something goes wrong in 4624')
                        print('')

                elif event_id in [4778, 4779]:
                    try: 
                        for data in event_data:
                             if data.get("Name") in "AccountName" and data.text is not None:
                                username = data.text.split("@")[0]
                                if username[-1:] not in "$":
                                    username = username.lower()
                                    for data in event_data:
                                       if data.get("Name") in "AccountDomain" and data.text is not None:
                                         domain = data.text.split(".")[0]
                                    event_id = str(event_id)
                                    tmstmp = int(datetime.datetime.timestamp(logtime))
                                    logtime = str(logtime)
                                    tmstmp = str(tmstmp)
                                    node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                                    GRAPH.create(node)
                                else:
                                    pass
                    except:
                        print('something goes wrong in 4778')
                        print('')

                elif event_id == 39:
                    try:
                        sesid = str(node.xpath("/Event/UserData/EventXML/TargetSession")[0].text)
                        event_id = str(event_id)
                        tmstmp = int(datetime.datetime.timestamp(logtime))
                        logtime = str(logtime)
                        tmstmp = str(tmstmp)
                        node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                        GRAPH.create(node)
                    except:
                        print('something goes wrong in 39')
                        print('')

                elif event_id == 40:
                    try:
                        sesid = str(node.xpath("/Event/UserData/EventXML/Session")[0].text)
                        event_id = str(event_id)
                        tmstmp = int(datetime.datetime.timestamp(logtime))
                        logtime = str(logtime)
                        tmstmp = str(tmstmp)
                        node = Node('Event', id = event_id, time = logtime, timestmp = tmstmp, user = username, srcaddress = srcip, session = sesid, logontp = logontype)
                        GRAPH.create(node)
                    except:
                        print('something goes wrong in 40')
                        print('')
                
                #tx.process()
                #tx.commit()
            else:
                pass


def fillbd():
    for root, dirs, files in os.walk("./uploads"): 
        evtxfiles = []
        for filename in files:
            evtxfiles.append('./uploads/'+filename)
    for evtx_file in evtxfiles:
        if not os.path.isfile(evtx_file):
            sys.exit("[!] Can't open file {0}.".format(evtx_file))
    parse_evtx(evtxfiles)
    for evtx_file in evtxfiles:
        os.remove(evtx_file)

def crgraph():
    NEO4J_USER = 'neo4j'

    NEO4J_PASSWORD = 'password'

    NEO4J_SERVER = '127.0.0.1'

    WEB_PORT = '8080'

    NEO4J_PORT = "7474"

    graph_http = "http://" + NEO4J_USER + ":" + NEO4J_PASSWORD + "@" + NEO4J_SERVER + ":" + NEO4J_PORT + "/db/data/"
    GRAPH = Graph(graph_http)

    #Search for logon and reconnect

    rxlistln = GRAPH.run('match (Event) where Event.id = \'1149\' return Event').data()

    for nd in rxlistln:
        ev1149 = nd.get('Event')
        timestmp = int(ev1149['timestmp'])
        time = str(ev1149['time'])
        srcip = str(ev1149['srcaddress'])
        starttime = str(timestmp)
        endtime = str(timestmp+20)
        user = ev1149['user']
        checkrel = GRAPH.run("match (Event) where  Event.id in ['21', '22'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
        #print (checkrel)
        if checkrel != []:
            timestmp = str(timestmp)
            nd1 = GRAPH.run("MATCH (Event {id: '1149', timestmp: '"+timestmp+"', user: '"+user+"'}) return Event").data()
            nd2 = GRAPH.run("MATCH (Event) where  Event.id in ['4624'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            nd3 = GRAPH.run("MATCH (Event) where  Event.id in ['21'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            nd4 = GRAPH.run("MATCH (Event) where  Event.id in ['22'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            #for nnd1 in nd1:
            n1 = ev1149
            for nnd3 in nd3:
                n3 = nnd3.get('Event')
                sesid = str(n3['session'])
            for nnd4 in nd4:
                n4 = nnd4.get('Event')
            for nnd2 in nd2:
                n2 = nnd2.get('Event')
                n1_n2 = Relationship(n1, 'logon', n2)
                GRAPH.create(n1_n2)
                n2_n3 = Relationship(n2, 'logon', n3)
                GRAPH.create(n2_n3)
            n3_n4 = Relationship(n3, 'logon', n4)
            GRAPH.create(n3_n4)
            logev = Node('Logon', ev_name = 'Successful logon', loged_user = user, logon_time = time, src_adress = srcip, session_id = sesid)
            n4_logev = Relationship(n4, 'logon', logev)
            GRAPH.create(n4_logev)

        else:
            pass #print("this is not new logon")
        checkrelrc = GRAPH.run("match (Event) where  Event.id in ['4778'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
        if checkrelrc != []:
            timestmp = str(timestmp)
            #nd1 = GRAPH.run("MATCH (Event {id: '1149', timestmp: '"+timestmp+"', user: '"+user+"'}) return Event").data()
            n1 = ev1149
            nd2 = GRAPH.run("MATCH (Event) where  Event.id in ['4624'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            nd3 = GRAPH.run("MATCH (Event) where  Event.id in ['25'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            for nnd3 in nd3:
                n3 = nnd3.get('Event')
                sesid = str(n3['session'])
            nd4 = GRAPH.run("MATCH (Event) where  Event.id in ['40'] and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' and Event.session = '"+sesid+"' return Event").data()

            nd5 = GRAPH.run("MATCH (Event) where  Event.id in ['4778'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            for nnd5 in nd5:
                n5 = nnd5.get('Event') 
            for nnd2 in nd2:
                n2 = nnd2.get('Event')
                n1_n2 = Relationship(n1, 'reconnect', n2)
                GRAPH.create(n1_n2)
                n2_n3 = Relationship(n2, 'reconnect', n3)
                GRAPH.create(n2_n3)
            for nnd4 in nd4:
                n4 = nnd4.get('Event')
                n3_n4 = Relationship(n3, 'reconnect', n4)
                GRAPH.create(n3_n4)
                n4_n5 = Relationship(n4, 'reconnect', n5)
                GRAPH.create(n4_n5)
            logev = Node('Reconnect', ev_name = 'Successful reconnect', loged_user = user, logon_time = time, src_adress = srcip, session_id = sesid)
            n5_logev = Relationship(n5, 'reconnect', logev)
            GRAPH.create(n5_logev)
     
        else:
            pass
        nd1 = 0
        nd2 = 0
        nd3 = 0
        nd4 = 0
        nd5 = 0
        n1 = 0
        n2 = 0
        n3 = 0
        n4 = 0
        n5 = 0
    #Search for logoff
    rxlistlf = GRAPH.run('match (Event) where Event.id = \'24\' return Event').data()

    for nd in rxlistlf:
        ev24 = nd.get('Event')
        timestmp = int(ev24['timestmp'])
        time = str(ev24['time'])
        srcip = str(ev24['srcaddress'])
        starttime = str(timestmp-10)
        endtime = str(timestmp+10)
        user = ev24['user']
        sesid = ev24['session']
        check39 = GRAPH.run("match (Event) where  Event.id in ['39'] and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' and Event.session = '"+sesid+"' return Event").data()
        check23 = GRAPH.run("match (Event) where  Event.id in ['23'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
        if check39 != []:
            n4 = ev24
            nd2 = check39
            nd3 = GRAPH.run("MATCH (Event) where  Event.id in ['40'] and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' and Event.session = '"+sesid+"' return Event").data()
            nd4 = GRAPH.run("MATCH (Event) where  Event.id in ['4779'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            if nd3 !=[] and nd4 != []:
                for nnd2 in nd2:
                    n3 = nnd2.get('Event')
                for nnd3 in nd3:
                    n2 = nnd3.get('Event')
                for nnd4 in nd4:
                    n1 = nnd4.get('Event')
                n1_n2 = Relationship(n1, 'disconnect', n2)
                GRAPH.create(n1_n2)
                n2_n3 = Relationship(n2, 'disconnect', n3)
                GRAPH.create(n2_n3)
                n3_n4 = Relationship(n3, 'disconnect', n4)
                GRAPH.create(n3_n4)
                logev = Node('Disconnect', ev_name = 'Successful disconnect', loged_user = user, logon_time = time, src_adress = srcip, session_id = sesid)
                n4_logev = Relationship(n4, 'disconnect', logev)
                GRAPH.create(n4_logev)
            else:
                pass
        elif check23 != []:
            n4 = ev24
            nd3 = check23
            nd2 = GRAPH.run("match (Event) where  Event.id in ['4647'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            nd4 = GRAPH.run("MATCH (Event) where  Event.id in ['40'] and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' and Event.session = '"+sesid+"' return Event").data()
            if nd2 !=[] and nd4 != []:
                for nnd2 in nd2:
                    n1 = nnd2.get('Event')
                for nnd3 in nd3:
                    n2 = nnd3.get('Event')
                for nnd4 in nd4:
                    n3 = nnd4.get('Event')
                n1_n2 = Relationship(n1, 'logoff', n2)
                GRAPH.create(n1_n2)
                n2_n3 = Relationship(n2, 'logoff', n3)
                GRAPH.create(n2_n3)
                n3_n4 = Relationship(n3, 'logoff', n4)
                GRAPH.create(n3_n4)
                logev = Node('Logoff', ev_name = 'Successful Logoff', loged_user = user, logon_time = time, src_adress = srcip, session_id = sesid)
                n4_logev = Relationship(n4, 'logoff', logev)
                GRAPH.create(n4_logev)
            else:
                pass
        else:
            n3 = ev24
            nd2 = GRAPH.run("MATCH (Event) where  Event.id in ['40'] and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' and Event.session = '"+sesid+"' return Event").data()
            nd3 = GRAPH.run("MATCH (Event) where  Event.id in ['4779'] and Event.user = '"+user+"' and Event.timestmp >= '"+starttime+"' and Event.timestmp <= '"+endtime+"' return Event").data()
            if nd3 !=[] and nd2 != []:
                for nnd2 in nd2:
                    n2 = nnd2.get('Event')
                for nnd3 in nd3:
                    n1 = nnd3.get('Event')
                n1_n2 = Relationship(n1, 'disconnect', n2)
                GRAPH.create(n1_n2)
                n2_n3 = Relationship(n2, 'disconnect', n3)
                GRAPH.create(n2_n3)
                logev = Node('Disconnect', ev_name = 'Successful disconnect by window close', loged_user = user, logon_time = time, src_adress = srcip, session_id = sesid)
                n3_logev = Relationship(n3, 'disconnect', logev)
                GRAPH.create(n3_logev)
            else:
                pass
        nd1 = 0
        nd2 = 0
        nd3 = 0
        nd4 = 0
        nd5 = 0
        n1 = 0
        n2 = 0
        n3 = 0
        n4 = 0
        n5 = 0

# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['evtx'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html')


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            filenames.append(filename)
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
    # Load an html page with a link to each uploaded file
    return render_template('upload.html', filenames=filenames)

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/parse', methods=['GET'])
def upload1():
    fillbd()
    crgraph()
    return render_template('graph.html')

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8888"),
        debug=True
)
    url_for('static', filename='neovis.js')