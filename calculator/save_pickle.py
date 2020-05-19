import pandas as pd
import numpy as np
import analyzer.utils as u
import pickle
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

import xgboost as xgb

from analyzer.learners import scores, train_and_evaluate

best_seed = 30
current_seed = 30

BEST_PARAMS_AND_SEEDS = {'mortality_with_lab': {'xgboost': {'best_seed': best_seed, 
                                                        'best_params': {'n_estimators': 900,
                                                                        'learning_rate': 2.080204e-02,
                                                                        'max_depth': 10,
                                                                        'min_child_weight': 1.000000e-07,
                                                                        'gamma': 4.936753e+00,
                                                                        'colsample_bytree': 5.528630e-01,
                                                                        'lambda': 1.000000e-07}},

                                                'cart': {'best_seed': best_seed, 
                                                        'best_params': { 'max_depth': 22,
                                                        'min_weight_fraction_leaf':  0.0095584,
                                                        'min_samples_leaf': 0.0639822,
                                                        'min_samples_split': 0.14137,
                                                        'min_impurity_decrease':  0,
                                                        'criterion':    'entropy'}},
                                                'lr': {'best_seed': best_seed, 
                                                        'best_params': {'penalty': 'none',
                                                                        'tol':  1e-05,
                                                                        'C': 1.77829,
                                                                        'solver': 'saga'}}},


                        'mortality_without_lab': {'xgboost': {'best_seed': best_seed, 
                                                        'best_params': {'n_estimators': 357,
                                                                        'learning_rate': 9.958195e-02,
                                                                        'max_depth': 10,
                                                                        'min_child_weight': 1.000000e-07,
                                                                        'gamma': 7.359521e+00,
                                                                        'colsample_bytree': 3.752731e-01,
                                                                        'lambda':   1.000000e-07}},

                                                'cart': {'best_seed': best_seed, 
                                                        'best_params': { 'max_depth': 6,
                                                                        'min_weight_fraction_leaf':  0.0399055,
                                                                        'min_samples_leaf': 0.0001,
                                                                        'min_samples_split': 0.0001,
                                                                        'min_impurity_decrease':  0,
                                                                        'criterion':    'gini'}},
                                                'lr': {'best_seed': best_seed, 
                                                        'best_params': {'penalty': 'l1', 
                                                                        'tol': 1e-05, 
                                                                        'C': 0.267824, 
                                                                        'solver': 'saga'}}},

                        'infection_with_lab': {'xgboost': {'best_seed': best_seed, 
                                                        'best_params': {'n_estimators': 635,
                                                                        'learning_rate': 0.031542,
                                                                        'max_depth': 10,
                                                                        'min_child_weight': 1,
                                                                        'gamma': 2.843149,
                                                                        'colsample_bytree': 0.398404,
                                                                        'lambda':20}},

                                                'cart': {'best_seed': best_seed, 
                                                        'best_params': {'max_depth': 20,
                                                                        'min_weight_fraction_leaf':  0.0167917,
                                                                        'min_samples_leaf': 0.0209234,
                                                                        'min_samples_split': 0.0001,
                                                                        'min_impurity_decrease':  0,
                                                                        'criterion':    'entropy'}},
                                                'lr': {'best_seed': best_seed, 
                                                        'best_params': {'penalty': 'l2',
                                                                        'tol':  1e-05,
                                                                        'C': 2,
                                                                        'solver': 'saga'}}},

                        'infection_without_lab': {'xgboost': {'best_seed': best_seed, 
                                                        'best_params': {'n_estimators': 900,
                                                                        'learning_rate': 1.951791e-02,
                                                                        'max_depth': 10,
                                                                        'min_child_weight': 1.000000e-07,
                                                                        'gamma': 3.464945e+00,
                                                                        'colsample_bytree': 4.340650e-01,
                                                                        'lambda': 6.077259e+00}},

                                                'cart': {'best_seed': best_seed, 
                                                        'best_params': { 'max_depth': 6,
                                                                        'min_weight_fraction_leaf':  0.0558581,
                                                                        'min_samples_leaf': 0.0215371,
                                                                        'min_samples_split': 0.0001,
                                                                        'min_impurity_decrease':  0,
                                                                        'criterion':    'gini'}},
                                                'lr': {'best_seed': best_seed, 
                                                        'best_params': {'penalty': 'l1',
                                                                        'tol':  1e-05,
                                                                        'C': 0.160919,
                                                                        'solver':    'saga'}}}}

predictions = ['mortality_with_lab', 'mortality_without_lab', 'infection_with_lab', 'infection_without_lab']
algorithms_name = ['xgboost', 'cart', 'lr']
algorithms = [xgb.XGBClassifier, DecisionTreeClassifier, LogisticRegression]
website_path = '../../website/assets/risk_calculators'
post_processing_path = '../../covid19_clean_data'

categorical = ['Gender'] 
comorb = ['Cardiac dysrhythmias',
                'Chronic kidney disease',
                'Coronary atherosclerosis and other heart disease', 
                #'Essential hypertension',
                'Diabetes']
