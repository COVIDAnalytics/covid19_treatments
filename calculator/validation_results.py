
import os

# os.chdir('/Users/hollywiberg/Dropbox (MIT)/COVID_risk/covid19_calculator/calculator')

import evaluation.treatment_utils as u
from sklearn.impute import KNNImputer
import pandas as pd
import numpy as np
from pathlib import Path


from sklearn.metrics import (brier_score_loss, precision_score, recall_score,accuracy_score,
                             f1_score, confusion_matrix)
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.metrics import classification_report

from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import matplotlib.pyplot as plt
from sklearn import metrics

#%% Load data and prescriptions
data_version = 'partners'
data_list = ['partners']

outcome = 'COMORB_DEATH'
prediction_list = ['COMORB_DEATH']

data_path = '../../covid19_treatments_data/'
data = pd.read_csv(data_path+'partners_treatments_2020-09-16.csv')

## Select results version
version = 'matched_single_treatments_der_val_addl_outcomes/'
results_path = '../../covid19_treatments_results/'+version
matched = True
match_status = 'matched' if matched else 'unmatched'

SEEDS = range(1, 2)
# algorithm_list = ['lr','rf','cart','oct','xgboost','qda','gb']
# prediction_list = ['COMORB_DEATH','OUTCOME_VENT','DEATH','HF','ARF','SEPSIS']
# algorithm_list = ['lr','rf','cart','qda','gb','xgboost']
algorithm_list = ['rf','cart','qda','gb','xgboost']

# data_list = ['train','test']

treatment = 'ACEI_ARBS'
treatment_list = [treatment, 'NO_'+treatment]

version_folder = str(treatment)+'/'+str(outcome)+'/'
save_path = results_path + version_folder + 'summary/'
    
## Load data for comparison
training_set_name = treatment+'_hope_hm_cremona_matched_all_treatments_train.csv'
X_train, Z_train, y_train = u.load_data(data_path+version,training_set_name,
                                split='train', matched=matched, prediction = outcome,
                                med_hx  = False, other_tx = False)

#%% Match new data to training format
## Impute missing data

data_oh = pd.get_dummies(data, prefix_sep='_', drop_first=True)
X = data_oh.reindex(X_train.columns, axis=1)
Z = data[treatment].apply(lambda x: treatment if x==1 else 'NO_'+treatment).rename('REGIMEN')
y = data[outcome]

ft_val = X.describe().transpose().add_prefix('val_')
ft_train = X_train.describe().transpose().add_prefix('train_')

pd.concat([ft_val, ft_train], axis=1).to_csv(data_path+'feature_comparison_partners.csv')
#%% For each method, generate predictions and accuracies of each method
## Part 1: generate results for all outcomes

print("X observations: " , str(X.shape[0]))
result = pd.concat([u.algorithm_predictions(X, treatment_list = treatment_list, 
                                        algorithm = alg,  matched = matched, 
                                        prediction = outcome,
                                        result_path = results_path+version_folder) 
                for alg in algorithm_list], axis = 0)
# Find optimal prescription across methods
result['Prescribe'] = result.idxmin(axis=1)
result['Prescribe_Prediction'] = result.min(axis=1)
#  Save result file
result.to_csv(save_path+data_version+'_'+match_status+'_bypatient_allmethods.csv')
# =============================================================================
# Predictive Performance evaluation:
# - Given a combination of treatment and method calculate the AUC 
# - All results are saved in a panda where every column is a treatment and every row is a different algorithm
# =============================================================================

pred_results = u.algorithms_pred_evaluation(X, Z, y, treatment_list, algorithm_list, 
                                        matched = matched, prediction = outcome,
                                        result_path = results_path+version_folder)
pred_results.to_csv(save_path+data_version+'_'+match_status+'_performance_allmethods.csv', index_label = 'Algorithm')
            

#%% Part 2: save results
metrics_agg = pd.DataFrame(columns = ['data_version','weighted_status','threshold','match_rate','presc_count','average_auc','PE','pr_low','pr_high'])


