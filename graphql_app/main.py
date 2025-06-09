from ariadne.asgi import GraphQL
from ariadne import load_schema_from_path, make_executable_schema
from resolvers import query

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, query)

app = GraphQL(schema, debug=True)
