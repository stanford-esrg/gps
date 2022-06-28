# GPS: Predicting IPv4 Services Across All Ports

GPS predicts IPv4 services across all 65K ports. 
GPS works with scanners such as [LZR](https://github.com/stanford-esrg/lzr) and relies on Google [BigQuery](http://bigquery.cloud.google.com) to compute predictions.

To learn more about GPS' system and performance, check out the original [paper] appearing at [Sigcomm '22](https://conferences.sigcomm.org/sigcomm/2022/).

## GPS Computational Requirements

In this repository we provide a GPS implementation which uses Google BigQuery as its back-end.

To run GPS, you need the following capabilities:
- Access to Google Big Query
- Access to Internet scanning infrastructure

## Configuring GPS Parameters

Config file
The beginning of main.py specifies multiple todos in which the user
is expected to spectify their Big Query account, the BQ dataset they plan to use,
the table name to which the seed scan was uploaded, where intermediate data is to
be stored, as well as other GPS configurations. 

## Running GPS

GPS prediction works in two phases:
(1) GPS predicts at least one service across all hosts.
(2) GPS predicts all remaining services on every host it has discovered in the first phase.


Thus, the user must specify which phase of GPS to run:

```
python gps.py first
```
or 
```
python gps.py remaining
```


## Seed Scan Input:

We provide in the data/ foler a sample seed scan (1% ipv4 lzr scan across all 65K ports) collected in April 2021. The seed scan has been filtered for real services (i.e., services that send back real data) and hosts that respond on 10 or less ports (i.e., removing pseudo services). Please see the LZR paper and the GPS paper for more details behind this methodology. 
#### todo add section numbers

To use this seed scan, upload it to BigQuery and update the seed table name in main.py.
You can use the following command-line big query command:

bq load --source_format NEWLINE_DELIMITED_JSON --autodetect \
      BQ_RESOURCE_PROJECT.BQ_DATASET.SEED_TABLE lzr_seed_april2021_filt.json



The dataset should just be used for testing purposes.
Using this data means that GPS will predict services given the state of the Internet from April 2021. 
To make up-to-date predictions, please use an up-to-date seed scan. 
#### todo add section numbers for size of a seed scan


### When using your own seed scan:

The code base currently supports two formats of Interent scans to be used as the seed:
(1) The raw output of a LZR scan. GPS then re-formats it as a "step 0"
or
(2) An already correctly formatted scan. GPS expects the following format:
ip (string), p (port number- integer), asn (integer), data (string), fingerprint (protocol - string), w (tcp window size-integer).

At minimum, the gps algorithm expects ip, p, data.

Note that fields can be added or removed, but the appropriate features should be added or removed as well in main.py: 

usedFeatures = [TLS_OID, TLS_CERT, HTTP_LINES, FINGERPRINT, WINDOW, SSH]
Each of those features are defined in data_features.py

If removing the ASN feature, then set useASN to false in main.py. 




## Debugging

When adding functionality to GPS, the user may run into the following Big Query errors: 

``400 Resources exceeded during query execution: Not enough resources for query planning - too many subqueries or query is too complex.''
    
Why it happened: This message means that the query has become too long/nested for BigQuery to process. 
This can happen if you have added more features, or added more code that calls the defined sub-tables.

Solution: Reduce the amount of queries that are defined as sub-tables. Or split the query in two and run them seperately (saving to a destination table in the process. 



## License and Copyright

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