## Data is already loaded (X,Z,y)
for outcome in prediction_list:
    version_folder = str(treatment)+'/'+str(outcome)+'/'
    save_path = results_path + version_folder + 'summary/'
    # create summary folder if it does not exist
    Path(save_path).mkdir(parents=True, exist_ok=True)
    for data_version in data_list:
        print(data_version)
        for threshold in [0,0.01,0.02,0.05,0.1]:
            print('Threshold = '+str(threshold))
            #Read in the relevant data
            result = pd.read_csv(save_path+data_version+'_'+match_status+'_bypatient_allmethods.csv')
            #Filter only to algorithms in the algorithms list
            result =result.loc[result['Algorithm'].isin(algorithm_list)]             
            # result.set_index(['ID','Algorithm'], inplace = True)
            pred_results = pd.read_csv(save_path+data_version+'_'+match_status+'_performance_allmethods.csv')
            pred_results.set_index('Algorithm', inplace = True)
            #Predictive performance table to base decisions from
            pred_perf_results = pd.read_csv(save_path+'train'+'_'+match_status+'_performance_allmethods.csv')
            pred_perf_results.set_index('Algorithm', inplace = True)
            #Compare different schemes
            schemes = ['no_weights']
            # schemes = ['weighted','no_weights']
            for weighted_status in schemes:
                print("Prescription scheme = ", weighted_status)
                ## Get summary by patient
                if weighted_status == 'weighted':
                    summary = pd.DataFrame(index = result['ID'].unique())
                    for col in treatment_list:
                        pred_auc = pred_perf_results.loc[:,col].rename('AUC', axis = 1)
                        result_join = result.merge(pred_auc, on = 'Algorithm').groupby('ID').apply(u.wavg, col, 'AUC')
                        summary = pd.concat([summary,result_join.rename(col)], axis = 1)
                    # if threshold == 0:
                    #     summary['Prescribe'] = summary.idxmin(axis=1)
                    #     summary['AverageProbability'] = summary.min(axis=1)
                    #     summary['Benefit'] = summary.apply(lambda row: (row['NO_'+treatment] -  row[treatment])/row['NO_'+treatment], axis = 1)
                    # else: 
                    summary['NO_'+treatment] = summary['NO_'+treatment].replace(0,1e-4)
                    summary['Benefit'] = summary.apply(lambda row: (row['NO_'+treatment] -  row[treatment])/row['NO_'+treatment], axis = 1)
                    summary['Prescribe'] = summary.apply(lambda row: treatment if row['Benefit'] > threshold else 'NO_'+treatment, axis = 1)
                    summary['AverageProbability'] = summary.apply(lambda row: row[row['Prescribe']], axis = 1)        
                    summary = pd.concat([summary, Z, y],axis=1)
                    summary['Match'] = [x.replace(' ','_') == y for x,y in zip(summary['REGIMEN'], summary['Prescribe'])]
                    summary.to_csv(save_path+data_version+'_'+match_status+'_bypatient_summary_'+weighted_status+'_t'+str(threshold)+'.csv')
                    n_summary = summary
                else:
                    result['NO_'+treatment] = result['NO_'+treatment].replace(0,1e-4)
                    result['Benefit'] = result.apply(lambda row: (row['NO_'+treatment] -  row[treatment])/row['NO_'+treatment], axis = 1)
                    result['Prescribe'] = result.apply(lambda row: treatment if row['Benefit'] > threshold else 'NO_'+treatment, axis = 1)
                    result['Prescribe_Prediction'] = result.apply(lambda row: row[row['Prescribe']], axis = 1)    
                    summary = pd.concat([result.groupby('ID')[treatment_list].agg({'mean'}),
                      result.groupby('ID')['Prescribe'].apply(
                          lambda x:  ', '.join(pd.Series.mode(x).sort_values())), Z, y], axis=1)
                    ## two treatments and 7 methods -- no ties
                    #Resolve Ties among treatments by selecting the treatment whose models have the highest average AUC
                    summary['Prescribe_list'] =   summary['Prescribe'].str.split(pat = ', ')
                    summary = u.resolve_ties(summary, result, pred_perf_results)
                    summary['Match'] = [x.replace(' ','_') == y for x,y in zip(summary['REGIMEN'], summary['Prescribe'])]
                    merged_summary = u.retrieve_proba_per_prescription(result, summary, pred_perf_results)
                    merged_summary.to_csv(save_path+data_version+'_'+match_status+'_detailed_bypatient_summary_'+weighted_status+'_t'+str(threshold)+'.csv')
                    #Add the average probability and participating algorithms for each patient prescription
                    d1 = merged_summary.groupby('ID')['Prescribe_Prediction'].agg({'mean'})
                    d2 = merged_summary.reset_index().groupby('ID')['Algorithm'].apply(
                                  lambda x:  ', '.join(pd.Series(x))).to_frame()        
                    n_summary = pd.merge(summary, d1, left_index=True, right_index=True)
                    n_summary = pd.merge(n_summary, d2, left_index=True, right_index=True)
                    n_summary.rename(columns={"mean":"AverageProbability"},inplace=True)
                    n_summary.to_csv(save_path+data_version+'_'+match_status+'_bypatient_summary_'+weighted_status+'_t'+str(threshold)+'.csv')
                #
                prescription_summary = pd.crosstab(index = summary.Prescribe, columns = summary.Match, 
                                               margins = True, margins_name = 'Total')
                prescription_summary.columns = ['No Match', 'Match', 'Total']
                prescription_summary.drop('Total',axis=0)
                prescription_summary.sort_values('Total', ascending = False, inplace = True)
                prescription_summary.to_csv(save_path+data_version+'_'+match_status+'_bytreatment_summary_'+weighted_status+'_t'+str(threshold)+'.csv')
                #
                 # ===================================================================================
                # Calibration Evaluation
                # We will create calibration plots: line plots of the relative frequency of what was observed (y-axis) versus the predicted probability frequency  (x-axis).
                # The better calibrated or more reliable a forecast, the closer the points will appear along the main diagonal from the bottom left to the top right of the plot.
                # ===================================================================================
                u.simple_calibration_plot(n_summary,  outcome, save_path, data_version, match_status, weighted_status, threshold)
                # ===================================================================================
                # Prescription Effectiveness
                # We will show the difference in the percent of the population that survives.
                # Prescription Effectiveness compares the outcome with the algorithm's suggestion versus what happened in reality
                # ===================================================================================
                #Calculate the baseline mortality rate on the training set.
                orig_data_path = '../../covid19_treatments_data/matched_single_treatments_der_val_addl_outcomes/'         
                X_train, Z_train, y_train = u.load_data(orig_data_path,training_set_name,
                                split='train', matched=matched, prediction = outcome)

                PE = n_summary['AverageProbability'].mean() - n_summary[outcome].mean()
                pe_list = u.prescription_effectiveness(result, summary, pred_results,algorithm_list, y_train, calibration=False, prediction=outcome)
                #pe_list = u.prescription_effectiveness(result, summary, pred_results,algorithm_list,prediction=outcome)
                
                # ===================================================================================
                # Calibrated Prescription Effectiveness
                # We will show the difference in the percent of the population that survives.
                # Prescription Effectiveness compares the outcome with the algorithm's suggestion versus what happened in reality
                # ===================================================================================
                                
                n_summary['CalibratedAverageProbability'] = n_summary['AverageProbability']*(n_summary[outcome].mean()/y_train.mean())
                CPE = n_summary['CalibratedAverageProbability'].mean() - n_summary[outcome].mean()            
                cpe_list = u.prescription_effectiveness(result, summary, pred_results,algorithm_list,y_train, calibration=True, prediction=outcome)
                
                # ===================================================================================
                # Prescription Robustness
                # We will show the difference in the percent of the population that survives.
                # Prescription Robustness compares the outcome with the algorithm's suggestion versus a ground truth estimated by an algorithm
                # ===================================================================================
                # This is prescription robustness of the prescriptive algorithm versus reality, when reality is calculated by alternative ground truths
                PR = u.algorithm_prescription_robustness(result, n_summary, pred_results,algorithm_list,prediction=outcome)
                #
                # This is prescription robustness of the prescriptive algorithm versus reality when both decisions take as input alternative ground truths
                pr_table = u.prescription_robustness_a(result, summary, pred_results,algorithm_list,prediction=outcome)
                #
                #We can create a table and save all the results
                pr_table['PE'] = pe_list
                pr_table['CPE'] = cpe_list
                pr_min = np.diag(pr_table).min()
                pr_max = np.diag(pr_table).max()
                PR.append(PE)
                PR.append(CPE)
                pr_table.loc['prescr'] = PR
                pr_table.to_csv(save_path+data_version+'_'+match_status+'_prescription_robustness_summary_'+weighted_status+'_t'+str(threshold)+'.csv')
                #
                match_rate = n_summary['Match'].mean()
                average_auc = u.get_prescription_AUC(n_summary,prediction=outcome)
                print("Match Rate: ", match_rate)
                print("Average AUC: ", average_auc)
                print("PE: ", PE)
                print("PR Range: ", round(pr_max,3),  " - ", round(pr_min,3))
                #
                presc_count = sum(summary['Prescribe']==treatment)
                #
                metrics_agg.loc[len(metrics_agg)] = [data_version, weighted_status, threshold, 
                                                     match_rate, presc_count, average_auc, 
                                                     PE, pr_max, pr_min]
        metrics_agg.to_csv(save_path+data_version+'_'+match_status+'_metrics_summary.csv')
        
