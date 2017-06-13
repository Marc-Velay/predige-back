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
#CLIENT_ID = "dev" # "app_client_id"
#UAA_URL= "https://marcv-dapep-flask.predix-uaa.run.aws-usw02-pr.ice.predix.io/" #"https://9c5f79c3-9760-47fc-b23f-0beba4525e10.predix-uaa.run.aws-usw02-pr.ice.predix.io"
#BASE64ENCODING = "ZGV2OnRvdG8xMjM0" #'YXBwX2NsaWVudF9pZDpzZWNyZXQ='
port = int(os.getenv("PORT", 3000))
#REDIRECT_URI = "http://localhost:3000/callback" #"http://localhost:"+str(port)+"/callback"

uaaUrl = "https://MMEurope.predix-uaa.run.aws-usw02-pr.ice.predix.io"
tsDataUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/datapoints"
tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/tags"
requestTags = "{\"tags\": [{\"name\": \"Compressor-2015:CompressionRatio\"}]}"
#requestData = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"asc\",      \"limit\": 1    }  ]}"
requestData = "{ \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",     }  ]}"
requestData_last = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"desc\",      \"limit\": 1    }  ]}"
requestData_first = "{  \"start\": \"50y-ago\",  \"tags\": [    {      \"name\": \"Flight_13.Air_Density_ambient_kg_m\",      \"order\": \"asc\",      \"limit\": 1    }  ]}"
zoneId = "3464894c-1cf7-440f-8f5c-a27314e35066"
tokents = base64.b64encode('timeseries_client_readonly:secret'.encode())

## Setting up Oauth2 , this values should be read from vcaps .
APP_URL= "http://localhost:3000/"
# Get UAA credentials from VCAPS
#if 'VCAP_SERVICES' in os.environ:
    #services = json.loads(os.getenv('VCAP_SERVICES'))
    #uaa_env = services['predix-uaa'][0]['credentials']
    #UAA_URL=uaa_env['uri']

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
        return redirect(APP_URL+"/flight", code=302)
    else : #if not IDed, redirect to identification url
        return redirect(APP_URL+"/flight", code=302)

@app.route('/flight', methods=['GET', 'POST'])
def flightspage():
    tags = set()
    flight = None
    tag = None
    firstPoint = doQueryTags(requestTags, tsUrl, uaaUrl, tokents, zoneId)
    for item in firstPoint["results"]:
        tags.add(item)
    print(tags)
    return render_template('index/index.html',
                            title='Flight',
                            fp=tags)

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
        tags.add(item)

    requestDatafromTag_last = {"start": "50y-ago", "tags": [{"name": tag, "order": "desc", "limit": 1}]}
    requestDatafromTag_first = {"start": "50y-ago", "tags": [{"name": tag, "order": "asc", "limit": 1}]}


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

    '''while (startDate < endDate ):
        payload = { 'cache_time':0, 'tags':[{'name': flight+"."+tag, 'order': 'asc'}], 'start': startDate, 'end': startDate + 10000000}
        startDate = startDate + 100000000
        series = doQuery(json.dumps(payload, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)
        pdArray.append(series)'''
    payload = { 'start':"1mm-ago", 'tags':[{'name': tag, 'order': 'asc', 'limit':200}]}
    pdArray = doQuery(json.dumps(payload, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId)

    fullseries = pdArray
    data = dict(vals = fullseries['values'], Date=fullseries['timestamp'])
    dataJson = json.dumps([{'Date': time, 'val': value} for time, value in zip(data['Date'], data['vals'])], default=json_serial)
    data = json.loads(dataJson)
    return json.dumps({'success':True, 'data':data}), 200, {'ContentType':'application/json'}

'''
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
'''
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
    print(tokents.decode('utf-8'))
    headers = {
        'authorization': 'Basic ' + tokents.decode('utf-8'),
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
        'authorization': 'Basic ' + tokents.decode('utf-8'),
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
    
