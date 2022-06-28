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
# build_features.py
# Purpose: big query snippets used to build features

WITH = '''
with
'''

###################################################
def formatUnions(format_i):
    if format_i == 0:
        breakl = "\n"
        format_i += 1
    else:
        breakl = "\nUNION ALL\n"
        
    return format_i, breakl

###################################################
def buildDataFeatures(usedFeatures):
    Q = '''
dataFeatures as (
SELECT distinct ip, p, server FROM (
'''
    format_i = 0
    for f in usedFeatures:
        format_i, breakl = formatUnions(format_i)
        Q += (breakl + f)
        
    Q += "\n)),"
    return Q


###################################################
def buildSpatialFeatures(startSlash=16, endSlash=23, L4 = True, ASN = True):
    Q = '''
#extract all spatial (subnet+AS) features and assign to each ip/port
spatialFeatures as (
'''
    format_i = 0
    for i in range(startSlash, endSlash):

        format_i, breakl = formatUnions(format_i)
        
        q = 'SELECT ip, p, CONCAT("s' + str(i) + ': ",' + \
        'CAST(TO_HEX(NET.IP_TRUNC(NET.SAFE_IP_FROM_STRING(ip),'+str(i)+')) as string))'+ \
         'server FROM `{project}.{dataset}.{table}`'
            
        Q+= (breakl + q)
        
    if L4:
        format_i, breakl = formatUnions(format_i)
        q = 'SELECT ip,p, "L4" server FROM `{project}.{dataset}.{table}`'
        Q+=  (breakl + q)
        
    if ASN:
        format_i, breakl = formatUnions(format_i)
        q = 'SELECT ip, p, CONCAT("asn: ",asn) server FROM `{project}.{dataset}.{table}`'
        Q+=  (breakl + q)
        
    Q += "\n),"
    return Q 

###################################################
# input param spatialFeatures  is a subset of spatial features defined previously
# that will be crossjoined with all data features 
def buildCrossJoinFeatures(slashes = [16],ASN = True):
    Q = '''
#combine spatial with data features (interaction) and assign to each ip and port
crossJoinFeatures as (
'''
    format_i = 0
    for i in slashes:
        format_i, breakl = formatUnions(format_i)
        q = '(SELECT t1.ip, p, CONCAT("'+str(i)+':", t1.server,"-", t2.server' +\
        ')server FROM\n' +\
        '''(SELECT * FROM dataFeatures)t1
INNER JOIN
( SELECT DISTINCT ip, 
CAST(TO_HEX(NET.IP_TRUNC(NET.SAFE_IP_FROM_STRING(ip),
        ''' + str(i)+ ''' )) as string)
 server FROM `{project}.{dataset}.{table}`
 )t2
ON t1.ip = t2.ip )
        '''
        Q+=  (breakl + q)
    
    
    if ASN:
        format_i, breakl = formatUnions(format_i)
        q = '(SELECT t1.ip, p, CONCAT("asn:", t1.server,"-", t2.server' +\
        ')server FROM\n' +\
        '''(SELECT * FROM dataFeatures)t1
INNER JOIN
(SELECT DISTINCT ip, CONCAT("asn: ",asn) server FROM `{project}.{dataset}.{table}`)t2
ON t1.ip = t2.ip )
        '''
        Q+=  (breakl + q)
    
    Q += "\n),"
    return Q 

###################################################
# cant use this implementation as it queries spatialFeatures 
# and that leads to a too many resources big query error
# so must use the implementation where we query the original dataset...
# and re-make the spatial features....

# input param spatialFeatures  is a subset of spatial features defined previously
# that will be crossjoined with all data features 
def buildCrossJoinFeatures_Old(spatialFeatures = ["s16","asn"]):
    Q = '''
#combine spatial with data features (interaction) and assign to each ip and port
crossJoinFeatures as (
'''
    format_i = 0
    for f in spatialFeatures:
        format_i, breakl = formatUnions(format_i)
        q = '(SELECT t1.ip, p, CONCAT("'+str(f)+':", t1.server,"-", t2.server' +\
        ')server FROM\n' +\
        '''(SELECT * FROM dataFeatures)t1
INNER JOIN
(SELECT DISTINCT ip, server
FROM spatialFeatures 
where server = "''' +str(f)+':%"' +\
        ''' )t2
ON t1.ip = t2.ip )
        '''
        Q+=  (breakl + q)
    
    Q += "\n),"
    return Q 
    
    
