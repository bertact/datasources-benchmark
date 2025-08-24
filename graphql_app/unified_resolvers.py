from ariadne import QueryType, MutationType
import postgres_resolvers as postgres
import mongo_resolvers as mongo

query = QueryType()
mutation = MutationType()


def get_resolvers(container):
    if container == "postgres":
        return postgres
    elif container == "mongodb":
        return mongo
    else:
        raise ValueError(f"Unknown container: {container}")


@query.field("selectById")
def select_by_id(_, info, container, table, id):
    return get_resolvers(container).resolve_select_by_id(_, info, table, id)


@query.field("selectFiltering")
def select_filtering(_, info, container, table, city):
    return get_resolvers(container).resolve_select_filtering(_, info, table, city)


@query.field("joinCityState")
def join_city_state(_, info, container, main_table, join_table):
    return get_resolvers(container).resolve_join_city_state(
        _, info, main_table, join_table
    )


@query.field("getAllIds")
def get_all_ids(_, info, container, table, limit=None):
    return get_resolvers(container).resolve_get_all_ids(_, info, table, limit)


@query.field("getCities")
def get_cities(_, info, container, table, limit=None):
    return get_resolvers(container).resolve_get_cities(_, info, table, limit)


@mutation.field("updateSalaryById")
def update_salary_by_id(_, info, container, table, id):
    return get_resolvers(container).resolve_update_salary_by_id(_, info, table, id)


@mutation.field("deleteById")
def delete_by_id(_, info, container, table, id):
    return get_resolvers(container).resolve_delete_by_id(_, info, table, id)


@mutation.field("insertData")
def insert_data(_, info, container, table, columns, values):
    return get_resolvers(container).resolve_insert_data(_, info, table, columns, values)
