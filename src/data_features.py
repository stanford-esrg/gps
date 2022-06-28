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

# data_features.py
# Purpose: Extract data features
# If adding new features:
# 1. Create definition
# 2. Add to features array


TLS_OID = '''
# extract oid from tls certs and assign as feature to each ip and port
SELECT DISTINCT ip,p, CONCAT("tls oid: ", tls_server) server FROM (
SELECT ip, p, tls_server FROM (
SELECT ip,p, iscan_alg.ExtractOIDTLS(data) oids FROM `{project}.{dataset}.{table}`
where fingerprint = "tls"
), UNNEST(oids) tls_server
)
where LENGTH(tls_server) >7 #for computation reasons - only keep larger potential oids
'''

HTTP_LINES = '''
# extract every line in the http payload and assign as feature to each ip and port
SELECT ip, p, CONCAT("http line: ",http_line) server FROM (
SELECT ip, p, asn, SPLIT(data,"\\n") http_split FROM `{project}.{dataset}.{table}`
), UNNEST(http_split) http_line

'''

TLS_CERT = '''
SELECT ip,p,CONCAT("tls cert: ", iscan_alg.ExtractTLSCert(data)) cert FROM `{project}.{dataset}.{table}`
where fingerprint = "tls"
'''

FINGERPRINT = '''
SELECT ip,p, CONCAT("fingerprint: ", fingerprint) server FROM `{project}.{dataset}.{table}`
'''

WINDOW = '''
SELECT ip,p, CONCAT("window: ",CAST(w as string)) server FROM `{project}.{dataset}.{table}`
'''

SSH = '''
SELECT ip,p, CONCAT("ssh banner: ",data) server FROM `{project}.{dataset}.{table}`
where fingerprint = "ssh" 
'''

FEATURES = [TLS_OID, TLS_CERT, HTTP_LINES, FINGERPRINT, WINDOW, SSH]
