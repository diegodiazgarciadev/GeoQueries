import requests
from functools import reduce
import operator
import json
import pymongo
import pandas as pd
import numpy as np
from folium import Choropleth, Circle, Marker, Icon, Map
from geopy.geocoders import Nominatim
from pymongo import MongoClient

# TODO comment every function
def call_api_foursquare (query, coordinates, url_query, client_id, client_secret ):
    parametros = {
        "client_id": client_id,
        "client_secret": client_secret,
        "v": "20220209",
        "ll": f"{coordinates[0]},{coordinates[1]}",
        "query": query,
        "limit": 200
    }
    resp = requests.get(url_query, params=parametros).json()["response"]["groups"][0]["items"]
    return resp


def json_api_to_dic(city_coordiantes, language, url_query, client_id, client_secret):
    json_vegan = call_api_foursquare(language[0], city_coordiantes, url_query, client_id, client_secret)
    json_startup = call_api_foursquare(language[1], city_coordiantes, url_query, client_id, client_secret)
    json_guarderias = call_api_foursquare(language[2], city_coordiantes, url_query, client_id, client_secret)
    json_colegios = call_api_foursquare(language[3], city_coordiantes, url_query, client_id, client_secret)
    json_discotecas = call_api_foursquare(language[4], city_coordiantes, url_query, client_id, client_secret)
    json_starbucks = call_api_foursquare(language[5], city_coordiantes, url_query, client_id, client_secret)
    json_train_station = call_api_foursquare(language[6], city_coordiantes, url_query, client_id, client_secret)
    json_peluqueria = call_api_foursquare(language[7], city_coordiantes, url_query, client_id, client_secret)

    return {
        "vegan_restaurant": json_vegan,
        "startup": json_startup,
        "kindergarden": json_guarderias,
        "school": json_colegios,
        "pubs": json_discotecas,
        "starbucks": json_starbucks,
        "train": json_train_station,
        "doggrummer": json_peluqueria
    }

def getFromDict(diccionario, mapa):
    return reduce(operator.getitem,mapa,diccionario)

def type_point(lista):
    return {"type": "Point",
            "coordinates": lista
    }


def json_reduced(response, type_=""):
    mapa_nombre = ["venue", "name"]
    mapa_latitud = ["venue", "location", "lat"]
    mapa_longitud = ["venue", "location", "lng"]
    mapa_direccion = ["venue", "location", "formattedAddress"]

    json_reduced = []
    for dic in response:
        new_dic = {}
        new_dic["nombre"] = getFromDict(dic, mapa_nombre)
        lat = getFromDict(dic, mapa_latitud)
        lon = getFromDict(dic, mapa_longitud)
        new_dic["dirección"] = getFromDict(dic, mapa_direccion)
        new_dic["location"] = type_point([lat, lon])
        new_dic["Type"] = type_
        json_reduced.append(new_dic)
    return json_reduced

def build_dic_json_to_mongo(dic_json_cities):
    dictionary = dict ()
    for k, v in dic_json_cities.items():
        dictionary[k] = json_reduced(v)
    return dictionary

def export_dump (name, json_to_save) :
    with open(name, 'w') as f:
        json.dump(json_to_save,f)


def create_collections_in_mongo(db, dic_json_to_mongo, place):
    for k, v in dic_json_to_mongo.items():
        file_path = f"./data/{k}_{place}.json"
        export_dump(file_path, v)

        with open(file_path) as file:
            file_data = json.load(file)

        Collection = db[k]

        if isinstance(file_data, list):
            Collection.insert_many(file_data)
        else:
            Collection.insert_one(file_data)

        Collection.create_index([("location", pymongo.GEOSPHERE)])

def drop_collections(db):
    db.get_collection("vegan_restaurant").drop()
    db.get_collection("airport").drop()
    db.get_collection("school").drop()
    db.get_collection("pubs").drop()
    db.get_collection("kindergarden").drop()
    db.get_collection("doggrummer").drop()
    db.get_collection("venga_restaurant").drop()
    db.get_collection("starbucks").drop()
    db.get_collection("startup").drop()
    db.get_collection("train").drop()


def create_query_distances(coordinates):
    query = [
       {
         '$geoNear': {
            'near':  coordinates,# [37.402559152869856, -6.006329402641001] ,
            'distanceField': "dist.calculated",
            'maxDistance': 2,
            'distanceMultiplier': 6371000,
            "spherical": True
         }
       }
    ]
    return query

def create_dict_distances(db, origin_coordinates):
    dict_distances = dict()
    for coll in db.list_collection_names():
        collection = db.get_collection(coll)
        dict_distances[coll] = list(collection.aggregate(create_query_distances(origin_coordinates)))
    return dict_distances


