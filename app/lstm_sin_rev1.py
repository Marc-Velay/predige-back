import numpy as np
import pandas as pd
import tensorflow as tf
from matplotlib import pyplot as plt
import warnings
#import numpy.subtract as sb
from tensorflow.contrib import learn
from tensorflow.contrib.learn.python import SKCompat
from sklearn.metrics import mean_squared_error

from lstm_predictior import generate_data, lstm_model, load_csvdata
from weathercsvparser import get_data, print_tab

warnings.filterwarnings("ignore")

LOG_DIR = 'resources/logs/'
TIMESTEPS = 1
RNN_LAYERS = [{'num_units': 400}]
DENSE_LAYERS = None
TRAINING_STEPS = 5000
PRINT_STEPS = TRAINING_STEPS # / 10
BATCH_SIZE = 100

regressor = SKCompat(learn.Estimator(model_fn=lstm_model(TIMESTEPS, RNN_LAYERS, DENSE_LAYERS),))
                          #   model_dir=LOG_DIR)

#X, y = generate_data(np.sin, np.linspace(0, 100, 10000, dtype=np.float32), TIMESTEPS, seperate=False)
X, y = load_csvdata(TIMESTEPS,seperate=False)

#noise_train = np.asmatrix(np.random.normal(0,0.2,len(y['train'])),dtype = np.float32)
#noise_val = np.asmatrix(np.random.normal(0,0.2,len(y['val'])),dtype = np.float32)
#noise_test = np.asmatrix(np.random.normal(0,0.2,len(y['test'])),dtype = np.float32) #asmatrix

#noise_train = np.transpose(noise_train)
#noise_val = np.transpose(noise_val)
#noise_test = np.transpose(noise_test)


#y['train'] = np.add( y['train'],noise_train)
#y['val'] = np.add( y['val'],noise_val)
#y['test'] = np.add( y['test'],noise_test)


# print(type(y['train']))


print('-----------------------------------------')
print('train y shape',y['train'].shape)
print('train y shape_num',y['train'][1:5])
#print('noise_train shape',noise_train.shape)
#print('noise_train shape_num',noise_train.shape[1:5])
print(y['val'].shape)
y['val'] = y['val'].reshape(359,8)
# create a lstm instance and validation monitor
validation_monitor = learn.monitors.ValidationMonitor(X['val'], y['val'],)
                                                     # every_n_steps=PRINT_STEPS,)
                                                     # early_stopping_rounds=1000)
# print(X['train'])
y['train'] = y['train'].reshape(3238,8)
#print(y['train'].shape)

SKCompat(regressor.fit(X['train'], y['train'],
              monitors=[validation_monitor],
              batch_size=BATCH_SIZE,
              steps=TRAINING_STEPS))

print('X train shape', X['train'].shape)
print('y train shape', y['train'].shape)
#print_tab(y['test'])
y['test'] = y['test'].reshape(399,8)
#print_tab(y['test'])
print('X test shape', X['test'].shape)
print('y test shape', y['test'].shape)
print('C\'est un pic !',X['test'].shape)
lol2 = regressor.predict(X['test'])
print('C\est un roc ! ', lol2.shape)
predicted = np.asmatrix(lol2,dtype = np.float32) #,as_iterable=False))
print('C\est un cap ! ',predicted.shape)
#predicted = np.transpose(predicted)
print('Que dis-je ? ', predicted.shape, 'C\'est une péninsule ! ', y['test'].shape)

lol = np.asarray((predicted - y['test'])) ** 2
print ('substract array : ', lol.shape)
rmse = np.sqrt((lol).mean()) 
print(rmse.shape)
# this previous code for rmse was incorrect, array and not matricies was needed: rmse = np.sqrt(((predicted - y['test']) ** 2).mean())  
score = mean_squared_error(predicted, y['test']) #.reshape(397,8))
nmse = score / np.var(y['test']) # should be variance of original data and not data from fitted model, worth to double check

print("RSME: %f" % rmse)
print("NSME: %f" % nmse)
print("MSE: %f" % score)