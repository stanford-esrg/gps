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

# format_lzr.py
# Purpose: to format raw lzr scans to use the correct column names
#          and filter for real services that return data

GPS_BANNER_FORMAT_LZR = '''
#GPS: FORMAT LZR
'''


FORMAT_LZR = ''' 

SELECT distinct saddr ip, sport p, zannotate.routing.asn asn, 
data, fingerprint, `window` w FROM  `{project}.{dataset}.{table}`
where data <> "" and data is not null and RST is false and `window` <> 0

'''


