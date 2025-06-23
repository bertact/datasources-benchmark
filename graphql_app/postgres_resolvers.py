from psycopg2 import sql
import psycopg2
from ariadne import QueryType, MutationType

query = QueryType()
mutation = MutationType()


def get_postgres_conn():
    return psycopg2.connect(
        "dbname=benchmark_postgres user=postgres password=password host=postgresql-db port=5432"
    )


def resolve_select_by_id(_, info, table, id):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table))

        cur.execute(query, (id,))
        result = cur.fetchall()
        conn.commit()

        return len(result) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_select_filtering(_, info, table, city):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL(
            """
            SELECT * FROM {} WHERE city = %s
            AND name_prefix = 'Mr.'
            AND gender = 'M'
            AND salary > 65000
            AND age_in_company > 2
            AND year_of_joining > 2000
        """
        ).format(sql.Identifier(table))

        cur.execute(query, (city,))
        result = cur.fetchall()
        conn.commit()

        return len(result) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_update_salary_by_id(_, info, table, id):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("UPDATE {} SET salary = %s WHERE id = %s").format(
            sql.Identifier(table)
        )
        cur.execute(query, (65000, id))
        conn.commit()

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_delete_by_id(_, info, table, id):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(table))
        cur.execute(query, (id,))
        conn.commit()

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_join_city_state(_, info, main_table, join_table):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL(
            """
            SELECT e.*, l.state AS state_long
            FROM {} AS e
            JOIN {} AS l
            ON e.state = l.abbreviation
        """
        ).format(sql.Identifier(main_table), sql.Identifier(join_table))

        cur.execute(query)
        cur.fetchall()
        conn.commit()

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_insert_data(_, info, table, columns, values):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        )
        cur.execute(query, values)

        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def resolve_get_all_ids(_, info, table, limit=None):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("SELECT id FROM {} ORDER BY id").format(sql.Identifier(table))
        if limit:
            query += sql.SQL(" LIMIT %s")
            cur.execute(query, (limit,))
        else:
            cur.execute(query)

        rows = cur.fetchall()
        conn.commit()

        ids = [row[0] for row in rows]

        return ids

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def resolve_get_cities(_, info, table, limit=None):
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        query = sql.SQL("SELECT DISTINCT city FROM {}").format(sql.Identifier(table))
        if limit:
            query += sql.SQL(" LIMIT %s")
            cur.execute(query, (limit,))
        else:
            cur.execute(query)

        rows = cur.fetchall()
        conn.commit()
        cities = [row[0] for row in rows]

        return cities
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        if conn:
            conn.close()