symptoms = []

len_seed = 40

i = 0
prediction = predictions[i]
best_seed = BEST_PARAMS_AND_SEEDS[prediction]['xgboost']['best_seed'] #seed of the model to save on the website
best_params = BEST_PARAMS_AND_SEEDS[prediction]['xgboost']['best_params'] #parameters of the model to save on the website

if i == 0: #mortality_with_lab
        comorbidities = comorb.copy()

        # u.create_and_save_pickle(xgb.XGBClassifier, X_train, X_test, y_train, y_test, best_seed, best_seed, best_params, categorical, #Save on the website
        #                                 symptoms, comorbidities, prediction, website_path + '/mortality/model_with_lab.pkl', 
        #                                 data_save = True, data_in_pickle = False, folder_path = post_processing_path + '/xgboost/')

        # for current_seed in range(1, len_seed + 1):
        for j in range(len(algorithms)):
                algorithm = algorithms[j]
                algorithm_name = algorithms_name[j]

                best_seed = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_seed']
                best_params = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_params']

                u.create_and_save_pickle(algorithm, X_train, X_test, y_train, y_test, current_seed, best_seed, best_params, categorical, #Save for post processing
                                        symptoms, comorbidities, prediction, post_processing_path + '/' + algorithm_name + '/' + prediction + '/seed' + str(current_seed) + '.pkl', 
                                        data_save = False, data_in_pickle = True, folder_path = post_processing_path + '/' + algorithm_name + '/')

if i == 1: #mortality_without_lab
        comorbidities = comorb.copy()

        # u.create_and_save_pickle(xgb.XGBClassifier, X_train, X_test, y_train, y_test, best_seed, best_seed, best_params, categorical, #Save on the website
        #                                 symptoms, comorbidities, prediction, website_path + '/mortality/model_without_lab.pkl', 
        #                                 data_save = True, data_in_pickle = False, folder_path = post_processing_path + '/xgboost/')

        # for current_seed in range(1, len_seed + 1):
        for j in range(len(algorithms)):
                algorithm = algorithms[j]
                algorithm_name = algorithms_name[j]

                best_seed = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_seed']
                best_params = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_params']

                u.create_and_save_pickle(algorithm, X_train, X_test, y_train, y_test, current_seed, best_seed, best_params, categorical, #Save for post processing
                                        symptoms, comorbidities, prediction, post_processing_path + '/' + algorithm_name + '/' + prediction + '/seed' + str(current_seed) + '.pkl', 
                                        data_save = False, data_in_pickle = True, folder_path = post_processing_path + '/' + algorithm_name + '/')

if i == 2: #infection_with_lab
        comorbidities = []

        # u.create_and_save_pickle(xgb.XGBClassifier, X_train, X_test, y_train, y_test, best_seed, best_seed, best_params, categorical, #Save on the website
        #                                 symptoms, comorbidities, prediction, website_path + '/infection/model_with_lab.pkl', 
        #                                 data_save = True, data_in_pickle = False, folder_path = post_processing_path + '/xgboost/')

        # for current_seed in range(1, len_seed + 1):
        for j in range(len(algorithms)):
                algorithm = algorithms[j]
                algorithm_name = algorithms_name[j]

                best_seed = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_seed']
                best_params = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_params']

                u.create_and_save_pickle(algorithm, X_train, X_test, y_train, y_test, current_seed, best_seed, best_params, categorical, #Save for post processing
                                        symptoms, comorbidities, prediction, post_processing_path + '/' + algorithm_name + '/' + prediction + '/seed' + str(current_seed) + '.pkl', 
                                        data_save = False, data_in_pickle = True, folder_path = post_processing_path + '/' + algorithm_name + '/')

if i == 3: #infection_without_lab
        comorbidities = []

        # u.create_and_save_pickle(xgb.XGBClassifier, X_train, X_test, y_train, y_test, best_seed, best_seed, best_params, categorical, #Save on the website
        #                                 symptoms, comorbidities, prediction, website_path + '/infection/model_without_lab.pkl', 
        #                                 data_save = True, data_in_pickle = False, folder_path = post_processing_path + '/xgboost/')

        # for current_seed in range(1, len_seed + 1):
        for j in range(len(algorithms)):
                algorithm = algorithms[j]
                algorithm_name = algorithms_name[j]

                best_seed = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_seed']
                best_params = BEST_PARAMS_AND_SEEDS[prediction][algorithm_name]['best_params']

                u.create_and_save_pickle(algorithm, X_train, X_test, y_train, y_test, current_seed, best_seed, best_params, categorical, #Save for post processing
                                        symptoms, comorbidities, prediction, post_processing_path + '/' + algorithm_name + '/' + prediction + '/seed' + str(current_seed) + '.pkl', 
                                        data_save = False, data_in_pickle = True, folder_path = post_processing_path + '/' + algorithm_name + '/')