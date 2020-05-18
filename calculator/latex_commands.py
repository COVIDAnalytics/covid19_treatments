#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 09:30:50 2020

@author: agni
"""

import numpy as np
import pandas as pd
import os
import pickle
import csv

import evaluation_utils as u
import matplotlib.pyplot as plt
from sklearn import metrics

def convert_to_latex(command_name, val):    
    com = '\\newcommand{\\' + command_name +'}{'+val+'}}'  
    return com


def extract_metric_from_table_to_latex(command_name, model_type, model_labs,  cohort, metric):
    
    # Table 1: AUC and Sensitivity results with confidence intervals
    results_table_path = '../results/'+model_type+'/paper_tables/summary_perforamance_'+model_type+'_AUC_sensitivity.csv'
    
    df =  pd.read_csv(results_table_path, encoding= 'unicode_escape')
    
    # Model with labs - Test
    auclabstest = df.loc[(df['Model Labs']==model_labs) & (df['Cohort']== cohort), metric].to_string()
    x = auclabstest
    
    main_res =  str(round(float(x.split(' ')[4])/100,2))
    ci_res =x.split(' ')[5]
    l = str(round(float(ci_res.split(',')[0].replace('(', ''))/100,2))
    h = str(round(float(ci_res.split(',')[1].replace(')', ''))/100,2))
    
    val = main_res+' (95% CI, '+l+'-' + h +')'
    
    com =  convert_to_latex(command_name, val)
    return com


shortcuts = list()

shortcuts.append('% Model with labs - Test')

shortcuts.append(extract_metric_from_table_to_latex('auclabstest', 'mortality', 'with_lab', 'Testing Set', 'AUC'))
shortcuts.append(extract_metric_from_table_to_latex('acclabstest', 'mortality', 'with_lab', 'Testing Set', 'Accuracy'))
shortcuts.append(extract_metric_from_table_to_latex('speclabstest', 'mortality', 'with_lab', 'Testing Set', 'Specificity'))
shortcuts.append(extract_metric_from_table_to_latex('preclabstest', 'mortality', 'with_lab', 'Testing Set', 'Precision'))
shortcuts.append(extract_metric_from_table_to_latex('npvlabstest', 'mortality', 'with_lab', 'Testing Set', 'Negative predictive value'))

shortcuts.append('%Model with labs - Greece')

shortcuts.append(extract_metric_from_table_to_latex('auclabstest', 'mortality', 'with_lab', 'Greek HC', 'AUC'))
shortcuts.append(extract_metric_from_table_to_latex('acclabstest', 'mortality', 'with_lab', 'Greek HC', 'Accuracy'))
shortcuts.append(extract_metric_from_table_to_latex('speclabstest', 'mortality', 'with_lab', 'Greek HC', 'Specificity'))
shortcuts.append(extract_metric_from_table_to_latex('preclabstest', 'mortality', 'with_lab', 'Greek HC', 'Precision'))
shortcuts.append(extract_metric_from_table_to_latex('npvlabstest', 'mortality', 'with_lab', 'Greek HC', 'Negative predictive value'))

shortcuts.append('% Model without labs - Test')


shortcuts.append(extract_metric_from_table_to_latex('auclabstest', 'mortality', 'without_lab', 'Testing Set', 'AUC'))
shortcuts.append(extract_metric_from_table_to_latex('acclabstest', 'mortality', 'without_lab', 'Testing Set', 'Accuracy'))
shortcuts.append(extract_metric_from_table_to_latex('speclabstest', 'mortality', 'without_lab', 'Testing Set', 'Specificity'))
shortcuts.append(extract_metric_from_table_to_latex('preclabstest', 'mortality', 'without_lab', 'Testing Set', 'Precision'))
shortcuts.append(extract_metric_from_table_to_latex('npvlabstest', 'mortality', 'without_lab', 'Testing Set', 'Negative predictive value'))

shortcuts.append('%Model without labs - Greece')

shortcuts.append(extract_metric_from_table_to_latex('auclabstest', 'mortality', 'without_lab', 'Greek HC', 'AUC'))
shortcuts.append(extract_metric_from_table_to_latex('acclabstest', 'mortality', 'without_lab', 'Greek HC', 'Accuracy'))
shortcuts.append(extract_metric_from_table_to_latex('speclabstest', 'mortality', 'without_lab', 'Greek HC', 'Specificity'))
shortcuts.append(extract_metric_from_table_to_latex('preclabstest', 'mortality', 'without_lab', 'Greek HC', 'Precision'))
shortcuts.append(extract_metric_from_table_to_latex('npvlabstest', 'mortality', 'without_lab', 'Greek HC', 'Negative predictive value'))


#Save the shortcuts in a txt
results_shortcuts_path = '../results/'+model_type+'/paper_tables/shortcuts.txt'
with open(results_shortcuts_path, 'w') as f:
    for item in shortcuts:
        f.write("%s\n" % item)
