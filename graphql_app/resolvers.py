from pymongo import MongoClient
from sqlalchemy import create_engine, text
from ariadne import QueryType

query = QueryType()

# MongoDB
mongo_client = MongoClient("mongodb://admin:password@mongo-db:27017/?authSource=admin")
mongo_collection = mongo_client["benchmark_mongodb"]["employees"]

# Postgres
engine = create_engine(
    "postgresql://postgres:password@postgresql-db:5432/benchmark_postgres"
)


@query.field("employeeById")
def resolve_employee_by_id(*_, emp_id):
    # MongoDB
    result = mongo_collection.find_one({"emp_id": emp_id})
    if result:
        return result

    # Postgres
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM employees WHERE emp_id = :id"), {"id": emp_id}
        ).fetchone()
        if row:
            return dict(row)

    return None
