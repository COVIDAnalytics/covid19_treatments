import os
import json
import shutil
import pandas as pd
import matplotlib.pylab as plt
import seaborn as sns
import numpy as np
import pickle
from analyzer.learners import scores, train_and_evaluate
from sklearn.model_selection import train_test_split
import shap

from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer, KNNImputer

FEATURE_BOUNDS_EXPLANATION = {'Alanine Aminotransferase (ALT)': [2.0, 929.0,'Alanine Aminotransferase (ALT) in U/L'],
                            'Prothrombin Time (INR)': [0.0, 17.0, 'Prothrombin Time Ratio (INR)'],
                            'Blood Creatinine': [0.0, 11.0, 'Blood Creatinine in mg/dL'],
                            'Respiratory Frequency': [14.0, 40.0, 'Number of Breaths per Minute'],
                            'Cholinesterase': [1422.0, 19851.0, 'Cholinesterase in Units per Liter (U/L)'],
                            'ABG: pH': [7.0, 8.0, 'Acid-base balance of the blood'],
                            'Blood Sodium': [115.0, 166.0, 'Blood Sodium in mmol/L'],
                            'CBC: Hemoglobin': [6.0, 19.0, 'Hemoglobin in g/dL'],
                            'Cardiac Frequency': [40.0, 171.0, 'Number of Beats per Minute.'],
                            'ABG: PaO2': [17.0, 305.0, 'Partial Pressure of Oxygen in mmHg'],
                            'Total Bilirubin': [0.0, 5.0, 'Total Bilirubin in mg/dL'],
                            'ABG: MetHb': [0.0, 3.0, 'Methemoglobin fraction'],
                            'ABG: Oxygen Saturation (SaO2)': [80, 100.0, 'Oxygen Saturation (SaO2) in %'],
                            'SaO2': [80, 100.0, 'Oxygen Saturation (SaO2) in %'],
                            'Potassium Blood Level': [2.0, 7.0, 'Potassium Blood Level in mmol/L'],
                            'Blood Urea Nitrogen (BUN)': [4.0, 174.0, 'Blood Urea Nitrogen (BUN) in mg/dL'],
                            'CBC: Leukocytes': [0.0, 36.0, 'Leukocytes in 10^3/muL'],
                            'Body Temperature': [34, 104.0, 'Body temperature measurement. Use the dropdown to select the unit (Fahrenheit or Celsius).'],
                            'CBC: Platelets': [20.0, 756.0, 'Platelets in 10^3/muL'],
                            'CBC: Mean Corpuscular Volume (MCV)': [58.0, 116.0,'Mean Corpuscular Volume (MCV) in fL'],
                            'Blood Calcium': [6.0, 12.0, 'Blood Calcium in mg/dL'],
                            'Age': [0.0, 100.0, 'Age of the patient. Modeled only for adults.'],
                            'C-Reactive Protein (CRP)': [0.0, 567.0, 'C-Reactive Protein (CRP) in mg/L'],
                            'Aspartate Aminotransferase (AST)': [9.0, 941.0,'Aspartate Aminotransferase (AST) in U/L'],
                            'Glycemia': [57.0, 620.0, 'Blood Glucose in mg/dL'],
                            'Systolic Blood Pressure': [20.0, 199.0, 'Systolic Blood Pressure in mmHg'],
                            'Gender': 'Select the gender of the patient', 
                            'Activated Partial Thromboplastin Time (aPTT)' : [0.0, 6.0, 'Activated Partial Thromboplastin Time in minutes'],
                            'Blood Amylase' : [10, 300, 'Blood Amylase Level in Units per Liter (U/L)'],
                            'CBC: Red cell Distribution Width (RDW)': [10, 27, 'Red cell Distribution Width in %']}


def change_SaO2(x):
    if x > 92:
        return 1
    else:
        return 0

def create_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def remove_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def top_features(model, X_train, n=20):
    varsImpo = pd.DataFrame({'names':X_train.columns,
                             'vals':model.feature_importances_})

    varsImpo = varsImpo.sort_values(by='vals',
                                    ascending = False)
    varsImpo = varsImpo[:n]

    print("Top %d\n" % n)
    print(varsImpo)
    return varsImpo

