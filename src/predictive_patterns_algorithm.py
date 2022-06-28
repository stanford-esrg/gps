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

# predictive_patterns_algorithm.py
# Purpose: Compute the features that are most indicative of another service being present 
#          on an IP/Port
# INPUT dataset: assume that real services (e.g., returned data) have been filtered for


GPS_BANNER_PRED_PATTERNS = '''
#GPS: FINDING PREDICTIVE PATTERNS
'''

PREDICTIVE_PATTERNS_ALGORITHM = ''' 

# assign features for only hosts that have at least 2 ports open.
base as (
SELECT t2.* FROM

(
#FILTER BY hosts that resp < 11 ports. 99% of them are service sinks
SELECT ip FROM (
SELECT ip, COUNT(distinct p) c FROM `{project}.{dataset}.{table}`
GROUP BY ip
)
where c > 1 and c <11

)t1
INNER JOIN
(
SELECT * FROM dataFeatures
UNION ALL
SELECT ip, p, server FROM spatialFeatures
UNION ALL
SELECT ip, p, server FROM crossJoinFeatures
)t2
 ON t1.ip = t2.ip
),


#essentially do a cross join where we can analyze all pairs of services/features
pairs as (
SELECT distinct t1.ip, t1.p p1, t1.server p1_server, t2.p p2  FROM
(SELECT * FROM base )t1
INNER JOIN
(SELECT * FROM base  )t2
ON t1.ip = t2.ip 
where t1.p <> t2.p
),

#calculate the hitrates/correlations for every pair
found_corr as (
SELECT p1, p1_server, t1.p2, count_p2/ cp_server hitrate, count_p2, cp_server FROM
(SELECT p1, p1_server, p2, COUNT(*) count_p2 FROM
pairs
GROUP BY p1,p2,p1_server)t1
INNER JOIN
(SELECT p, server, COUNT(*) cp_server
FROM base
GROUP BY p, server 
 ) t2
ON t1.p1 = t2.p and t1.p1_server = t2.server
where count_p2 > 2 #for likelihood that pair will appear in any 1% scan 
),


meta as ( 
SELECT t1.ip, t1.p2 p, t1.p1 neededP, hitrate, count_p2,c, cp_server, p1_server FROM 

#assign back the correlations to ips that actually respond on those 2 ports
(SELECT t1.*,count_p2, hitrate,cp_server FROM 
(SELECT ip, p1,p2,p1_server FROM pairs)t1
LEFT OUTER JOIN
(SELECT p1, p2, hitrate,p1_server,count_p2, cp_server FROM found_corr)t2
ON t1.p1 = t2.p1 and t1.p2 = t2.p2 and t1.p1_server=t2.p1_server)t1
INNER JOIN
(
SELECT ip, COUNT(distinct p) c FROM `{project}.{dataset}.{table}`
GROUP BY ip
)t2
ON t1.ip = t2.ip

)

#combine most correlative features with services that only respond
#on one port and therefore do not have correlations

#select the best more correlative features
SELECT ip, p, neededP, count_p2, hitrate, cp_server, server FROM
(SELECT * FROM (
SELECT ip, p, ARRAY_AGG(neededP order by hitrate DESC, neededP,p1_server)[OFFSET(0)] neededP, 
ARRAY_AGG(count_p2 order by hitrate DESC, neededP,p1_server)[OFFSET(0)] count_p2, 
ARRAY_AGG(hitrate order by hitrate DESC, neededP,p1_server)[OFFSET(0)] hitrate,
ARRAY_AGG(cp_server order by hitrate DESC, neededP,p1_server)[OFFSET(0)] cp_server,
ARRAY_AGG(p1_server order by hitrate DESC, neededP,p1_server)[OFFSET(0)] server,
FROM

(SELECT ip, p,neededP, hitrate, count_p2,cp_server,p1_server FROM 
meta where c > 1) #save the information for all services that respond > 1 port. 
GROUP BY ip, p )
where hitrate > {hitrate})

UNION ALL

#IPs that only respond on one port
SELECT ip, null, p, null, null, null, null FROM
(SELECT t1.ip, p FROM 
(SELECT distinct ip,p FROM `{project}.{dataset}.{table}`)t1
INNER JOIN
(
SELECT distinct ip FROM (
SELECT ip, COUNT(distinct p) c FROM `{project}.{dataset}.{table}`
GROUP BY ip
)
where c = 1)t2
ON t1.ip = t2.ip)
'''
