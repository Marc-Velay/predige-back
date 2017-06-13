import numpy as np
import pandas as pd
import requests
import requests.auth
from matplotlib import pyplot as plt
import pandas as pd
import base64
import json, codecs
from datetime import datetime
import os

from tensorflow.contrib import learn
from sklearn.metrics import mean_squared_error, mean_absolute_error
from .lstm_predictor import generate_data, load_csvdata, lstm_model


port = int(os.getenv("PORT", 3000))
uaaUrl = "https://MMEurope.predix-uaa.run.aws-usw02-pr.ice.predix.io"
tsDataUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/datapoints"
tsUrl = "https://time-series-store-predix.run.aws-usw02-pr.ice.predix.io/v1/tags"
zoneId = "3464894c-1cf7-440f-8f5c-a27314e35066"
tokents = base64.b64encode('timeseries_client_readonly:secret'.encode())

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
    '''
    LOG_DIR = './ops_logs'
    TIMESTEPS = 10
    RNN_LAYERS = [{'steps': TIMESTEPS}]
    DENSE_LAYERS = [10, 10]
    TRAINING_STEPS = 100000
    BATCH_SIZE = 100
    PRINT_STEPS = TRAINING_STEPS / 100

    dateparse = lambda dates: pd.datetime.strptime(dates, '%d/%m/%Y %H:%M')
    rawdata = pd.read_csv("./input/ElectricityPrice/RealMarketPriceDataPT.csv", 
                    parse_dates={'timeline': ['date', '(UTC)']}, 
                    index_col='timeline', date_parser=dateparse)


    X, y = load_csvdata(rawdata, TIMESTEPS, seperate=False)


    regressor = learn.Estimator(model_fn=lstm_model(TIMESTEPS, RNN_LAYERS, DENSE_LAYERS), 
                                        n_classes=0,
                                        verbose=1,  
                                        steps=TRAINING_STEPS, 
                                        optimizer='Adagrad',
                                        learning_rate=0.03, 
                                        batch_size=BATCH_SIZE)




    validation_monitor = learn.monitors.ValidationMonitor(X['val'], y['val'],
                                                        every_n_steps=PRINT_STEPS,
                                                        early_stopping_rounds=1000)

    regressor.fit(X['train'], y['train'], monitors=[validation_monitor], logdir=LOG_DIR)


    predicted = regressor.predict(X['test'])
    mse = mean_absolute_error(y['test'], predicted)
    print ("Error: %f" % mse)

    plot_predicted, = plt.plot(predicted, label='predicted')
    plot_test, = plt.plot(y['test'], label='test')
    plt.legend(handles=[plot_predicted, plot_test])
'''

'''
def test():
    hello = tf.constant('Hello, TensorFlow!')
    sess = tf.Session()
    time.sleep(15)
    print(sess.run(hello))
'''