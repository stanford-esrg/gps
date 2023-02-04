''' 
Copyright 2020 The Board of Trustees of The Leland Stanford Junior University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import pandas as pd
import db_dtypes
import math
import configparser
import sys
from google.cloud import bigquery

from src.BQ_interaction import *
from src.build_features import *
from src.data_features import *
from src.format_lzr import *
from src.get_predictions_algorithm import *
from src.predictive_patterns_algorithm import *
from src.scanning_plan import * 


###################################################
#GPS: Predicting first or remaining services?
###################################################

def error_mes():
    print("------Command line parsing failed!")
    print("------Expecting one of the following command line arguments:")
    print("------'first': predict first service across hosts (phase 1)")
    print("------or")
    print("------'remaining': predict all remaining services (phase 2)")
    print("------Aborting.")
    sys.exit()

if len(sys.argv) != 2:
    error_mes()

gps_part = sys.argv[1]
if gps_part not in ['first','remaining']:
    error_mes()

GPS_PART1 = False
if gps_part == 'first':
    GPS_PART1 = True

###################################################
#Read Config
###################################################

config = configparser.ConfigParser()
config.read('config.ini')

BQ_RESOURCE_PROJECT = config['BigQuery']['BQ_Resource_Project']
BQ_DATASET = config['BigQuery']['BQ_Dataset']
SEED_TABLE = config['BigQuery']['Seed_Table']

DATAPATH = config['GPS']['Datapath'] 

HITRATE= config['GPS']['Hitrate']
STEP_SIZE=config['GPS']['Step_Size']
PRE_FILT_SEED=eval(config['GPS']['Pre_Filt_Seed'])
PRE_FILT_PRIORS=eval(config['GPS']['Pre_Filt_Priors'])

useASN = eval(config['Features']['UseASN'])


###################################################
#Begin GPS Algorithm
###################################################

BQ_CLIENT = bigquery.Client(project=BQ_RESOURCE_PROJECT)
print('Authenticated')

#**************************************************
#********GPS variables 
#**************************************************

FILT_TABLE = SEED_TABLE + '-formatted'
PRED_PATTERNS_TABLE = SEED_TABLE + "-predictivepatterns"
PRIORS_SCAN_TABLE = SEED_TABLE + "-priors"
SCANNING_PLAN_TABLE = SEED_TABLE + "-scanningplan"
PRIORS_SCAN_FILT_TABLE = PRIORS_SCAN_TABLE + "-formatted"
PRED_RESULTS_TABLE = SEED_TABLE + "-predictionresults"
SCANNING_PLAN=DATAPATH+"priors_scan_"


#**************************************************
#********Format Uploaded Scan (Assuming its a LZR scan)
#**************************************************

if not PRE_FILT_SEED:
    if GPS_PART1:
        print("------optionally formating lzr scan...")
        print("------saving to BQ table " + FILT_TABLE)

        FORMAT_LZR_QUERY = GPS_BANNER_FORMAT_LZR + FORMAT_LZR

        FORMAT_LZR_QUERY = FORMAT_LZR_QUERY.format(project=BQ_RESOURCE_PROJECT,\
                                           dataset=BQ_DATASET,\
                                           table=SEED_TABLE)

        run_bq_query(FORMAT_LZR_QUERY,BQ_RESOURCE_PROJECT,\
             BQ_DATASET, FILT_TABLE)
        print("------done w/ BigQuery.")

else:
    FILT_TABLE = SEED_TABLE

#**************************************************
#********Extract features and build predictive patterns table
#**************************************************
if GPS_PART1:

    print("------extracting features and building predictive patterns table...")
    print("------saving to BQ table " + PRED_PATTERNS_TABLE)

    PREDICTIVE_PATTERNS_QUERY = WITH + GPS_BANNER_PRED_PATTERNS + \
        buildDataFeatures(FEATURES) + \
        buildSpatialFeatures(startSlash=16, endSlash=23, L4 = True, ASN = useASN)+\
        buildCrossJoinFeatures(slashes = [16],ASN = useASN) +\
        PREDICTIVE_PATTERNS_ALGORITHM
        
    PREDICTIVE_PATTERNS_QUERY = PREDICTIVE_PATTERNS_QUERY.format(project=BQ_RESOURCE_PROJECT,\
                                           dataset=BQ_DATASET,\
                                           table=FILT_TABLE,\
                                           hitrate=HITRATE)

    run_bq_query(PREDICTIVE_PATTERNS_QUERY,BQ_RESOURCE_PROJECT,\
             BQ_DATASET, PRED_PATTERNS_TABLE)
    print("------done w/ BigQuery.")


#**************************************************
#********Generate scanning plan
#********can try out different ones to see which fits bandwidth budget
#**************************************************

if GPS_PART1:
    for STEP in [STEP_SIZE]:
    
        SCANNING_PLAN_CSV = SCANNING_PLAN+str(STEP)+".csv"

        print("------building priors scanning plan to predict first service across all IPs...")
        print("------saving locally at "+ SCANNING_PLAN_CSV)
    
    
        GET_PRIORS_SCAN_QUERY = buildScanningPlan(project=BQ_RESOURCE_PROJECT,\
                                    dataset=BQ_DATASET,\
                                    table=PRED_PATTERNS_TABLE,\
                                    hitrate=HITRATE, \
                                    STEP=STEP)
    
        GET_PRIORS_SCAN_QUERY = GPS_BANNER_GET_PRIORS + GET_PRIORS_SCAN_QUERY

        scanning_plan_df = run_bq_query(GET_PRIORS_SCAN_QUERY,BQ_RESOURCE_PROJECT,\
                                    BQ_DATASET, SCANNING_PLAN_TABLE, SAVE=True)
        print("------done w/ BigQuery.")
        scanning_plan_df.to_csv(SCANNING_PLAN_CSV, index=False, header=False)
        print("Here is a snippet of the scanning plan: ")
        print(scanning_plan_df)
        print("Packets that will be sent: ", calcBandwidthNeeded(scanning_plan_df,STEP))



#**************************************************
#********Run scanning plan scan
#**************************************************
if GPS_PART1:
    print("------Internet scan all the services in the scanning plan list")
    #upload scanning plan scan to big query under the PRED_PATTERNS_TABLE name
    print("------Then upload the results of the scan under the following table name: "+\
         PRIORS_SCAN_TABLE )
    print("------Using the following bash command: ")
    print("------bq load --source_format NEWLINE_DELIMITED_JSON --autodetect "+
      BQ_RESOURCE_PROJECT+"."+BQ_DATASET+"."+ PRIORS_SCAN_TABLE+ " data.json")

    print("------Once scanning plan is executed and uploaded to BQ, run:")
    print("------python gps.py remaining")
    sys.exit()
#**************************************************
#********Format priors scan
#**************************************************

if not PRE_FILT_PRIORS:
    if not GPS_PART1:
        print("------optionally formating lzr scan...")
        print("------saving to BQ table " + PRIORS_SCAN_FILT_TABLE)


        FORMAT_LZR_QUERY = GPS_BANNER_FORMAT_LZR + FORMAT_LZR

        FORMAT_LZR_QUERY = FORMAT_LZR_QUERY.format(project=BQ_RESOURCE_PROJECT,\
                                           dataset=BQ_DATASET,\
                                           table=PRIORS_SCAN_TABLE)

        run_bq_query(FORMAT_LZR_QUERY,BQ_RESOURCE_PROJECT,\
             BQ_DATASET, PRIORS_SCAN_FILT_TABLE)
        print("------done w/ BigQuery.")

else:
    PRIORS_SCAN_FILT_TABLE=PRIORS_SCAN_TABLE

#**************************************************
#********Get final predictions
#**************************************************

if not GPS_PART1:
    print("------Building final predictions")
    print("------saving to BQ table " + PRED_RESULTS_TABLE)
    GET_PREDICTIONS_QUERY = WITH + buildDataFeatures(FEATURES) + \
        buildSpatialFeatures(startSlash=16, endSlash=23, L4 = True, ASN = True)+\
        buildCrossJoinFeatures(slashes = [16],ASN = True) +\
        GET_PREDICTIONS_ALGORITHM


    GET_PREDICTIONS_QUERY = GPS_BANNER_GET_PREDICTIONS + GET_PREDICTIONS_QUERY

    GET_PREDICTIONS_QUERY = GET_PREDICTIONS_QUERY.format(project=BQ_RESOURCE_PROJECT,\
                                           dataset=BQ_DATASET,\
                                           table=PRIORS_SCAN_FILT_TABLE,\
                                           step=STEP_SIZE,\
                                           pred_table=PRED_PATTERNS_TABLE,\
                                           seed_table=FILT_TABLE,\
                                           prior_table=SCANNING_PLAN_TABLE)

    #saving the results to a destination table b/c the list is going to be large
    run_bq_query(GET_PREDICTIONS_QUERY,BQ_RESOURCE_PROJECT,\
             BQ_DATASET, PRED_RESULTS_TABLE)
    print("------done w/ BigQuery.")
    print("------To download run two commands:")
    print("------bq extract --destination_format CSV --field_delimeter , " +\
             "--print_header=false " +  BQ_RESOURCE_PROJECT+"."+BQ_DATASET+"."+ \
            PRED_RESULTS_TABLE + "gs://bucket/filename.csv")
    print("------gsutil cp gs://bucket/filename.csv " + DATAPATH )  
    print("------Then Internet scan all the services in the prediction results list")
	print("!!!!!!Remember to eventually delete the generated GPS tables from BigQuery!!!!!!")  
    sys.exit()

