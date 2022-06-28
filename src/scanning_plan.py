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

#scanning_plan.py
#get scanning plan using specified step stize

import math

###################################################
GPS_BANNER_GET_PRIORS = '''
#GPS: COLLECTING PRIORS
'''

###################################################
def buildScanningPlan(project, dataset, table, hitrate, STEP=16):
        
    Q = '''
SELECT neededP, slash FROM (
SELECT neededP, 
CONCAT(NET.IP_TO_STRING(NET.IP_TRUNC(NET.IP_FROM_STRING(ip), {step})), "/", {step}) slash, 
COUNT(*) c 
FROM `{project}.{dataset}.{table}`
GROUP BY neededP, slash
)
where c/POW(2,32-{step}) > {hitrate}
ORDER BY c DESC
'''
    
    Q = Q.format(step=STEP,
                 project=project,\
                 dataset=dataset,\
                 table=table,\
                 hitrate=hitrate)

    return Q 


###################################################
#given a scanning plan, how many packets will be sent
def calcBandwidthNeeded(scanning_plan_df,step):
    
    #extract the size of subnet
    numSlashes = len(scanning_plan_df.index)
    
    return math.pow(2,32-step)*numSlashes