def plot_correlation(X, file_name):
    data_corr = X.copy()
    data_corr['Sex'] = data_corr['Sex'].astype(object)
    data_corr.loc[data_corr['Sex'] == 'M', 'Sex'] = 0
    data_corr.loc[data_corr['Sex'] == 'F', 'Sex'] = 1
    X_corr = data_corr.loc[:, data_corr.columns != 'outcome'].astype(np.float64).corr()

    # Plot correlation
    mask = np.triu(np.ones_like(X_corr.corr(), dtype=np.bool))

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(15, 15))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(X_corr.corr(), mask=mask, cmap=cmap, center=0,
                xticklabels=True, yticklabels=True,
                vmax=1.0, vmin=-1.0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})
    create_dir(os.path.dirname(file_name))
    plt.tight_layout()
    plt.savefig(file_name)

    # Print correlations > 0.25
    upper = X_corr.corr().where(np.triu(np.ones(X_corr.corr().shape), k=1).astype(np.bool))
    rows, columns = np.where(abs(upper) > 0.8)

    print("Highest correlations (> 0.8)")
    print(list(zip(upper.columns[rows], upper.columns[columns])))

def impute_missing(df, type = 'knn'):
    if type == 'knn':
        imputer = KNNImputer()
        imputer.fit(df)
    if type == 'iterative':
        imputer = IterativeImputer(random_state=0)
        imputer.fit(df)
    imputed_df = imputer.transform(df)
    df = pd.DataFrame(imputed_df, index=df.index, columns=df.columns)
    return df

categorical = ['Gender'] 
comorbidities = ['Cardiac dysrhythmias',
                'Chronic kidney disease',
                'Coronary atherosclerosis and other heart disease', 
                #'Essential hypertension',
                'Diabetes']
symptoms = []

def export_features_json(X, numeric, categorical,  symptoms, comorbidities):
    data = {'numeric': [],
            'categorical': [],
            'checkboxes': [],
            'multidrop': []}
    X = impute_missing(X)

    for i in range(len(numeric)):
        data['numeric'].append({"name":numeric[i], 'index' : list(X.columns).index(numeric[i]), "min_val" : FEATURE_BOUNDS_EXPLANATION[numeric[i]][0],
        "max_val" : FEATURE_BOUNDS_EXPLANATION[numeric[i]][1], "default" : np.round(np.median(X[numeric[i]]),2), 'explanation' : FEATURE_BOUNDS_EXPLANATION[numeric[i]][2]})

    for i in range(len(categorical)):
        data['categorical'].append({"name": categorical[i], 'index' : list(X.columns).index(categorical[i]), "vals" : list(np.unique(X[categorical[i]])),
        "default" : np.unique(X[categorical[i]])[0], 'explanation' : FEATURE_BOUNDS_EXPLANATION[categorical[i]] })

    data['checkboxes'].append({'name': "Symptoms", "index": [], "vals" : [], 'explanation': []})
    data['multidrop'].append({'name': "Comorbidities", "index": [], "vals" : [], 'explanation': []})

    for i in range(len(symptoms)):
        data['checkboxes'][0]["index"].append(list(X.columns).index(symptoms[i]))
        data['checkboxes'][0]["vals"].append(symptoms[i])
    data['checkboxes'][0]["explanation"].append("Select the existing symptoms.")


    for i in range(len(comorbidities)):
        data['multidrop'][0]["index"].append(list(X.columns).index(comorbidities[i]))
        data['multidrop'][0]["vals"].append(comorbidities[i])
    data['multidrop'][0]["explanation"].append("Select the existing chronic diseases or conditions.")
    return data


def export_model_imp_json(model, imp, json, cols, seed, accTest, ofsAUC, X_train, X_test, y_train, y_test, path):
    exp = {'model': model,
    'imputer': imp,
    'json': json,
    'columns': list(cols),
    'seed': seed,
    'Misclassification': np.round(accTest,2),
    'AUC': np.round(ofsAUC,2),
    'Size Training': len(X_train),
    'Size Test': len(X_test),
    'Percentage Training': np.round(np.mean(y_train),2),
    'Percentage Test': np.round(np.mean(y_test),2)}
    with open(path, 'wb') as handle:
        pickle.dump(exp, handle, protocol=4)
    return exp

