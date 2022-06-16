#!/usr/local/bin/python3

#
# Get state of Dyntrace agents and processes needing restart
#

import json
import requests
from datetime import datetime
from pprint import pprint
import math
import os

#
# Globals
#
URL_BASE="https://kel38879.live.dynatrace.com/api"
TOKEN=os.environ['DT_TOKEN']
domain = "mgmt.hh.atg.se"
G =  1024*1024*1024

headers = {'Content-Type': 'application/json',
           'Authorization': 'Api-Token %s' % TOKEN,
           'Accept': 'application/json; charset=utf-8'}

def get_hosts(rt=None):
    '''
    Get all hosts from DT
    '''
    url = "%s/v1/entity/infrastructure/hosts" % URL_BASE
    if rt:
        url = "%s?relativeTime=%s" % (url, rt)
    print("debug: get_hosts: url=%s" % url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = json.loads(response.content.decode('utf-8'))
    else:
        print("failed: %d" % response.status_code)
        exit(1)
    return res

def get_events(rt=None, cursor=None):
    '''
    Get all events from DT
    '''
    url = "%s/v1/events" % URL_BASE
    if cursor:
        url = "%s?cursor=%s" % (url, cursor)
    elif not rt:
        #rt = "day"
        rt = "week"
    if rt:
        url = "%s?relativeTime=%s" % (url, rt)
    print("debug: get_events: url=%s" % url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = json.loads(response.content.decode('utf-8'))
    else:
        print("failed: %d" % response.status_code)
        exit(1)
    return res

allprocs = {}
def get_all_proc():
    '''
    Get all processes DT
    '''
    url = "%s/v1/entity/infrastructure/processes" % (URL_BASE)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = json.loads(response.content.decode('utf-8'))
    else:
        #print("failed: %d" % response.status_code)
        #exit(1)
        res = None
    for p in res:
        allprocs[p['entityId']] = p
    return res

def get_proc(pgi):
    '''
    Get a process (from cache loaded in get_all_proc above)
    '''
    if pgi in allprocs:
        return allprocs[pgi]
    else:
        return None

def out_row(v):
    print(", ".join(v))

def dt_get_outdated_procs():
    #
    # Get hosts and procs
    #
    hosts = get_hosts()
    get_all_proc()

    h = ["Hostname","Host OneAgent version","Process","Process OneAgent versions",
        "Is monitored","Can monitor", "Need restart"]
    vout = []
    vout.append(h)

    # Check versions of agents and which processes needs restart
    for host in hosts:
        if 'agentVersion' in host:
            ver = host['agentVersion']
        else:
            ver = {'major':0, 'minor':0, 'revision':0}
        hname = host['displayName']
        v = (ver['major'], ver['minor'], ver['revision'])
        if hname.find(',') != -1:
            print("comma in hostname: ", hname)
            exit(1)
        if 'toRelationships' not in host:
            continue
        if 'isProcessOf' not in host['toRelationships']:
            continue
        for pgi in host['toRelationships']['isProcessOf']:
            proc = get_proc(pgi)
            if proc == None:
                continue
            restartReq = proc['monitoringState']['restartRequired']
            if restartReq:
            #if True:
                pname = proc['displayName']
                isMonitored = (proc['monitoringState']['actualMonitoringState'] == "ON")
                canMonitor = (proc['monitoringState']['expectedMonitoringState'] == "ON")
                p_agent_ver = ""
                if 'agentVersions' in proc:
                    avs = proc['agentVersions']
                    f = True
                    for av in avs:
                        if not f:
                            p_agent_ver += ";"
                        f = False
                        p_agent_ver += "%d.%d.%d.%s" % (av['major'],av['minor'],
                            av['revision'],av['timestamp'])
                if pname.find(',') != -1:
                    print("command in process name: ", pname)
                    exit(1)
                a = [hname, "%d.%d.%d" % v, pname, p_agent_ver, 
                    str(isMonitored), str(canMonitor), str(restartReq)]
                vout.append(a)
    return vout

def dt_get_host_units():
    #
    # Get used hosts units
    #
    hosts = get_hosts()
    hosts2 = get_hosts("5mins")
    
    h = ["Hostname","Host OneAgent version","First Seen","Last Seen","Host Units","Current Used Host Units"]
    vout = []
    vout.append(h)
    totalUsed = 0.0
    currentUsed = 0.0

    h5min = dict()
    for host in hosts2:
        id = host['entityId']
        h5min[id] = 1

    # Check versions of agents and which processes needs restart
    for host in hosts:
        if 'agentVersion' in host:
            ver = host['agentVersion']
        else:
            ver = {'major':0, 'minor':0, 'revision':0}
        id = host['entityId']
        lseen = ""
        if 'lastSeenTimestamp' in host:
            t = host['lastSeenTimestamp']/1000
            lseen = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
        fseen = ""
        if 'firstSeenTimestamp' in host:
            t = host['firstSeenTimestamp']/1000
            fseen = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
        hname = host['displayName']
        hunits = host['consumedHostUnits']
        if hunits != None:
            hunits = float(hunits)
        else:
            hunits = 0.0
        totalUsed += hunits
        if id in h5min:
            cunits = hunits
        else:
            cunits = 0.0
        currentUsed += cunits
        if hname.find(',') != -1:
            print("comma in hostname: ", hname)
            exit(1)
        v = (ver['major'], ver['minor'], ver['revision'])
        a = [hname, "%d.%d.%d" % v, fseen, lseen, str(hunits), str(cunits)]
        vout.append(a)
    a = ["Total", "", "", "", str(totalUsed), str(currentUsed)]
    vout.append(a)
    return vout

def v(ev, f):
    if f in ev:
        return str(ev[f])
    return ""

def dt_get_events():
    #
    # Get events
    #
    """
    {
  "nextEventStartTms": 1582101191249,
  "nextEventId": -5289211181293908000,
  "nextCursor": "AgEAAAFwWDJdGAEAAAFwXVi5GAAAAQAcMTcwNWM5NDVhNTEtYjY5OGYyNzQzY2YzZDE0OQ==",
  "from": 1582027660568,
  "to": 1582114060568,
  "totalEventCount": 1885,
  "events": [
    {
      "eventId": -5223837172936983000,
      "startTime": 1582113480000,
      "endTime": -1,
      "entityId": "SERVICE-6D2D80E9386C8F6B",
      "entityName": "RMI requests on SpeltjanstDomain",
      "severityLevel": "ERROR",
      "impactLevel": "SERVICE",
      "eventType": "FAILURE_RATE_INCREASED",
      "eventStatus": "OPEN",
      "tags": [
        {
          "context": "CONTEXTLESS",
          "key": "Tillsammans"
        }
      ],
      "id": "-5223837172936982929_1582113480000",
      "affectedRequestsPerMinute": 165.2132,
      "service": "RMI requests on SpeltjanstDomain",
      "source": "builtin",
      "serviceMethodGroup": "se.atg.service.ejb.vi75.EJBVi75KupongBean_xi0o3k_EJBVi75KupongRemoteImpl"
    },
    {'endTime': 1582118260000,
 'entityId': 'PROCESS_GROUP_INSTANCE-4C8DEE2796C33CF8',
 'entityName': 'MonitoringHost.exe',
 'eventId': 8276943567184864959,
 'eventStatus': 'CLOSED',
 'eventType': 'PROCESS_RESTART',
 'id': '8276943567184864959_1582118250000',
 'impactLevel': 'INFRASTRUCTURE',
 'source': 'builtin',
 'startTime': 1582118250000,
 'tags': []}
    """

    h = ["Event ID", "Start time", "End time", 
        "Entity ID", "Entity name", "Event type",
        "Severity", "Impact", "Status",
        "Affected req/min", "Service",
        "Source"]
    vout = []
    vout.append(h)

    c = None
    done = False
    while not done:
        res = get_events(cursor=c)
        if res:
            events = res['events']
        else:
            return vout

        if events == None or len(events) == 0:
            return vout

        print("debug: got %d events" % len(events))

        for ev in events:
            #pprint(ev)
            t = ev['startTime']/1000
            tfrom = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
            t = ev['endTime']/1000
            tto = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
            a = [str(ev['eventId']), tfrom, tto, 
                str(ev['entityId']), v(ev,'entityName'), ev['eventType'],
                v(ev,'severityLevel'), ev['impactLevel'], ev['eventStatus'],
                v(ev,'affectedRequestsPerMinute'), v(ev,'service'),
                ev['source']]
            vout.append(a)

        if 'nextCursor' in res:
            c = res['nextCursor']

        if c == None:
            done = True

    return vout


#########


ocp_hosts_all = [ "vlpocpie01",
    "vlpocpie02",
    "vlpocpie03",
    "vlpocpie04",
    "vlpocpin01",
    "vlpocpin02",
    "vlpocpin03",
    "vlpocpin04",
    "vlpocpma01",
    "vlpocpma02",
    "vlpocpma03",
    "vlpocpwn01",
    "vlpocpwn02",
    "vlpocpwn03",
    "vlpocpwn04",
    "vlpocpwn05",
    "vlpocpwn06",
    "vlpocpwn07",
    "vlpocpwn08",
    "vlpocpwn09",
    "vlpocpwn10",
    "vlpocpwn11",
    "vlpocpwn12",
    "plpocpwn01",
    "plpocpwn02",
    "plpocpwn03",
    "plpocpwn04",
    "plpocpwn05",
    "plpocpwn06",
]

ocp_hosts = [ 
    "plpocpwn01",
    "plpocpwn02",
    "plpocpwn03",
    "plpocpwn04",
    "plpocpwn05",
    "plpocpwn06",
]

#ocp_hosts = [ 
#    "plpocpwn01",
#]


def get_metrics(selector, entity):
    url = "%s/v2/metrics/series/%s?scope=entity(%s)&resolution=h&from=now-1y" % (URL_BASE, selector, entity)
    #print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = json.loads(response.content.decode('utf-8'))
    else:
        print("failed: %d" % response.status_code)
        print(response)
        return None
    return res

def get_data(selector, entity, host, host_data, metric_time):
    d = get_metrics(selector, entity)
    if d == None:
        return None
    if 'metrics' not in d:
        return None
    if len(d['metrics'][selector]['series']) < 1:
        return None
    v1 = None
    host_data[host] = dict()

    for e in d['metrics'][selector]['series'][0]['values']:
        val = e['value']
        if val != None:
            t = int(e['timestamp'])
            if metric_time['first'] == 0 or t < metric_time['first']:
                metric_time['first'] = t
            if t > metric_time['last']:
                metric_time['last'] = t
            host_data[host][t] = int(val)
            v1 = val
    return v1


def dt_ocp_mem_usage():
    usum = 0
    tsum = 0
    host_data = dict(dict())
    host_hdata = dict()
    metric_time = { 'first' : 0, 'last' : 0 }

    #startt = '2019-01-01 00:00'
    #tfrom = datetime.datetime.strptime(startt, '%Y-%m-%d %H:%M').timestamp()
    #tto = datetime.datetime.now().timestamp()-24*60*60

    for host in ocp_hosts:
        fhost = "%s.%s" % (host,domain)
        used = get_data("builtin:host.mem.used", fhost, host, host_data, metric_time)
        if used == None:
            print(host, "failed to read data for host")
            continue

    for host in ocp_hosts:
        t = metric_time['first']
        d = host_data[host]
        hd = []
        while t <= metric_time['last']:
            if t in d:
                hd.append(d[t])
            else:
                hd.append(0)
            t += 3600*1000;
        host_hdata[host] = hd
        cnt = len(hd)

    res = []
    h = [ "time" ]
    h += ocp_hosts
    h += ocp_hosts
    h += [ "max", "sum", "max%%", "avg%%", "active", "above10", "flag" ]
    res.append(h)
    msz = 768*G
    tsz = msz * len(ocp_hosts)
    i = 0
    t = metric_time['first'] / 1000
    while i < cnt:
        max = 0
        sum = 0
        above10 = 0
        active = 0
        vals = [ datetime.fromtimestamp(t) ]
        for host in ocp_hosts:
            v = host_hdata[host][i]
            if v > max:
                max = v
            sum += v
            if v > 0:
                active += 1
            vals.append(v)
        for host in ocp_hosts:
            v = host_hdata[host][i]
            vp = math.ceil(100*v/msz)
            if vp > 10:
                above10 += 1
            vals.append(vp)
        vals.append(max)
        vals.append(sum)
        maxp = math.ceil(100*max/msz)
        tp = math.ceil(100*sum/tsz)
        fl = 0
        if maxp > 10:
            fl += 1
        if tp > 10:
            fl += 2
        vals.append(maxp)
        vals.append(tp)
        vals.append(active)
        vals.append(above10)
        vals.append(fl)
        svals = map(str, vals)
        res.append(svals)
        i += 1
        t += 3600

    return res

        
        