def create_list_city_distances(db, origin_coordinates, origin_name):
    dict_distances = create_dict_distances(db, origin_coordinates)
    list_total = []
    for k, v in dict_distances.items():
        list_distances = []
        for result in v:
            #print(result)
            latitude = result["location"]["coordinates"][0]
            longitude = result["location"]["coordinates"][1]

            list_distances.append([result["dist"]['calculated'], latitude,longitude, result['nombre']])
        #I'm getting the 3 first elements of the list, so the ones with less distances
        # TODO creating a loop using a parameter n which will be the number of distances we will keep (in this case is 3)
        list_total.append({"origin": origin_name, "feature": k,

                           "name1": list_distances[0][3], "distance1": list_distances[0][0],
                           "latitude1": list_distances[0][1],"longitude1": list_distances[0][2],
                           "name2": list_distances[1][3], "distance2": list_distances[1][0],
                           "latitude2": list_distances[1][1], "longitude2": list_distances[1][2],
                           "name3": list_distances[2][3], "distance3": list_distances[2][0],
                           "latitude3": list_distances[2][1], "longitude3": list_distances[2][2],
                           })
    return list_total

def mean_list(list_marks):
    marks_df = pd.DataFrame(list_marks)
    list_mean = []
    for i in range(len(marks_df.columns)):
        list_mean.append(marks_df[i].mean())
    return list_mean


# TODO add an dictionary as a parameter in the function(Configuration) with the weight of every group of worker
# so that, every group will have different weight on the totoal of weights. Obviously, data will have the bigger weight
def calculate_marks_mean():
    list_mean_total = []
    number_features = 8

    #desginers (20)
    marks_designers = 10*np.random.dirichlet(np.ones(number_features),size=20)
    mean_marks_designer = mean_list(marks_designers)
    list_mean_total.append(mean_marks_designer)

    #5 UI/UX Engineers
    marks_ui_ux= 10*np.random.dirichlet(np.ones(number_features),size=5)
    mean_marks_ui_ux = mean_list(marks_ui_ux)
    list_mean_total.append(mean_marks_ui_ux)

    #10 Frontend Developers
    marks_frontend= 10*np.random.dirichlet(np.ones(number_features),size=10)
    mean_marks_frontend = mean_list(marks_frontend)
    list_mean_total.append(mean_marks_frontend)

    #15 Data Engineers
    marks_data= 10*np.random.dirichlet(np.ones(number_features),size=15)
    mean_marks_data = mean_list(marks_data)
    list_mean_total.append(mean_marks_data)

    #5 Backend Developers
    marks_backend= 10*np.random.dirichlet(np.ones(number_features),size=5)
    mean_marks_backend = mean_list(marks_backend)
    list_mean_total.append(mean_marks_backend)

    #20 Account Managers
    marks_accountant= 10*np.random.dirichlet(np.ones(number_features),size=20)
    mean_marks_accountant = mean_list(marks_accountant)
    list_mean_total.append(mean_marks_accountant)

    # 1 Maintenance guy that loves basketball
    marks_maintenance= 10*np.random.dirichlet(np.ones(number_features),size=1)
    mean_marks_maintenance = mean_list(marks_maintenance)
    list_mean_total.append(mean_marks_maintenance)

    #10 Executives
    marks_executives= 10*np.random.dirichlet(np.ones(number_features),size=10)
    mean_marks_executives = mean_list(marks_executives)
    list_mean_total.append(mean_marks_executives)

    #1 CEO/President
    marks_CEO= 10*np.random.dirichlet(np.ones(number_features),size=20)
    mean_marks_CEO = mean_list(marks_CEO)
    list_mean_total.append(mean_marks_CEO)

    total_mean =  mean_list(list_mean_total)
    return total_mean
    print("mean total: ", mean_list(list_mean_total))
    print((sum(mean_list(list_mean_total))))

def values_total(db, city_coords, city_name, df_city):
    #df_city = pd.DataFrame(create_list_city_distances(db, city_coords, city_name))
    df_city["percentage"] = calculate_marks_mean()
    df_city["percentage"] = df_city["percentage"] / 10
    df_city["log"] = np.log(df_city["distance1"])
    df_city["value"] = (df_city["percentage"]) * df_city["log"]
    return df_city["value"].sum()


def values_total_df(db, city_coords, city_name, df_city):
    #df_city = pd.DataFrame(create_list_city_distances(db, city_coords, city_name))
    df_city["percentage"] = calculate_marks_mean()
    df_city["percentage"] = df_city["percentage"] / 10
    df_city["log"] = np.log(df_city["distance1"])
    df_city["value"] = (df_city["percentage"]) * df_city["log"]
    return df_city


def create_structure(db, origin_coordinates, name_place, language, url_query, client_id, client_secret):
    dic_json_api_response_for_city = json_api_to_dic(origin_coordinates, language, url_query, client_id,
                                                        client_secret)
    dic_json_to_mongo = build_dic_json_to_mongo(dic_json_api_response_for_city)
    create_collections_in_mongo(db, dic_json_to_mongo, name_place)

