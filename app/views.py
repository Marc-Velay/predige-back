from flask import Flask, render_template, flash, redirect, request, session
from uuid import uuid4
import requests
import requests.auth
import urllib
import base64
import os
import pandas as pd
import base64
import json, codecs
from datetime import datetime
from app import app
from .forms import LoginForm


## SET this only for local testing, if VCAPS is set env they will be overwritten by VCAPS.
CLIENT_ID = "dev" # "app_client_id"
UAA_URL= "https://marcv-dapep-flask.predix-uaa.run.aws-usw02-pr.ice.predix.io/" #"https://9c5f79c3-9760-47fc-b23f-0beba4525e10.predix-uaa.run.aws-usw02-pr.ice.predix.io"
BASE64ENCODING = "ZGV2OnRvdG8xMjM0" #'YXBwX2NsaWVudF9pZDpzZWNyZXQ='
port = int(os.getenv("PORT", 3000))
REDIRECT_URI = "http://localhost:3000/callback" #"http://localhost:"+str(port)+"/callback"

uaaUrl = "https://iiotquest-uaa-service.predix-uaa.run.aws-usw02-pr.ice.predix.io"
tsDataUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/datapoints"
tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/tags"
requestTags = "{\"tags\": [{\"name\": \"Compressor-2015:CompressionRatio\"}]}"
#requestData = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"asc\",      \"limit\": 1    }  ]}"
requestData = "{ \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",     }  ]}"
requestData_last = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"desc\",      \"limit\": 1    }  ]}"
requestData_first = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"asc\",      \"limit\": 1    }  ]}"
zoneId = "6138f224-a4d2-4329-8a10-5ffdc3d4ca9f"
tokents = base64.b64encode('timeseries_client_readonly:IM_SO_SECRET')

## Setting up Oauth2 , this values should be read from vcaps .
APP_URL= "http://localhost:3000/"
# Get UAA credentials from VCAPS
if 'VCAP_SERVICES' in os.environ:
    services = json.loads(os.getenv('VCAP_SERVICES'))
    uaa_env = services['predix-uaa'][0]['credentials']
    UAA_URL=uaa_env['uri']

# Get UAA credentials from VCAPS
if 'VCAP_APPLICATION' in os.environ:
    applications = json.loads(os.getenv('VCAP_APPLICATION'))
    app_details_uri = applications['application_uris'][0]
    APP_URL = 'https://'+app_details_uri
    REDIRECT_URI = APP_URL+'/callback'
else :
    APP_URL = "http://localhost:"+str(port)
    REDIRECT_URI = APP_URL+"/callback"

#Cloud env defined variable for services, see manifest file
#used for identification on services
if(os.getenv('client_id')):
    CLIENT_ID = os.getenv('client_id')

#Cloud env defined variable for services, see manifest file
#Used for authentification on services
if(os.getenv('base64encodedClientDetails')):
    BASE64ENCODING = os.getenv('base64encodedClientDetails')


@app.route('/')
def home():
    key = session.get('key', 'not set') #UAA session token
    if 'access_token' in session: # check if user has identified himself
        # TODO: call to Check_token to validate this token
        return redirect(APP_URL+"/index", code=302)
    else : #if not IDed, redirect to identification url
        return redirect(getUAAAuthorizationUrl(), code=302)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm() #fetch form from forms.py, which include objects and requirements for fields
    if form.validate_on_submit():   #What to do when submit button is clicked
        flash('Login requested for OpenID="%s", remember_me=%s' %
              (form.openid.data, str(form.remember_me.data)))
        return redirect('/index')
    return render_template('index/login.html', #get the login.html template to fill the base.html page
                           title='Sign In',     #Passing objects to web pages
                           form=form)

@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
     
    flights = set()
    firstPoint = doQueryTags(requestTags, tsUrl, uaaUrl, tokents, zoneId)
    for item in firstPoint["results"]:
        tmp,_ = item.split('.', 1)
        flights.add(tmp)
    
    return render_template('index/index.html',
                           title='Home',
                           flights=flights,
                           user=user, 
                           loginURL=getUAAAuthorizationUrl())

