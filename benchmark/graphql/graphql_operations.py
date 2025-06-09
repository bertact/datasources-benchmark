import requests


def query_by_id(emp_id):
    url = "http://graphql-api:8000/graphql"
    query = """
    query($emp_id: Int!) {
      employeeById(emp_id: $emp_id) {
        emp_id
        name
        salary
        city
        dpt_id
        prj_id
      }
    }
    """
    variables = {"emp_id": emp_id}
    response = requests.post(url, json={"query": query, "variables": variables})
    data = response.json()
    print(response.json())
    print(data.get("data", {}).get("employeeById"))
    return data.get("data", {}).get("employeeById")
