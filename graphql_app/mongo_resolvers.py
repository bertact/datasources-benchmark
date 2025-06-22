from pymongo import MongoClient
from ariadne import QueryType, MutationType

query = QueryType()
mutation = MutationType()


def get_mongo_collection():
    client = MongoClient("mongodb://admin:password@mongo-db:27017/?authSource=admin")
    db = client["benchmark_mongodb"]
    return db["employees"]


collection = get_mongo_collection()


def resolve_select_by_id(_, info, table, id):
    try:
        doc = collection.find_one({"id": id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return len(doc) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_select_filtering(_, info, table, city):
    try:
        filter_query = {
            "city": city,
            "name_prefix": "Mr.",
            "gender": "M",
            "salary": {"$gt": 65000},
            "age_in_company": {"$gt": 2},
            "year_of_joining": {"$gt": 2000},
        }
        results = list(collection.find(filter_query))
        for doc in results:
            doc["_id"] = str(doc["_id"])
        return len(results) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_update_salary_by_id(_, info, table, id):
    try:
        result = collection.update_one({"id": id}, {"$set": {"salary": 65000}})
        return result.modified_count > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_delete_by_id(_, info, table, id):
    try:
        result = collection.delete_one({"id": id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_join_city_state(_, info, table_name, join_table):
    try:
        result = list(
            collection.aggregate(
                [
                    {
                        "$lookup": {
                            "from": join_table,
                            "localField": "state",
                            "foreignField": "abbreviation",
                            "as": "state_info",
                        }
                    },
                    {"$unwind": "$state_info"},
                    {
                        "$project": {
                            "id": 1,
                            "name": 1,
                            "state": 1,
                            "state_info.state": 1,
                        }
                    },
                ]
            )
        )

        for doc in result:
            doc["_id"] = str(doc["_id"])
        return len(result) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_insert_data(_, info, table, columns, values):
    try:
        doc = dict(zip(columns, values))
        result = collection.insert_one(doc)
        return len(result) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def resolve_get_all_ids(_, info, table, limit=None):
    try:
        cursor = collection.find({}, {"id": 1}).sort("id", 1)
        if limit:
            cursor = cursor.limit(limit)
        ids = [doc["id"] for doc in cursor]
        return ids

    except Exception as e:
        print(f"Error: {e}")
        return []


def resolve_get_cities(_, info, table, limit=None):
    try:
        pipeline = [
            {"$group": {"_id": "$city"}},
            {"$limit": limit} if limit else {},
        ]
        results = list(collection.aggregate([p for p in pipeline if p]))
        cities = [doc["_id"] for doc in results]
        return cities
    except Exception as e:
        print(f"Error: {e}")
        return []