def set_markers(map_cities, df, origin_location):
    icono = Icon( color="red",
                   prefix="fa",
                   icon="train",
                   icon_color="black"  )
    mar =Marker(location=origin_location, icon=icono)
    mar.add_to(map_cities)
    for i, row in df.iterrows():
        #print(i,row)
        feature = {
            "location": [row["latitude1"], row["longitude1"]],
            "tooltip": row["feature"]
        }

        if row["feature"] == "pubs":
            icono = Icon( color="green",
                   icon="glyphicon glyphicon-glass",
                   icon_color="black")

        elif row["feature"] == "airport":
            icono = Icon( color="cadetblue",
                   icon="glyphicon glyphicon-road",
                   icon_color="black")

        elif row["feature"] == "startup":
            icono = Icon( color="cadetblue",
                   prefix="fa",
                   icon="laptop",
                   icon_color="black")

        elif row["feature"] == "starbucks":
            icono = Icon( color="darkgreen",
                   prefix="fa",
                   icon="coffee",
                   icon_color="black")

        elif row["feature"] == "doggrummer":
            icono = Icon( color="cadetblue",
                   prefix="fa",
                   icon="paw",
                   icon_color="black")

        elif row["feature"] == "vegan_restaurant":
            icono = Icon( color="green",
                   prefix="fa",
                   icon="cutlery",
                   icon_color="green")

        elif row["feature"] == "kindergarden":
            icono = Icon( color="pink",
                   prefix="fa",
                   icon="child",
                   icon_color="black")

        elif row["feature"] == "school":
            icono = Icon( color="blue",
                   prefix="fa",
                   icon="graduation-cap",
                   icon_color="black")

        elif row["feature"] == "train":
            icono = Icon( color="lightblue",
                   prefix="fa",
                   icon="train",
                   icon_color="black"  )
        else:
            icono = Icon( color="red",
                   prefix="fa",
                   icon="calendar",
                   icon_color="black")
            print(icono)

        mar = Marker(**feature, icon=icono)
        mar.add_to(map_cities)
    return map_cities


def input_cities(list_sp, list_en):
    geolocator = Nominatim(user_agent="Geomaps")

    city_name1 = input("Set the first city: ")
    try:
        location_geo1 = geolocator.geocode(city_name1)
        city_location1 = [location_geo1.latitude, location_geo1.longitude]
        city_name1 = city_name1.replace(" ", "_")
    except:
        city_location1 = [37.402559152869856, -6.006329402641001]
        city_name1 = "seville_cartuja"
        print("default location 1 : ", city_name1)

    while True :
        city_lang_input1 = input("select a language for the first city: (en/sp): ")
        if city_lang_input1.lower() == 'en':
            city_lang1 = list_en
            break
        if city_lang_input1.lower() == 'sp':
            city_lang1 = list_sp
            break

    city_name2 = input("Set the second city: ")
    try:
        location_geo2 = geolocator.geocode(city_name2)
        city_location2 = [location_geo2.latitude, location_geo2.longitude]
        city_name2 = city_name2.replace(" ", "_")
    except:
        city_location2 = [50.888243561864115, 4.445462993709954]
        city_name2 = "brussels_diegem"
        print("default location 2 : ", city_name2)

    while True :
        city_lang_input2 = input("select a language for the first city: (en/sp): ")
        if city_lang_input2.lower() == 'en':
            city_lang2 = list_en
            break
        if city_lang_input2.lower() == 'sp':
            city_lang2 = list_sp
            break

    city_name3 = input("Set the third city: ")
    try:
        location_geo3 = geolocator.geocode(city_name3)
        city_location3 = [location_geo3.latitude, location_geo3.longitude]
        city_name3 = city_name3.replace(" ", "_")
    except:
        city_location3 = [51.42136762437117, -0.9924852129899059]
        city_name3 = "reading_greenpark"
        print("default location 3 : ", city_name3)

    while True:
        city_lang_input3 = input("select a language for the first city: (en/sp): ")
        if city_lang_input3.lower() == 'en':
            city_lang3 = list_en
            break
        if city_lang_input3.lower() == 'sp':
            city_lang3 = list_sp
            break

    return city_name1, city_location1, city_name2, city_location2, city_name3, city_location3, city_lang1, city_lang2, city_lang3


def input_data_base():
    client = MongoClient("localhost:27017")
    database_name = input("Database Name: ")
    try:
        db = client[database_name]
        dblist = client.list_database_names()
        if database_name in dblist:
              print("The database exists.")
        else:
            print("Creating database....", database_name)
            print("Database created")
    except:
        db = client.get_database("project3")
        print("loading existing data base")
    print(db.name)
    return db