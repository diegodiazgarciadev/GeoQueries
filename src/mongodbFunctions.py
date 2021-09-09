import json
import pymongo
from pymongo import MongoClient

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

def export_dump (name, json_to_save) :
    """
    Create a json file from a jason.
    Args:
        name (string): name of the file,
        json_to_save (json) : json to save
     """
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
    """ dropping all collection from a database
      args : db( database we will be using)

      """
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




