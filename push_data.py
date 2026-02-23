import os
import sys
import json
import certifi
import pandas as pd
import numpy as np
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from dotenv import load_dotenv
load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
print(MONGO_DB_URL)

ca = certifi.where()


class NetworkDataExtract():
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def csv_to_json_convertor(self, file_Path):
        try:
            data = pd.read_csv(file_Path)
            data.reset_index(drop=True, inplace=True)
            records = list(json.loads(data.T.to_json()).values())
            return records
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def inset_data_mongodb(self, records, database, collection):
        try:
            client = pymongo.MongoClient(
                MONGO_DB_URL,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=30000
            )

            db = client[database]
            col = db[collection]

            batch_size = 1000
            total = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                col.insert_many(batch)
                total += len(batch)

            return total

        except Exception as e:
            raise NetworkSecurityException(e, sys)


if __name__ == "__main__":
    FILE_PATH = r"Network_Data\PhishingData.csv"
    DATABASE = "ABHIAI"
    Collection = "NetworkData"
    networkobj = NetworkDataExtract()
    records = networkobj.csv_to_json_convertor(file_Path=FILE_PATH)
    print(records)
    no_of_records = networkobj.inset_data_mongodb(
        records, DATABASE, Collection)
    print(no_of_records)
