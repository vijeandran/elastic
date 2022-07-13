try:
    import psycopg2
    import json
    import pandas as pd

    import elasticsearch
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers
    from elasticsearch import RequestsHttpConnection

    print("Loaded  .. . . . . . . .")
except Exception as e:
    print("Error : {} ".format(e))


class Settings():

    def __init__(self,
                 pgsqlhost='localhost',
                 pgsqlport=5432,
                 pgsqluser='flaskuser',
                 pgsqlpassword='aaaaaaaa',
                 pgsqldataBase='mydb1',
                 pgsqltableName='employee',
                 pgsqlquery='',
                 elkhost="localhost",
                 elkport='9200'):

        self.pgsqlhost=pgsqlhost
        self.pgsqlport = pgsqlport
        self.pgsqluser = pgsqluser
        self.pgsqlpassword = pgsqlpassword
        self.pgsqldataBase = pgsqldataBase
        self.pgsqltableName = pgsqltableName
        self.pgsqlquery =pgsqlquery
        self.elkhost =elkhost
        self.elkport =elkport
        self.elkhost = "https://{}:{}".format(self.elkhost, self.elkport)

class PgSql(object):

    def __init__(self, settings=None):
        self.settings=settings

    def execute(self):
        try:

            self.conn = psycopg2.connect(
                host     =      self.settings.pgsqlhost,
                port     =      self.settings.pgsqlport,
                password =      self.settings.pgsqlpassword,
                user     =      self.settings.pgsqluser,
                database =      self.settings.pgsqldataBase,
            )

            self.cursor = self.conn.cursor()
            self.cursor.execute("{}".format(self.settings.pgsqlquery))
            myresult = self.cursor.fetchall()
            yield myresult
        except Exception as e:
            print("Error : {} ".format(e))
            return "Invalid Query : {} ".format(e)


class ELK(object):
    def __init__(self, settings=None):
        self.settings =settings
#        self.es = Elasticsearch(timeout=600, hosts=self.settings.elkhost)

        self.es = Elasticsearch(timeout=600)
#        self.es = Elasticsearch("http://localhost:9200")
#        self.es = Elasticsearch([{'host': 'localhost', 'port': '9200'}], timeout=60, max_retries=10, retry_on_timeout=True)
    def upload(self, records):

        try:
            helpers.bulk(self.es,records)
        except Exception as e:
            print("{}".format(e))


def main():
    # Step 1: Create a Settings

    BATCH_SIZE      = 5
    TABLE_NAME      = "employee"
    DATABASE_NAME   = 'mydb1'
    TOTAL_RECORDS   = 0

    print("Main Func Started  .. . . . . . . .")

    # Count Total number of Records
    _settings = Settings(pgsqltableName=TABLE_NAME,
                         pgsqldataBase=DATABASE_NAME,
                         pgsqlquery='SELECT COUNT(*) from {} '.format(TABLE_NAME))

    print("_settings variable assigned .. . . . . . . .")

    # Create a PgSQL Class
    _helper = PgSql(settings=_settings)
    res = _helper.execute()

    TOTAL_RECORDS = next(res)[0][0]

    print("Total records counted: ", TOTAL_RECORDS)

    # ===========================================================================================
    # Pagination system to pull records in a efficient way
    queries = ['SELECT * FROM {} limit {} OFFSET {} '.format(TABLE_NAME, BATCH_SIZE, page)
               for page in range(0,TOTAL_RECORDS, BATCH_SIZE)]
    print("Queries are: ",queries)
    # ==============================================================================================
    columnQuery = "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_CATALOG='{}' AND TABLE_NAME = '{}' order by ordinal_position".format(DATABASE_NAME, TABLE_NAME)
    _settings.pgsqlquery = columnQuery
    res = _helper.execute()

    # List of All column Names
    columnNames = [name[0] for name in next(res)]

    print("Column Names collected . . . . . . . . .")

    list_df = []

    for query in queries:
        _settings.pgsqlquery = query
        res = _helper.execute()
        res = next(res)
        df = pd.DataFrame(data=res, columns=columnNames)

        df1 = df.to_dict("records")

        list_df.append(df1)

        print(" ")
        print('------------------------')
        print("list_df: ", list_df)
        print(" ")

    flat_list = [item for sublist in list_df for item in sublist]
    print("Flat List: ", flat_list)
    action = [
        {
            '_index': '{}'.format(TABLE_NAME),
            '_id': chunk['id'],
            '_source':chunk
        }
        for chunk in flat_list
    ]      
    print("Records: ", action)
    print("-----------------------")    
        
    eshelper = ELK(settings=_settings)
    print("ELK class done . . . . . . . . .")
        
    eshelper.upload(records=action)
    print("Index loaded. . . . . . . . .")
        
if __name__ == "__main__":
    main()
    

