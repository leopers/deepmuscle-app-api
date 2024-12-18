from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL
import os
from dotenv import load_dotenv
load_dotenv()

# connection_url = URL.create(
#     "mssql+pyodbc",
#     username="sa",
#     password="12345678",
#     host="localhost",
#     database="deepmuscle-dev",
#     query={
#         "driver": "ODBC Driver 17 for SQL Server",
#         "TrustServerCertificate": "yes"
#     },
# )

connection_url = URL.create(
    "postgresql+psycopg2",
    username=os.environ.get("DB_USERNAME"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=5432,
    database=os.environ.get("DB_NAME"),
)

engine = create_engine(connection_url)

# engine = create_engine('mysql+pymysql://root:20314167@localhost/deepmuscle_dev', 
# echo=True
# )

conn = engine.connect()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()