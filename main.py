import pandas as pd
import json
import os
import requests
import mysql.connector

df_titles_and_movies = pd.read_csv('netflix_titles.csv') #csv files of netlix movie/data from kaggle
df_ratings = pd.read_csv('NetflixTVShowsAndMovies.csv') #csv file of netflix movie/show from kaggle - includes imdb

df_titles_and_movies = df_titles_and_movies[["title", "type", "director", "release_year", "duration", "country", "listed_in", "rating"]]

df_ratings = df_ratings[["title", "release_year", "imdb_score", "imdb_votes"]]

df_titles_and_movies['director'] = df_titles_and_movies['director'].apply(lambda x: x.split(",")[0] if pd.notna(x) else x)
df_titles_and_movies['country'] = df_titles_and_movies['country'].apply(lambda x: x.split(",")[0] if pd.notna(x) else x)
df_titles_and_movies['listed_in'] = df_titles_and_movies['listed_in'].apply(lambda x: x.split(",")[0] if pd.notna(x) else x)


common_titles_df = pd.merge(df_titles_and_movies, df_ratings, on=['title', 'release_year'], how='inner') #merging two dataframes based on common titles for simplicity purposes
common_titles_df = common_titles_df.head(100) #truncating dataframe to first 100 titles - 2000+ values was way too slow and hard to work with
common_titles_df = common_titles_df.dropna()
common_titles_df = common_titles_df.rename(columns={
    'duration': 'Duration',
    'release_year': 'ReleaseYear',
    'listed_in': 'GenreName',
    'rating': 'movie_rating',
    'imdb_score': 'RatingValue',
    'imdb_votes': 'NumberOfVotes'
})


print(common_titles_df)

countryDict = {}
processed_countries = set()

for country in common_titles_df['country']:
    if not isinstance(country, str):
        continue
    country = country.strip()
    if not country or country in processed_countries:
        continue
    processed_countries.add(country)

    url = f"https://restcountries.com/v3.1/name/{country}?fields=capital,population"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        countryData = response.json()
        capital = countryData[0].get('capital', [None])[0]
        data = {
            "CountryName": country.capitalize(),
            "Capital": capital,
            "Population": countryData[0]['population']
        }
        countryDict[country] = data

df_country = pd.DataFrame(list(countryDict.values())).dropna()


print(df_country)

from mysql.connector import Error


def create_table(connection, query): #function that creates all the tables
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
    cursor.close()


def insert_countries_table_data(connection, df): #function that inserts into the countries table
    query = ("INSERT INTO Countries (CountryName, Capital, Population) "
             "VALUES (%s, %s, %s) "
             "ON DUPLICATE KEY UPDATE "
             "Capital=VALUES(Capital), Population=VALUES(Population)")
    cursor = connection.cursor()
    for _, row in df.iterrows():
        values = (row['CountryName'], row['Capital'], row['Population'])
        cursor.execute(query, values)
    connection.commit()  # Commit the transaction
    cursor.close()

def insert_directors_table_data(connection, df): #function that inserts into the directors table
    query = """
    INSERT INTO Directors (Name)
    VALUES (%s)
    ON DUPLICATE KEY UPDATE Name=VALUES(Name)
"""
    cursor = connection.cursor()
    for _, row in df.iterrows():
        values = (row['DirectorName'],)
        cursor.execute(query, values)
    connection.commit()
    cursor.close()

def insert_genres_table_data(connection, df): #function that inserts into the directors table
    query = """
    INSERT INTO Genres (GenreName)
    VALUES (%s)
    ON DUPLICATE KEY UPDATE GenreName=VALUES(GenreName)
"""
    cursor = connection.cursor()
    for _, row in df.iterrows():
        values = (row['GenreName'],)
        cursor.execute(query, values)
    connection.commit()
    cursor.close()

