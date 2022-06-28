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

# get_predictions_algorithm.py
# Purpose: Use the predictive patterns table to extract predictions from the priors scan
# INPUT dataset: assume that real services (e.g., returned data) have been filtered for

GPS_BANNER_GET_PREDICTIONS = '''
#GPS: COLLECT PREDICTIONS
'''

GET_PREDICTIONS_ALGORITHM = ''' 
base as (

SELECT * FROM dataFeatures
UNION ALL
SELECT ip, p, server FROM spatialFeatures
UNION ALL
SELECT ip, p, server FROM crossJoinFeatures

),

#get the predictions
preds as (
SELECT ip, t2.p FROM
(SELECT DISTINCT ip, p, server FROM base)t1
INNER JOIN
(SELECT DISTINCT neededP, p, server 
FROM `{project}.{dataset}.{pred_table}`
where p is not null)t2
ON t1.p = t2.neededP and t1.server = t2.server
),

#filter what we have already scanned
filtpriors as (

SELECT t2.ip, t2.p FROM
(SELECT distinct CONCAT(NET.IP_TO_STRING(NET.IP_TRUNC(NET.IP_FROM_STRING(ip), {step})), "/", {step}) slash, p FROM
preds
EXCEPT DISTINCT
SELECT slash, neededP p
FROM `{project}.{dataset}.{prior_table}`)t1
INNER JOIN
(SELECT CONCAT(NET.IP_TO_STRING(NET.IP_TRUNC(NET.IP_FROM_STRING(ip), {step})), "/", {step}) slash,
ip, p
FROM preds)t2
ON t1.slash=t2.slash and t1.p=t2.p

),

filtseed as (

SELECT ip, p FROM
filtpriors 
EXCEPT DISTINCT 
SELECT ip, p FROM
`{project}.{dataset}.{seed_table}`

)

#make it lzr friendly
SELECT DISTINCT CONCAT(ip,":", p) service FROM 
filtseed
'''