#%% Race distribution
data_full = pd.read_csv(data_path+'hope_hm_cremona_data_clean_imputed_addl_outcomes.csv')

data_full.groupby(['SOURCE_COUNTRY','RACE']).size()

#%% Compare PE metrics
weighted_status = 'no_weights'
strategy = 'quantile'
threshold = 0.01
summary = pd.read_csv(save_path+data_version+'_'+match_status+'_bypatient_summary_'+weighted_status+'_t'+str(threshold)+'.csv') 
summary.rename({"('ACEI_ARBS', 'mean')":'ACEI_ARBS', "('NO_ACEI_ARBS', 'mean')":'NO_ACEI_ARBS'}, axis=1, inplace = True)


PE = summary.AverageProbability.mean() - summary[outcome].mean()

## Use probabilities for baseline
summary['REGIMEN_Probability'] = summary.apply(lambda row: row[row['REGIMEN']], axis = 1)
summary['PRESCRIBE_Probability'] = summary.apply(lambda row: row[row['Prescribe']], axis = 1)

summary.REGIMEN_Probability.mean()  ## actual treatments
summary.PRESCRIBE_Probability.mean() ## prescriptions
summary.AverageProbability.mean() ## prescriptions (optimistic - only include methods that voted for prescription)
PE_prob1 = summary.PRESCRIBE_Probability.mean() - summary.REGIMEN_Probability.mean()
PE_prob2 = summary.AverageProbability.mean() - summary.REGIMEN_Probability.mean()