def get_country_id(connection, country_name): #function that gets the country ID based on the country name
    query = "SELECT CountryID FROM Countries WHERE CountryName = %s"
    cursor = connection.cursor()
    cursor.execute(query, (country_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def insert_titles_table_data(connection, df_titles): #function that inserts into the directors table
    query = """
    INSERT INTO Titles (Type, Title, ReleaseYear, Duration, CountryID, Genre)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE TitleID=TitleID
    """
    cursor = connection.cursor()
    for _, row in df_titles.iterrows():
        country_id = get_country_id(connection, row['country'])
        values = (row['type'], row['title'], row['ReleaseYear'], row['Duration'], country_id, row['GenreName'])
        cursor.execute(query, values)
    connection.commit()
    cursor.close()


def get_title_id(connection, title, release_year): #function that gets the title ID based on the title name and release year
    query = "SELECT TitleID FROM Titles WHERE Title = %s AND ReleaseYear = %s"
    cursor = connection.cursor()
    cursor.execute(query, (title, release_year))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def insert_ratings_table_data(connection, df_ratings):
    query = """
    INSERT INTO Ratings (TitleID, RatingValue, NumberOfVotes)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE RatingValue=VALUES(RatingValue), NumberOfVotes=VALUES(NumberOfVotes)
    """
    cursor = connection.cursor()
    for _, row in df_ratings.iterrows():
        title_id = get_title_id(connection, row['title'], row['ReleaseYear'])
        if title_id:  # Ensure the title exists in the Titles table
            values = (title_id, row['RatingValue'], row['NumberOfVotes'])
            cursor.execute(query, values)
    connection.commit()
    cursor.close()


try:
    connection = mysql.connector.connect(host='localhost',
                                         database='etlproject',
                                         user='root',
                                         password='sanket') #need to create database beforehand

    if connection.is_connected():
        print("You're connected to database: ", connection.database)

        #SQL code for creating tables
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS Directors (
                DirectorID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(255) UNIQUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Countries (
                CountryID INT AUTO_INCREMENT PRIMARY KEY,
                CountryName VARCHAR(255) UNIQUE,
                Capital VARCHAR(255),
                Population INT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Titles (
                TitleID INT AUTO_INCREMENT PRIMARY KEY,
                Type VARCHAR(255),
                Title VARCHAR(255),
                ReleaseYear INT,
                Duration VARCHAR(255),
                CountryID INT,
                Genre VARCHAR(255),
                FOREIGN KEY (CountryID) REFERENCES Countries(CountryID),
                UNIQUE (Title, Type, ReleaseYear)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Genres (
                GenreID INT AUTO_INCREMENT PRIMARY KEY,
                GenreName VARCHAR(255) UNIQUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Ratings (
                RatingID INT AUTO_INCREMENT PRIMARY KEY,
                TitleID INT,
                RatingValue VARCHAR(255),
                NumberOfVotes INT,
                FOREIGN KEY (TitleID) REFERENCES Titles(TitleID),
                UNIQUE(TitleID)
            );
            """
        ]


        for table_sql in tables_sql:
            create_table(connection, table_sql)  #execute each table creation query

        insert_countries_table_data(connection, df_country) #separate dataframes for each table to be used to load in each table indiviually
        df_directors = pd.DataFrame(common_titles_df['director'].unique(),columns=['DirectorName'])
        insert_directors_table_data(connection, df_directors)
        df_genres = pd.DataFrame(common_titles_df['GenreName'].unique(), columns=['GenreName'])
        insert_genres_table_data(connection, df_genres)
        df_titles = pd.DataFrame(common_titles_df[['type','title','ReleaseYear','Duration','country','GenreName']])
        insert_titles_table_data(connection,df_titles)
        df_ratings = pd.DataFrame(common_titles_df[['title', 'ReleaseYear', 'RatingValue', 'NumberOfVotes']])
        insert_ratings_table_data(connection, df_ratings)

        cursor = connection.cursor() #the SQL query for part three of this assignment - gets number of titles associated with each of the genres
        query = """
        SELECT Genre, COUNT(*) AS NumberOfTitles
        FROM Titles
        GROUP BY Genre;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        print("~~~~~~~~~~~~~~~~~SQL Query~~~~~~~~~~~~~~~~~~")
        for (genre, numberOfTitles) in results:
            print(f"{genre}: {numberOfTitles}")
        cursor.close()


except Error as e: #error catching
    print(f"Error while connecting to MySQL", e)

finally:
    if connection.is_connected():
        connection.close()
        print("MySQL connection is closed")