import numpy as np
import pandas as pd
import requests
import requests.auth
import pandas as pd
import base64
import json, codecs
from datetime import datetime
import os
import warnings

from tensorflow.contrib import learn
from tensorflow.contrib.learn.python import SKCompat
from sklearn.metrics import mean_squared_error

from .lstm_predictior import generate_data, lstm_model, load_csvdata
from .weathercsvparser import get_data, print_tab


port = int(os.getenv("PORT", 3000))
uaaUrl = "https://MMEurope.predix-uaa.run.aws-usw02-pr.ice.predix.io"
tsDataUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/datapoints"
tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/tags"
zoneId = "3464894c-1cf7-440f-8f5c-a27314e35066"
tokents = base64.b64encode('timeseries_client_readonly:secret'.encode())



warnings.filterwarnings("ignore")

LOG_DIR = 'resources/logs/'
TIMESTEPS = 1
RNN_LAYERS = [{'num_units': 400}]
DENSE_LAYERS = None
TRAINING_STEPS = 5000
PRINT_STEPS = TRAINING_STEPS # / 10
BATCH_SIZE = 100


## Setting up Oauth2 , this values should be read from vcaps .
APP_URL= "http://localhost:3000/"

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

#####################################################

dataQueries = []
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC12','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC13','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC14','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC18','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC19','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC21','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC24','order':'asc',"limit": 8000}]})
dataQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/LoadData/Mullingar/MC25','order':'asc',"limit": 8000}]})

weatherQueries=[]
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/dewpt','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/irain','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/itemp','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/iwb','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/iwddir','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/iwdsp','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/msl','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/rain','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/rhum','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/temp','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/vappr','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/wddir','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/wdsp','order':'asc',"limit": 4000}]})
weatherQueries.append({'start':'1y-ago','tags':[{'name':'LoadForecasting/WeatherData/Mullingar/wetb','order':'asc',"limit": 4000}]})

#####################################################

def gatherData():
    dataSeries = []
    for query in dataQueries:
        dataSeries.append(doQuery(json.dumps(query, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId))
        print('data done +1')
    weatherSeries = []
    for query in weatherQueries:
        weatherSeries.append(doQuery(json.dumps(query, codecs.getwriter('utf-8'), ensure_ascii=False), tsDataUrl, uaaUrl, tokents, zoneId))
        print('wheater done +1')
    input = []
    output = []
    rowin = []
    rowout = []
    tmpNum =0
    for rowNum in range(4000):
        rowin.append(weatherSeries[0][rowNum][0])
        for colNum in range(14):
            rowin.append(weatherSeries[colNum][rowNum][1])
        for colNum in range(8):
            rowout.append(dataSeries[colNum][tmpNum][1])
        tmpNum+=2
        print(rowin)
        print(tmpNum)
        input.append(rowin.copy())
        output.append(rowout.copy())
        rowin.clear()
        rowout.clear()
    np.savetxt("input.csv", input, delimiter=";")
    np.savetxt("output.csv", output, delimiter=";")


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
    #series = pd.DataFrame(data, columns=column_labels)
    #series['timestamp'] = pd.to_datetime(series['timestamp'], unit='ms')
    return data


def test():
    if((os.path.isfile("input.csv") == False) and (os.path.isfile("output.csv") == False)):
        gatherData()
   
    regressor = SKCompat(learn.Estimator(model_fn=lstm_model(TIMESTEPS, RNN_LAYERS, DENSE_LAYERS),))

    X, y = load_csvdata(TIMESTEPS,seperate=False)


    print('-----------------------------------------')
    print('train y shape',y['train'].shape)
    print('train y shape_num',y['train'][1:5])
    print(y['val'].shape)
    y['val'] = y['val'].reshape(359,8)
    # create a lstm instance and validation monitor
    validation_monitor = learn.monitors.ValidationMonitor(X['val'], y['val'],)
    y['train'] = y['train'].reshape(3239,8)

    SKCompat(regressor.fit(X['train'], y['train'],
                monitors=[validation_monitor],
                batch_size=BATCH_SIZE,
                steps=TRAINING_STEPS))

    print('X train shape', X['train'].shape)
    print('y train shape', y['train'].shape)
    y['test'] = y['test'].reshape(399,8)
    print('X test shape', X['test'].shape)
    print('y test shape', y['test'].shape)
    lol2 = regressor.predict(X['test'])
    predicted = np.asmatrix(lol2,dtype = np.float32) #,as_iterable=False))

    lol = np.asarray((predicted - y['test'])) ** 2
    rmse = np.sqrt((lol).mean()) 
    print(rmse.shape)
    # this previous code for rmse was incorrect, array and not matricies was needed: rmse = np.sqrt(((predicted - y['test']) ** 2).mean())  
    score = mean_squared_error(predicted, y['test']) #.reshape(397,8))
    nmse = score / np.var(y['test']) # should be variance of original data and not data from fitted model, worth to double check

    print("RSME: %f" % rmse)
    print("NSME: %f" % nmse)
    print("MSE: %f" % score)