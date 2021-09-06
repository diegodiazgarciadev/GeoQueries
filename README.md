# GeoQueries

## Introduction

We recently created a new company in the GAMING industry. The company will have the following scheme:

20 Designers , 5 UI/UX Engineers ,10 Frontend Developers , 15 Data Engineers , 5 Backend Developers, 20 Account Managers, 1 Maintenance guy that loves basketball, 10 Executives, 1 CEO/President

We need to choose 3 locations in the world and decide which one is the best one to locate our new company.

## Goal 

My goal  in this project has been, in addition to complying with the specifications, to try to create a clean and modular code, in such a way that instead of having to take fixed values of cities, to be able to do it dynamically and through the user interface.

## Considerations

The parameters below has been the ones that we have selected as importants for our company workers and the ones that we will be searching on foursquare API:
 
 "vegan", "Startup", "nursery school", "school", "pubs", "starbucks", "train", "dog grummer"
 
We didn't use the basketball as a search parameter as we don't consider that is importat for our company.

Because we are not a selfish company we don't want to choose what is the most importat parameter, so what we have decided is to create a poll (not necessarily on friday, this time) where every worker in the company will be able to give the weight/mark to every parameter. 
The sad thing is We don't have time for that but we have create a function that will give us that info for every worker (using the dirichlet distribution)

The distance will be our principal measure, so we will take distances from all the places we want to have near by our company. After taking a look to the distances, and taken just the 3 distances closer to our company we have checked some places (mostly the 3rd less close) are really far comparing with the other, so we have decided just take the closer place for every parameter.

Because we are getting the cities dinamically, we don't want to do a cleaning or to pay close attention to the info of the selected cities. We are trying to create the more general code so that we could use it for other locations.


## Workflow

* The user will be asked for a database name for creating it or to laad an existing one. 
* The user will be asked to introduce 3 cities ( the user could set any location)
* We will delete all collections in our database, so we will start with a clean and empty data base
* Then we create structures for the 3 differents cities, which means:
    * We call the foursquare API and we create a json with the ino of all the search parameters for every city (**dic_json_api_response_for_city**) 
    * We reduce the json taking only the parameters we need and creating correctly the locaction attribute we will need for the GEOQUERIES. In summary we prepare the json to laad it in mongo (**build_dic_json_to_mongo**)
    * We create the collecions on MongoDB, we create json files (just in case we need it in the future) and we create the geo indexes (**create_collections_in_mongo**)

* Then we will be creating a Data Frame of distances between our cities and every parameter on the search list.
     * We will be creating an aggration query **create_query_distances**
     * This query will be call for every of the parameters in each city crearing a list of jsons **create_dict_distances**
     * Then with the info of all the distances between every parameter in a city we will create a list of json just taken the elemens with less distance to our base point (in this case the 3 firsts)
    * Finally we will create DataFrames for every city with this info . We will use it in the map and for calculating our marks

* After that, we will add the value column which will give us the total value of every city:
  * We will calculate the weights of every parameter in calculate_marks_mean function:
  * This fucntion will simulate polls where every worker on the company will give a weight to every parameter
  * Then we will do the mean of all theses weights, and we will have our total weights for every parameter
  * We will add this info to a new column percentage
 *Because we don't want big distances values adulterate our final value, we will take logarithm to the distances columns to minimize this circumstance. We will create a new column for that (log)
 * Finally we will multiply the log column with the weights columns, and we will have our value column , and  just doing a sum() of our value column which will give as the final mark to compare the different cities, the minimum mark will be the winner.






## Conclusions

For this example I have used 3 locations where I have worked, so there are 3 technological Park (England, Spain, Belgium).

This is our output: 

![image](https://user-images.githubusercontent.com/82879300/132257088-7eab4a0a-b840-4d7a-ba4f-321edff08ad0.png)



The winner will be the one with less value, in this case Brussels (diegem), and we can see the map created wiht folium below


![image](https://user-images.githubusercontent.com/82879300/132257610-2841cd67-d2f3-4271-b5ba-2b3caf199a30.png)





