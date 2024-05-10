import requests
import schedule
import time
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import mysql.connector
from datetime import datetime


def retrieve_data():
    engine = create_engine("mysql+mysqlconnector://root:sanket@localhost/dataprojectpart1") #function to get data from the API and store it in SQL database
    df = pd.read_sql("SELECT * FROM api_data", con=engine)
    return df



def analyze_data():
    df = retrieve_data()


    print(df.head()) #check data and analyze statistically
    print(df.describe())

    #plot of pi values over time
    plt.figure(figsize=(10, 5))
    plt.plot(df['time'], df['pi'], marker='o', linestyle='-')
    plt.title('Pi Values Over Time')
    plt.xlabel('Time')
    plt.ylabel('Pi')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    #plot of factor values over time
    plt.figure(figsize=(10, 5))
    plt.plot(df['time'], df['factor'], color='red', marker='o', linestyle='-')
    plt.title('Factor Values Over Time')
    plt.xlabel('Time')
    plt.ylabel('Factor')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def fetch_data():
    response = requests.get('https://4feaquhyai.execute-api.us-east-1.amazonaws.com/api/pi') #function to get data from API
    data = response.json()
    store_data(data)

def store_data(data): #function that stores the data into the database using the mysql connector
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="sanket",
        database="dataprojectpart1"
    )
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_data (
            time DATETIME,
            pi DOUBLE,
            factor INT
        )
    ''')
    insert_query = '''INSERT INTO api_data (time, pi, factor) VALUES (%s, %s, %s)'''
    c.execute(insert_query, (data['time'], data['pi'], data['factor'])) #insert into db
    conn.commit() #commit changes into the database
    conn.close()


def setup_scheduler():
    schedule.every().minute.at(":00").do(fetch_data) #scheduler is set up to fetch data every minute for 60 minutes
    for i in range(60):
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    next_minute = (datetime.now().minute + 1) % 60 #this code here ensures that the script runs at the start of every minute
    delay_start = (next_minute - datetime.now().minute) * 60 - datetime.now().second
    time.sleep(delay_start)

    setup_scheduler()
    analyze_data()