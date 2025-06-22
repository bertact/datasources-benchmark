from ariadne.asgi import GraphQL
from ariadne import load_schema_from_path, make_executable_schema
from unified_resolvers import query, mutation

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, [query, mutation])

app = GraphQL(schema, debug=True)