def save_data(X_train, y_train, X_test, y_test, name, folder_path = '../../covid19_clean_data/'):
    X_train = impute_missing(X_train)
    X_test = impute_missing(X_test)
    train = pd.concat((X_train, y_train), axis = 1)
    test = pd.concat((X_test, y_test), axis = 1)
    train.to_csv(folder_path + name + '/train.csv')
    test.to_csv(folder_path + name + '/test.csv')
    return train, test
    

def get_percentages(df, missing_type=np.nan):
    if np.isnan(missing_type):
        df = df.isnull()  # Check what is NaN
    elif missing_type is False:
        df = ~df  # Check what is False

    percent_missing = df.sum() * 100 / len(df)
    return pd.DataFrame({'percent_missing': percent_missing})

def remove_missing(df, missing_type=np.nan, nan_threshold=40, impute=False):
    missing_values = get_percentages(df, missing_type)
    df_features = missing_values[missing_values['percent_missing'] < nan_threshold].index.tolist()

    df = df[df_features]

    if impute:
        imputer = KNNImputer()
        imputer.fit(df)
        imputed_df = imputer.transform(df)
        df = pd.DataFrame(imputed_df, index=df.index, columns=df.columns)

    return df

def create_and_save_pickle(algorithm, X_train, X_test, y_train, y_test, current_seed, best_seed, 
                            best_params, categorical, symptoms, comorbidities, name, pickle_path, 
                            data_save = False, data_in_pickle = False, folder_path = '../../covid19_clean_data/'):
    numeric = [i for i in X_train.columns if i not in categorical + symptoms + comorbidities]

    X_train = impute_missing(X_train) #impute training set
    X_test = impute_missing(X_test) #impute test set
    
    if current_seed == best_seed:
        data_save = True

    if data_save:
        train, test = save_data(X_train, y_train, X_test, y_test, name, folder_path) #save training and test

    best_model, accTrain, accTest, isAUC, ofsAUC = train_and_evaluate(algorithm, X_train, X_test, y_train, y_test, best_params) # get best learner and performances
    json = export_features_json(X_train, numeric, categorical,  symptoms, comorbidities) #create json
    cols = X_train.columns

    imputer = KNNImputer() #create imputer
    imputer = imputer.fit(X_train)
    
    exp = {'model': best_model,
            'imputer': imputer,
            'json': json,
            'columns': list(cols),
            'current seed': current_seed,
            'best seed': best_seed,
            'Misclassification': np.round(accTest,2),
            'AUC': np.round(ofsAUC,2),
            'Size Training': len(X_train),
            'Size Test': len(X_test),
            'Percentage Training': np.round(np.mean(y_train),2),
            'Percentage Test': np.round(np.mean(y_test),2)}
            
    if 'alpha' in best_params:
        explainer = shap.TreeExplainer(best_model); # create shap explainer
        shap_values = explainer.shap_values(X_train); # compute shap values for imputed training set
        
        # shap.summary_plot(shap_values, X_train, show=False, max_display=50)
        # ft_imp = plt.gcf()
        # exp['importance']= ft_imp,
        exp['explainer']= explainer

    if data_in_pickle:
        train = pd.concat((X_train, y_train), axis = 1)
        test = pd.concat((X_test, y_test), axis = 1)
        exp['train'] = train
        exp['test'] = test
    
    with open(pickle_path, 'wb') as handle:
        pickle.dump(exp, handle, protocol=4)
    return



# def create_and_save_pickle_treatments(algorithm, treatment, SEED, split_type,
#                                       X_train, y_train, test_data, 
#                                       best_params, file_name, results_folder,
#                                       data_save = True, data_in_pickle = True,
#                                       json_model = False):

#     pickle_path = results_folder + file_name
#     # if data_save:
#     #     train, test = save_data(X_train, y_train, X_test, y_test, file_name, results_folder) #save training and test

