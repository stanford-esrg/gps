# GPS: Predicting IPv4 Services Across All Ports

GPS predicts IPv4 services across all 65K ports. 
GPS uses application, transport, and network layer features to probabilistically model and predict service presence.
To scan the predicted services, GPS relies on existing Internet scanners such as [LZR](https://github.com/stanford-esrg/lzr).
To compute predictions, this implementation of GPS uses Google [BigQuery](http://bigquery.cloud.google.com). 

To learn more about GPS' system and performance, check out the original [paper] appearing at [Sigcomm '22](https://conferences.sigcomm.org/sigcomm/2022/).

## GPS Computational Requirements

In this repository we provide a GPS implementation in python that uses Google BigQuery as its back-end computing source.

To run GPS, you need the following capabilities:
- Python v3
- Access to Google [BigQuery](http://bigquery.cloud.google.com) and the [google cloud command line](https://cloud.google.com/sdk/docs/install).
Users are responsible for their own billing. 
As long as intermediate tables are not stored in Google BigQuery for longer than GPS' execution, then the total cost of running GPS on BigQuery should be less than \$1. 
- Access to an Internet scanner (e.g.,[LZR](https://github.com/stanford-esrg/lzr)) and Internet scanning infrastructure. Please make sure to adhere to [these](https://github.com/zmap/zmap/wiki/Scanning-Best-Practices) scanning best practices.
- Access to a large disk (e.g., 1TB). The final list of service predictions generates a file that is larger than half a terabyte in size. 

## Configuring GPS Parameters

GPS uses a `config.ini` configuration file which expects users to specify:
1. a Big Query account
2. an existing BQ dataset that GPS can store tables to
3. the table name to which the seed scan was uploaded to (see below)
4. a local directory of where GPS can store predictions
5. other GPS parameters (e.g., minimum hitrate)


## Seed Scan:

GPS relies on an initial seed scan---a sub-sampled (e.g., 1\%) IPv4 scan across all 65K ports---to learn patterns from. 
A sample seed scan (1\% IPv4 LZR scan across all 65K ports collected in April 2021) can be found [here].
The seed scan has been filtered for real services (i.e., services that send back real data) and hosts that respond on 10 or less ports (i.e., removing pseudo services). 
Please see the [LZR paper](https://lizizhikevich.github.io/assets/papers/lzr.pdf) and the GPS paper for more details behind this methodology. 

The sample seed scan should just be used for testing purposes.
Using this data means that GPS will predict services given the state of the Internet from April 2021. 
To make up-to-date predictions, please use an up-to-date seed scan. 

To use the sample seed scan, upload it to BigQuery and update the seed table name in `config.ini`.
You can use the following command-line big query command:
```
bq load --source_format NEWLINE_DELIMITED_JSON --autodetect \
      BQ_RESOURCE_PROJECT.BQ_DATASET.SEED_TABLE lzr_seed_april2021_filt.json
```

### Using your own seed scan:

The GPS code base currently supports two formats of Interent scans to be used as the seed:
1. The raw output of a [LZR](https://github.com/stanford-esrg/lzr) scan. 
GPS then re-formats it when ``Pre_Filt_Seed=False`` is set in the config.ini. 
3. A scan with the following schema:
```
ip (string), p (port number- integer), asn (integer), data (string),\
fingerprint (protocol - string), w (tcp window size-integer).
```
Fields can be added or removed, as long as ``src/data_features.py`` is appropriately updated. 
At minimum, to compute predictions, the gps algorithm expects an ip address, a port number, and some form of layer 7 data for each service.

## Running GPS

Once the ``config.ini`` is properly set, and a valid seed scan has been uploaded to BigQuery, GPS is ready to predict services.

GPS prediction works in two phases:

1. GPS predicts at least one service across all IPv4 hosts. 
To run GPS' first phase, simply run the following:
``python gps.py first``
GPS outputs and downloads locally a short list of sub-networks and ports for the user to scan.

3. GPS predicts any remaining services on every host it has discovered in the first phase. 
To run GPS' second phase, simply run the following:
``python gps.py remaining``
GPS saves a large list of individual services for the user to scan. 
During runtime, GPS provides user instructions for how to best download that large list.

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
