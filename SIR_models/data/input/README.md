# Input Data
This is where all the data that can be implemented in the code is located.


## Age Distribution
This folder contains tsv/csv files with age groupings.

###### CanadaPopulation2020.csv
This is a file with the population of Canada by province. It has data from January of 2020 as well as April of 2020. 

###### KingstonPopulation.tsv
This is a file with the population of Kingston divided into five year age groupings and subdivided into male and female populations within those age groupings.

This data is from the 2016 census recorded by Statistics Canada.
http://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/index.cfm?Lang=E

## Case Data
This folder contains data that has to do with covid cases, such as case severity, time periods for incubation, recovery, etc.

###### covid_cases_by_severity.csv
This file contains a distribution of covid cases by severity (hospitalized, ICU, death). The severity of the case also impacts the period of transmission - more severe cases remain infectious for longer.

This data is from the paper titled: Enhanced Epidemiological Summary COVID-19 and Severe Outcomes in Ontario.
https://www.publichealthontario.ca/-/media/documents/ncov/epi/covid-19-severe-outcomes-ontario-epi-summary.pdf?la=en

###### TimePeriods.csv
This file contains time period for different characteristics of covid cases, such as:

Incubation period - the time between contracting the virus and showing symptoms 
(Sources: 
Early Transmission Dynamics in Wuhan, China, of Novel Coronavirus–Infected Pneumonia https://www.nejm.org/doi/10.1056/NEJMoa2001316 
Coronavirus disease (COVID-19): Summary of assumptions https://www.canada.ca/en/public-health/services/diseases/2019-novel-coronavirus-infection/health-professionals/assumptions.html#a2 )

Recovery period - the time from onset to recovery from disease (not necessarily the same as infectious period, since symptoms typically outlast infectiousness)
(Source: Report of the WHO-China Joint Mission on Coronavirus Disease 2019 (COVID-19)  https://www.who.int/docs/default-source/coronaviruse/who-china-joint-mission-on-covid-19-final-report.pdf )

Infectious period - the maximum number of days that transmission is possible (viral RNA is still able to replicate - viral RNA is still present in patients long after they have recovered, but after the infectious period, it is no longer able to repliacte and can therefore not be transmitted to another person). The infectious period is different depending on the severity of the case.
(Sources:
Duration of Isolation and Precautions for Adults with COVID-19 https://www.cdc.gov/coronavirus/2019-ncov/hcp/duration-isolation.html?CDC_AA_refVal=https%3A%2F%2Fwww.cdc.gov%2Fcoronavirus%2F2019-ncov%2Fcommunity%2Fstrategy-discontinue-isolation.html
Virological assessment of hospitalized patients with COVID-2019 https://www.nature.com/articles/s41586-020-2196-x )

Immunity period - not yet added, but hopefully will be as more data is gathered - currently, only an estimate of 90 days is availible, which is based on related endemic human betacoronavirus. Currently, no reinfection has been definitively confirmed in any recovered persons.


## Epidemiological Characteristics

###### EpidemiologicalCharacteristics.tsv
This file contains data about confirmed cases and deaths relating to different characteristics such as age (10 year groupings), sex, occupation, preexisting condition, etc.

This data is from China, from 2019 - 2020.


## Kingston Data
This folder contains data from Kingston relating to characteristics of people from the 2016 census (Statistics Canada - https://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/details/page.cfm?Lang=E&Geo1=CMACA&Code1=521&Geo2=PR&Code2=35&SearchText=Kingston&SearchType=Begins&SearchPR=01&B1=All&GeoLevel=PR&GeoCode=521&TABID=1&type=0).

###### Occupation_data.csv
This file contains the population of Kingston separated into categories based on occupation, and subdivided by gender. Different occupations likely have different exposure levels to virus, e.g. section 3 (health occupations) and section 6 (sales and service occupations) would likely contain more essential workers, increasing contact with people and exposure to the virus.

This data is from the 2016 Census Profile for Kingston (Statistics Canada).

###### commuting_data.csv
This file contains commuting data for the population of Kingston - the number of people commuting divided by mode of commuting as well as by commuting duration. Those commuting by public transit and with a longer commuting duration would be at an increased risk of contracting the virus. 

This data is from the 2016 Census Profile for Kingston (Statistics Canada).

###### household_data.csv
This file contains the population of Kingston divided by type of house/dwelling as well as the number of people in each household.

This data is from the 2016 Census Profile for Kingston (Statistics Canada).



## Census Data for Ontario and Kingston
Master sheet with census data for both Ontario and Kingston, includes categories above.