@app.route('/dashboard')
def dashboardpage():
    print 'dashboard'
    return render_template('index/dashboard.html',
                            title='Dashboard',
                            app_url=APP_URL)

@app.route('/flight', methods=['GET', 'POST'])
def flightspage():
    print 'flight'
    tags = set()
    flight = None
    tag = None
    flight = request.args.get('fly')
    tag = request.args.get('tag')
    firstPoint = doQueryTags(requestTags, tsUrl, uaaUrl, tokents, zoneId)
    for item in firstPoint["results"]:
        _,tmp = item.split('.', 1)
        tags.add(tmp)
        
    return render_template('index/flights.html',
                            title='Flight',
                            fp=tags,
                            flight=flight,
                            tag=tag)

@app.route('/flightData', methods=['GET','POST'])
def reqFlightData():
    tags = set()
    flight = None
    tag = None
    data = {}
    flight = request.args.get('fly')
    tag = request.args.get('tag')
    
    firstPoint = doQueryTags(requestTags, tsUrl, uaaUrl, tokents, zoneId)
    for item in firstPoint["results"]:
        _,tmp = item.split('.', 1)
        tags.add(tmp)

    requestDatafromTag_last = {"start": "50y-ago", "tags": [{"name": flight+"."+tag, "order": "desc", "limit": 1}]}
    requestDatafromTag_first = {"start": "50y-ago", "tags": [{"name": flight+"."+tag, "order": "asc", "limit": 1}]}

    
    firstPoint = doQuery(json.dumps(requestDatafromTag_first, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)
    if firstPoint.empty: 
        return json.dumps({'success':False, 'error':"No data associated to tag"}), 200, {'ContentType':'application/json'}
    startDate =  pd.Timestamp(firstPoint['timestamp'][0])
    startDate = int(startDate.strftime("%s")) * 1000
    startDateOrigin = startDate
    
    lastPoint = doQuery(json.dumps(requestDatafromTag_last, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)
    endDate =  pd.Timestamp(lastPoint['timestamp'][0])
    endDate = int(endDate.strftime("%s")) * 1000
    pdArray = []

    while (startDate < endDate ):
        payload = { 'cache_time':0, 'tags':[{'name': flight+"."+tag, 'order': 'asc'}], 'start': startDate, 'end': startDate + 10000000}
        startDate = startDate + 100000000
        series = doQuery(json.dumps(payload, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)
        pdArray.append(series)

    fullseries = pd.concat(pdArray)
    data = dict(vals = fullseries['values'], Date=fullseries['timestamp'])
    dataJson = json.dumps([{'Date': time, 'val': value} for time, value in zip(data['Date'], data['vals'])], default=json_serial)
    data = json.loads(dataJson)
    return json.dumps({'success':True, 'data':data}), 200, {'ContentType':'application/json'}


## Auth-code grant-type required UAA
@app.route('/callback')
def UAAcallback():
    print 'callback '
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        print 'Uh-oh, this request wasnt started by us!'
        #abort(403)
    code = request.args.get('code')
    access_token = get_token(code)
    # TODO: store the user token in sesson or redis cache , but for now use Flask session
    session['access_token'] = access_token
    print "You have logged in using UAA  with this access token %s" % access_token
    return redirect(APP_URL+"/", code=302)
   

@app.route('/test')
def test():
    
    firstPoint = doQuery(requestData_first, tsDataUrl, uaaUrl, tokents, zoneId)
    startDate =  pd.Timestamp(firstPoint['timestamp'][0])
    startDate = int(startDate.strftime("%s")) * 1000
    startDateOrigin = startDate
    
    lastPoint = doQuery(requestData_last, tsDataUrl, uaaUrl, tokents, zoneId)
    endDate =  pd.Timestamp(lastPoint['timestamp'][0])
    endDate = int(endDate.strftime("%s")) * 1000
    pdArray = []

    while (startDate < endDate ):
        payload = { 'cache_time': 0, 'tags': [{'name': 'Flight_13.Air_Density_ambient_kg_m', 'order': 'asc'}], 'start': startDate, 'end': startDate + 10000000}
        startDate = startDate + 100000000
        series = doQuery(json.dumps(payload, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)
        pdArray.append(series)

    fullseries = pd.concat(pdArray)
    data = dict(vals = fullseries['values'], Date=fullseries['timestamp'])
    #print(data)
    dataJson = json.dumps([{'Date': time, 'val': value} for time, value in zip(data['Date'], data['vals'])], default=json_serial)
    data = json.loads(dataJson)
    #print(dataJson)

    return render_template('index/test.html',
                           title='Testing in progress',
                           fp=data)


# method to consttruct Oauth authorization request
def getUAAAuthorizationUrl():
    state = 'secure'
    params = {"client_id": CLIENT_ID,
              "response_type": "code",
              "state": state,
              "redirect_uri": REDIRECT_URI
              }
    url = UAA_URL+"/oauth/authorize?" + urllib.urlencode(params)
    return url

# Oauth Call to get access_token based on code from UAA
def get_token(code):
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": REDIRECT_URI,
                 "state":"secure"}
    headers = base_headers()
    response = requests.post(UAA_URL+"/oauth/token",
                             headers=headers,
                             data=post_data)
    token_json = response.json()
    return token_json["access_token"]

#Adds authentification to the header
def base_headers():
    return {"Authorization": "Basic "+BASE64ENCODING }

#Was login successful? if yes secure
def is_valid_state(state):
    if(state == 'secure' ) :
        return True
    else :
        return False

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


#prepare querries for Time Series
def doQueryTags(payload, tsUrl, uaaUrl, tokents, zoneId):
    
    headers = {
        'authorization': 'Basic ' + tokents,
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id':'timeseries_client_readonly',
        'grant_type':'client_credentials'
    }
    
    response = requests.request('POST', uaaUrl+"/oauth/token", data=data, headers=headers)
    tokents = json.loads(response.text)['access_token']
    headers = {
        'authorization': "Bearer " + tokents,
        'predix-zone-id': "" + zoneId,
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    
    response = requests.request("GET", tsUrl, data=payload, headers=headers)
    data = json.loads(response.text)
    return data
  
#prepare querries for Time Series
def doQuery(payload, tsDataUrl, uaaUrl, tokents, zoneId):
    
    headers = {
        'authorization': 'Basic ' + tokents,
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id':'timeseries_client_readonly',
        'grant_type':'client_credentials'
    }
    
    response = requests.request('POST', uaaUrl+"/oauth/token", data=data, headers=headers)
    tokents = json.loads(response.text)['access_token']
    headers = {
        'authorization': "Bearer " + tokents,
        'predix-zone-id': "" + zoneId,
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    
    response = requests.request("POST", tsDataUrl, data=payload, headers=headers)
    data = json.loads(response.text)['tags'][0]['results'][0]['values']
    column_labels = ['timestamp', 'values', 'quality']
    series = pd.DataFrame(data, columns=column_labels)
    series['timestamp'] = pd.to_datetime(series['timestamp'], unit='ms')
    return series
    
def doQueryTwo(payload, tsDataUrl, uaaUrl, tokents, zoneId):
    
    headers = {
        'authorization': 'Basic ' + tokents,
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id':'timeseries_client_readonly',
        'grant_type':'client_credentials'
    }
    
    response = requests.request('POST', uaaUrl+"/oauth/token", data=data, headers=headers)
    tokents = json.loads(response.text)['access_token']
    headers = {
        'authorization': "Bearer " + tokents,
        'predix-zone-id': "" + zoneId,
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    
    response = requests.request("POST", tsDataUrl, data=payload, headers=headers)
    '''data = json.loads(response.text)['tags'][0]['results'][0]['values']
    column_labels = ['timestamp', 'values', 'quality']
    series = pd.DataFrame(data, columns=column_labels)
    series['timestamp'] = pd.to_datetime(series['timestamp'], unit='ms')'''
    return response
    
