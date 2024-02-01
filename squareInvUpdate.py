from square.client import Client
import json, uuid, datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

root_path = ''
# root_path = "Z:/excel files/00 RMH Sale report/"

if __name__ == '__main__':
    with open(root_path+'appdata/square_auth.json') as f:
        temp = json.load(f)
        access_token = temp['access_token']
        environment = temp['environment'] 

    client = Client(access_token=access_token, environment=environment)

    body = {
        "product_types": [
            "REGULAR"
        ]
    }

    result = client.catalog.search_catalog_items(body=body)

    item_list = pd.DataFrame(columns=['object_id', 'upc'])

    for body in result.body['items']:
        for data in body['item_data']['variations']:
            try:
                item_list.loc[len(item_list)]= {'object_id': data['id'], 'upc': data['item_variation_data']['upc']}
            except:
                print(data['id'])

    with open(root_path+'appdata/db_auth.json') as f:
        temp = json.load(f)
        server = temp['server']
        database = temp['database'] 
        username = temp['username'] 
        password = temp['password']

    connection_string = 'DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})

    engine = create_engine(connection_url)

    query = "SELECT ItemLookupCode, Quantity\
            FROM dbo.Item Item \
            WHERE Item.DepartmentID IN (2, 4, 6) AND Item.Inactive = 0\
            ORDER BY ItemLookupCode;"

    with engine.connect() as conn, conn.begin():  
        fromPOS = pd.read_sql(query, conn, dtype={'Quantity':'int64'})

    fromPOS.fillna('', inplace=True)

    fromPOS.columns=['Item Lookup Code', 'Qty On Hand']

    test = item_list.merge(fromPOS[['Item Lookup Code', 'Qty On Hand']], how='left', left_on='upc', right_on='Item Lookup Code')

    test.loc[test['Qty On Hand']<0, 'Qty On Hand'] = 0
    test.drop('Item Lookup Code', axis=1, inplace=True)
    test.dropna(ignore_index=True ,inplace=True)

    batch_size = 100  # 100 is maximum number for batch update supported by Square API

    for i in range(0, len(test), batch_size):
        batch = range(i, min(i+batch_size, len(test)))
        body = {
            "idempotency_key": str(uuid.uuid1()),
            "changes": []
        }
        for index in batch:
            try:
                body['changes'].append(
                    {
                        "type": "PHYSICAL_COUNT",
                        "physical_count": {
                            "catalog_object_id": test['object_id'][index],
                            "state": "IN_STOCK",
                            "location_id": "7BRJFTZVH3FSX",
                            "quantity": str(test['Qty On Hand'][index]),
                            "occurred_at": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                        }
                    }
                )
            except:
                print(test.loc[index])
        result = client.inventory.batch_change_inventory(body=body)

        if result.is_success():
            print(result.body)
        elif result.is_error():
            print(result.errors)