## Recalibrate probabilities based on validation event rate vs. baseline 
summary['CalibratedAverageProbability'] = summary['AverageProbability']*(summary[outcome].mean()/y_train.mean())
CPE = summary['CalibratedAverageProbability'].mean() - summary[outcome].mean()            
   
print("PE Original: " + str(round(PE,3)))
print("Calibrated PE: " + str(round(CPE,3)))
print("Probability-Based PE v1: " + str(round(PE_prob1,3)))
print("Probability-Based PE v2: " + str(round(PE_prob2,3)))
                
#%% Calibration plot           
summary_match = summary.query('Match == True')

# for model_type in model_types:
#     for model_lab in model_labs:

#         name = "Calibration Plot of "+model_type+" "+model_lab
#         y, y_pred, prob_pos = get_model_outcomes(model_type, model_lab, website_path, results_path)

plt.close()

fig_index=1


fig = plt.figure(fig_index, figsize=(10, 10))
ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2)
ax2 = plt.subplot2grid((3, 1), (2, 0))

ax1.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")

name = "Partners"

fraction_of_positives, mean_predicted_value = \
    calibration_curve(summary_match[outcome], summary_match['AverageProbability'], n_bins=10,
                      strategy = strategy)

model_score = brier_score_loss(summary_match[outcome], summary_match['AverageProbability'], pos_label=1)

ax1.plot(mean_predicted_value, fraction_of_positives, "s-",
         label="%s (%1.3f)" % (name, model_score))

ax2.hist(summary_match['AverageProbability'], range=(0, 1), bins=10, label=name,
         histtype="step", lw=2)

ax1.set_ylabel("Fraction of positives")
ax1.set_ylim([-0.05, 1.05])
ax1.legend(loc="lower right")
ax1.set_title('Calibration plots  (reliability curve)')

ax2.set_xlabel("Mean predicted value")
ax2.set_ylabel("Count")
ax2.legend(loc="upper center", ncol=2)

plt.tight_layout()
plt.savefig(save_path+data_version+'_'+match_status+'_'+weighted_status+'_t'+str(threshold)+'_calibration_plot_'+strategy+'.png')
            
            
            