#     best_model, accTrain, accTest, isAUC, ofsAUC = train_and_evaluate(algorithm, X_train, X_test, y_train, y_test, best_params) # get best learner and performances
#     # json = export_features_json(X_train, numeric, categorical,  symptoms, comorbidities) #create json
#     # for d in test_data:
#     #     X_d = d[0]
#     #     y_d = d[1]
#     #     auc =  best_model.score(X, y, criterion='auc')
#     #     acc = best_model.score(X, y, criterion='misclassification')

#     cols = X_train.columns

#     # imputer = KNNImputer() #create imputer
#     # imputer = imputer.fit(X_train)

#     if json_model:
#         ## Fix issue where OCT cannot save as pickle
#         best_model.write_json(pickle_path+'.json')
#         best_model = 'json_model'
    
#     exp = {'model': best_model,
#            'treatment':treatment,
#            'split_type':split_type,
#             # 'imputer': imputer,
#             # 'json': json,
#             'columns': list(cols),
#             'current seed': SEED,
#             'Misclassification': np.round(accTest,2),
#             'AUC': np.round(ofsAUC,2),
#             'Size Training': len(X_train),
#             'Size Test': len(X_test),
#             'Percentage Training': np.round(np.mean(y_train),2),
#             'Percentage Test': np.round(np.mean(y_test),2)}
            
#     # if 'alpha' in best_params:
#     #     explainer = shap.TreeExplainer(best_model); # create shap explainer
#     #     shap_values = explainer.shap_values(X_train); # compute shap values for imputed training set
        
#     #     # shap.summary_plot(shap_values, X_train, show=False, max_display=50)
#     #     # ft_imp = plt.gcf()
#     #     # exp['importance']= ft_imp,
#     #     exp['explainer']= explainer

#     if data_in_pickle:
#         train = pd.concat((X_train, y_train), axis = 1)
#         test = pd.concat((X_test, y_test), axis = 1)
#         exp['train'] = train
#         exp['test'] = test
        
#     pickle_path = results_folder + file_name
    
#     with open(pickle_path, 'wb') as handle:
#         pickle.dump(exp, handle, protocol=4)
#     return


def create_and_save_pickle_treatments(algorithm, treatment, SEED, split_type,
                                      X_train, X_test, y_train, y_test, 
                                      best_params, file_name, results_folder,
                                      data_save = True, data_in_pickle = True,
                                      json_model = False):

    pickle_path = results_folder + file_name
    # if data_save:
    #     train, test = save_data(X_train, y_train, X_test, y_test, file_name, results_folder) #save training and test

    best_model, accTrain, accTest, isAUC, ofsAUC = train_and_evaluate(algorithm, X_train, X_test, y_train, y_test, best_params) # get best learner and performances
    # json = export_features_json(X_train, numeric, categorical,  symptoms, comorbidities) #create json
    cols = X_train.columns

    # imputer = KNNImputer() #create imputer
    # imputer = imputer.fit(X_train)

    if json_model:
        ## Fix issue where OCT cannot save as pickle
        best_model.write_json(pickle_path+'.json')
        best_model = 'json_model'
    
    exp = {'model': best_model,
           'treatment':treatment,
           'split_type':split_type,
            # 'imputer': imputer,
            # 'json': json,
            'columns': list(cols),
            'current seed': SEED,
            'Misclassification': np.round(accTest,2),
            'AUC': np.round(ofsAUC,2),
            'Size Training': len(X_train),
            'Size Test': len(X_test),
            'Percentage Training': np.round(np.mean(y_train),2),
            'Percentage Test': np.round(np.mean(y_test),2)}
            
    # if 'alpha' in best_params:
    #     explainer = shap.TreeExplainer(best_model); # create shap explainer
    #     shap_values = explainer.shap_values(X_train); # compute shap values for imputed training set
        
    #     # shap.summary_plot(shap_values, X_train, show=False, max_display=50)
    #     # ft_imp = plt.gcf()
    #     # exp['importance']= ft_imp,
    #     exp['explainer']= explainer

    if data_in_pickle:
        train = pd.concat((X_train, y_train), axis = 1)
        test = pd.concat((X_test, y_test), axis = 1)
        exp['train'] = train
        exp['test'] = test
        
    pickle_path = results_folder + file_name
    
    with open(pickle_path, 'wb') as handle:
        pickle.dump(exp, handle, protocol=4)
    return










