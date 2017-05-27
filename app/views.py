from flask import Flask, render_template, flash, redirect, request, session
from uuid import uuid4
import requests
import requests.auth
import urllib
import base64
import os
import pandas as pd
import base64
import json
from app import app
from .forms import LoginForm
#from bokeh.io import output_notebook
#from bokeh.charts import TimeSeries, output_file, show 
#output_notebook()


## SET this only for local testing, if VCAPS is set env they will be overwritten by VCAPS.
CLIENT_ID = "dev" # "app_client_id"
UAA_URL= "https://marcv-dapep-flask.predix-uaa.run.aws-usw02-pr.ice.predix.io/" #"https://9c5f79c3-9760-47fc-b23f-0beba4525e10.predix-uaa.run.aws-usw02-pr.ice.predix.io"
BASE64ENCODING = "ZGV2OnRvdG8xMjM0" #'YXBwX2NsaWVudF9pZDpzZWNyZXQ='
port = int(os.getenv("PORT", 3000))
REDIRECT_URI = "http://localhost:3000/callback" #"http://localhost:"+str(port)+"/callback"

uaaUrl = "https://iiotquest-uaa-service.predix-uaa.run.aws-usw02-pr.ice.predix.io"
#tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/datapoints"
tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/tags"
payload_last = "{\"tags\": [{\"name\": \"Compressor-2015:CompressionRatio\"}]}"
payload_first = "{\"tags\": [{\"name\": \"Compressor-2015:CompressionRatio\"}]}"
zoneId = "6138f224-a4d2-4329-8a10-5ffdc3d4ca9f"
tokents = base64.b64encode('timeseries_client_readonly:IM_SO_SECRET')

## Setting up Oauth2 , this values should be read from vcaps .
APP_URL= None
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

if(os.getenv('client_id')):
    CLIENT_ID = os.getenv('client_id')

if(os.getenv('base64encodedClientDetails')):
    BASE64ENCODING = os.getenv('base64encodedClientDetails')


@app.route('/')
def home():
    #print 'Calling root resource'
    #text = '<br> <a href="%s">Authenticate with Predix UAA </a>'
    #return 'Hello from Python microservice template!'+text % getUAAAuthorizationUrl()

    key = session.get('key', 'not set')
    if 'access_token' in session:
        # TODO: call to Check_token to validate this token
        #return 'This is a secure page,gated by UAA'
        return redirect(APP_URL+"/index", code=302)
    else :
        #text = '<br> <a href="%s">Authenticate with Predix UAA </a>'
        #return 'Token not found, You are not logged in to UAA '+text % getUAAAuthorizationUrl()
        return redirect(getUAAAuthorizationUrl(), code=302)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for OpenID="%s", remember_me=%s' %
              (form.openid.data, str(form.remember_me.data)))
        return redirect('/index')
    return render_template('index/login.html', 
                           title='Sign In',
                           form=form)

@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
    flights = [  # fake array of posts
        { 
            'id': 1
        },
        { 
            'id': 2
        },
        { 
            'id': 3
        },
        { 
            'id': 4
        },
        { 
            'id': 5
        },
        { 
            'id': 6
        },
        { 
            'id': 7
        },
        { 
            'id': 8
        },
        { 
            'id': 9
        },
        { 
            'id': 10
        },
        { 
            'id': 11
        },
        { 
            'id': 12
        },
        { 
            'id': 13
        },
        { 
            'id': 14
        },
        { 
            'id': 15
        },
        { 
            'id': 16
        },
        { 
            'id': 17
        },
        { 
            'id': 18
        }
    ]
    
    firstPoint = doQuery(payload_first, tsUrl, uaaUrl, tokents, zoneId)
    '''startDate =  pd.Timestamp(firstPoint['timestamp'][0])
    startDate = int(startDate.strftime("%s")) * 1000
    startDateOrigin = startDate
    
    lastPoint = doQuery(payload_last, tsUrl, uaaUrl, tokents, zoneId)
    endDate =  pd.Timestamp(lastPoint['timestamp'][0])
    endDate = int(endDate.strftime("%s")) * 1000
    pdArray = []

    while (startDate < endDate ):
        payload = { 'cache_time': 0, 'tags': [{'name': 'Flight_128.Air_Density_ambient_kg_m', 'order': 'asc'}], 'start': startDate, 'end': startDate + 10000000}
        startDate = startDate + 100000000
        series = doQuery(json.dumps(payload), tsUrl, uaaUrl, tokents, zoneId)
        pdArray.append(series)

    fullseries = pd.concat(pdArray)
    '''

    return render_template('index/index.html',
                           title='Home',
                           flights=flights,
                           user=user, 
                           loginURL=getUAAAuthorizationUrl(),
                           fp=firstPoint)

@app.route('/dashboard')
def dashboardpage():
    print 'dashboard'
    return render_template('index/dashboard.html',
                            title='Dashboard',
                            app_url=APP_URL)

@app.route('/flight')
def flightspage():
    print 'flight'
    return render_template('index/flights.html',
                            title='Flight')

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

def base_headers():
    return {"Authorization": "Basic "+BASE64ENCODING }

def is_valid_state(state):
    if(state == 'secure' ) :
        return True
    else :
        return False

def doQuery(payload, tsUrl, uaaUrl, tokents, zoneId):
    
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
    #return json.loads(response.text)['access_token']
    headers = {
        'authorization': "Bearer " + tokents,
        'predix-zone-id': "" + zoneId,
        #'content-type': "application/json",
        #'cache-control': "no-cache"
    }
    
    response = requests.request("GET", tsUrl, data=payload, headers=headers)
    data = json.loads(response.text)#['tags'][0]['results'][0]['values']
    #column_labels = ['timestamp', 'values', 'quality']
    #series = pd.DataFrame(data, columns=column_labels)
    #series['timestamp'] = pd.to_datetime(series['timestamp'], unit='ms')
    return data
    
