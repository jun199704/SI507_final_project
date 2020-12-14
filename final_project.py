import csv
import sqlite3
import requests
from bs4 import BeautifulSoup
import json
import re
import plotly.graph_objs as go
from flask import Flask,render_template,request

app=Flask(__name__)

api_key='ebd493ec'
DB_NAME='movies.sqlite'
CACHE_FILENAME='cache.json'

class Movie:
    '''a movie

    Instance Attributes
    -------------------
    rank: int 
        the rank of a movie 
    
    title: string
        the name of a movie(e.g. 'citizen kane')

    produce_year: int
        the produce year of the movie 

    director: string 
        the director of a movie (e.g. 'Orson Welles|111394')

    cast: string
        the cast of a movie (e.g. 'Joseph Cotten, Dorothy Comingore, Agnes Moorehead')
    '''
    def __init__(self, rank='None', title='None',produce_year='None',director='None',cast='None'):
        self.rank= rank
        self.title = title
        self.produce_year=produce_year
        self.director=director
        self.cast=cast

    def movie_describe(self):
        print(str(self.rank)+'. '+self.title+' '+'('+str(self.produce_year)+')'+' '+'['+self.director+']'+' '+self.cast)

class Movie_Genre:
    '''
    movie and related genre 

    Instance Attributes
    -------------------
    movie_id: int 
        the movie_id (the rank of the movie) 
    
    genre_id: int
        the genre_id (the same key used in genre_dict)
    '''
    def __init__(self,movie_id=0,genre_id=0):
        self.movie_id=movie_id
        self.genre_id=genre_id


def build_movie_list():
    ''' Make a  movie list that contains all 100 movies scraping from page url "https://www.afi.com/afis-100-years-100-movies/"

    Parameters
    ----------
    None

    Returns
    -------
    list
    '''
    base_url='https://www.afi.com/afis-100-years-100-movies'   
    movie_list=[]
    response=requests.get(base_url)
    soup=BeautifulSoup(response.text,'html.parser')

    movies=soup.find_all('div',class_='single_list col-sm-12 movie_popup')

    for movie in movies:
        movie_info=movie.find('h6', class_='q_title').text.strip()    
        r=re.compile(r'\d+\.')
        movie_info1=r.findall(movie_info)
        movie_rank=movie_info1[0]
        movie_rank=int(movie_rank[:-1])  #rank
    
        movie_info2=r.split(movie_info)
        movie_info2=movie_info2[1]
        movie_info2=movie_info2[1:]
        movie_info2=movie_info2.split(' (')
        movie_title=movie_info2[0]   #title

        movie_produceyear=movie_info2[1]
        movie_produceyear=int(movie_produceyear[:-1])  #produce year
    
        if movie.find('p', class_='Cast') is not None:
            movie_cast=movie.find('p', class_='Cast').text.strip() 
            movie_cast=movie_cast.split(': ')
            movie_cast=movie_cast[1]
        else:
            movie_cast='None'

        if movie.find('p',class_='Directors') is not None:
            movie_directors=movie.find('p',class_='Directors').text.strip()
            movie_directors=movie_directors.split(': ')
            movie_directors=movie_directors[1]
            movie_directors=movie_directors.split('|')
            directors_string=''
            for directors in movie_directors:
                if directors.isdigit() or directors=='':
                    directors_string=directors_string
                else:
                    directors_string=directors_string+','+directors
            directors_string=directors_string[1:]
            movie_director=directors_string
        else:
            movie_director='None'
        movie_list.append(Movie(movie_rank,movie_title,movie_produceyear,movie_director,movie_cast))
    return movie_list

def build_genre_list(movie_list):
    genre_dict={}
    genre_dict_reverse={}
    search_url='http://www.omdbapi.com'
    id=1
    for movie in movie_list:
        params={
            'apikey':api_key,
            't':movie.title
        }
        response=requests.get(search_url,params)
        result=response.json()
        if result['Response'] !='False':
            movie_genres=result['Genre']
            movie_genres=movie_genres.split(', ')
            for genre in movie_genres:
                if genre in genre_dict.values():
                    genre_dict=genre_dict
                    genre_dict_reverse=genre_dict_reverse
                else:
                    genre_dict[str(id)]=genre
                    genre_dict_reverse[genre]=str(id)
                    id=id+1
    return genre_dict,genre_dict_reverse

def build_movie_genre(movie_list,genre_dict_reverse):
    movie_genre_list=[]
    search_url='http://www.omdbapi.com'
    for movie in movie_list:
        movie_id=movie.rank
        params={
            'apikey':api_key,
            't':movie.title
        }
        response=requests.get(search_url,params)
        result=response.json()
        if result['Response'] !='False':
            movie_genres=result['Genre']
            movie_genres=movie_genres.split(', ')
            #print(movie.title)
            #print(movie_genres)
            for genre in movie_genres:
                genre_id=genre_dict_reverse[genre]
                movie_genre_list.append(Movie_Genre(int(movie_id),int(genre_id)))
    return movie_genre_list

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def construct_unique_key(baseurl, params):
    '''
    constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    '''
    
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key 

def get_movie_info(moviename):
    search_url='http://www.omdbapi.com'
    params={
        'apikey':api_key,
        't':moviename
    }
    request_key=construct_unique_key(search_url,params)
    CACHE_DICT = open_cache()
    if request_key in CACHE_DICT.keys():
        result=CACHE_DICT[request_key]
    else:
        response=requests.get(search_url, params)
        CACHE_DICT[request_key] = response.json()
        save_cache(CACHE_DICT)
        result=CACHE_DICT[request_key]

    if result['Response'] !='False':
        movie_runtime=result['Runtime']
        movie_plot=result['Plot']
        movie_language=result['Language']

    else:
        movie_runtime='None'
        movie_plot='None'
        movie_language='None'
    #print(movie.title+movie_runtime+'  '+movie_plot+' '+movie_language)
    return movie_runtime,movie_plot,movie_language

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_movies_sql = 'DROP TABLE IF EXISTS "Movies"'
    drop_genres_sql = 'DROP TABLE IF EXISTS "Genres"'
    drop_movie_genre_sql='DROP TABLE IF EXISTS "Movie_Genre"'
    
    create_movies_sql = '''
        CREATE TABLE IF NOT EXISTS "Movies" (
            "Rank" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "Title" TEXT NOT NULL,
            "ProduceYear" INTEGER NOT NULL, 
            "Director" TEXT NOT NULL,
            "Casts" TEXT NOT NULL
        )
    '''
    create_genres_sql = '''
        CREATE TABLE IF NOT EXISTS 'Genres'(
            'Id' INTEGER PRIMARY KEY,
            'Type' TEXT NOT NULL
        )
    '''
    create_movie_genre_sql = '''
        CREATE TABLE IF NOT EXISTS 'Movie_Genre'(
            'Movie_Id' INTEGER NOT NULL,
            'Genre_Id' INTEGER NOT NULL
        )
    '''

    cur.execute(drop_movies_sql)
    cur.execute(drop_genres_sql)
    cur.execute(drop_movie_genre_sql)
    cur.execute(create_movies_sql)
    cur.execute(create_genres_sql)
    cur.execute(create_movie_genre_sql)
    conn.commit()
    conn.close()

def load_movies(movie_list):
    insert_movie_sql='''
        INSERT INTO Movies
        VALUES (NULL, ?, ?, ?, ?)
    '''

    conn=sqlite3.connect(DB_NAME)
    cur=conn.cursor()

    for movie in movie_list:
        cur.execute(insert_movie_sql,
            [
                movie.title,
                movie.produce_year,
                movie.director,
                movie.cast
            ]
        )
    
    conn.commit()
    conn.close()

def load_genres(genre_dict):
    insert_genre_sql='''
        INSERT INTO Genres
        VALUES(?, ?)
    '''

    conn=sqlite3.connect(DB_NAME)
    cur=conn.cursor()
    
    id=1
    for k in range(0,len(genre_dict)):
        cur.execute(insert_genre_sql,
            [
                int(id),
                genre_dict[str(id)]
            ]
        )
        id=id+1
    conn.commit()
    conn.close()

def load_movie_genre(movie_genre_list):
    insert_movie_genre_sql='''
        INSERT INTO Movie_Genre
        VALUES(?, ?)
    '''

    conn=sqlite3.connect(DB_NAME)
    cur=conn.cursor()
    
    for movie in movie_genre_list:
        cur.execute(insert_movie_genre_sql,
            [
                movie.movie_id,
                movie.genre_id
            ]
        )
        
    conn.commit()
    conn.close()



movie_list=build_movie_list()
genre_dict,genre_dict_reverse=build_genre_list(movie_list)
movie_genre_list=build_movie_genre(movie_list,genre_dict_reverse)

create_db()
load_movies(movie_list)
load_genres(genre_dict)
load_movie_genre(movie_genre_list)

def movie_category(typemovie):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    query = '''SELECT Rank,Title,ProduceYear,Director,Casts
    FROM Movies
    INNER JOIN Movie_Genre
    ON Movies.Rank=Movie_Genre.Movie_id
    INNER JOIN Genres
    ON Movie_Genre.Genre_Id=Genres.Id
    WHERE Genres.Type=?'''
    result = cursor.execute(query,(typemovie,)).fetchall()
    connection.close()
    return result
    
def movie_count():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    query='''SELECT COUNT (*),Type
    FROM Movies
    INNER JOIN Movie_Genre
    ON Movies.Rank=Movie_Genre.Movie_id
    INNER JOIN Genres
    ON Movie_Genre.Genre_Id=Genres.Id
    GROUP BY Genres.Id
    ORDER BY COUNT(*) DESC'''
    result=cursor.execute(query).fetchall()
    connection.close()
    return result

def director_count():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    query='''SELECT COUNT (*),Director
    FROM Movies
    GROUP BY Director
    ORDER BY COUNT(*) DESC'''
    result=cursor.execute(query).fetchall()
    connection.close()
    return result
#def search_by_name(moviename):
#    connection = sqlite3.connect(DB_NAME)
#    cursor = connection.cursor()
#    result = cursor.execute("SELECT Rank,Title,Director,ProduceYear,Casts from Movies where Title LIKE '%"+moviename+"%'").fetchall()
#    connection.close()
#    return result


@app.route('/')
def main_page():
    return render_template('main_page.html')

@app.route('/search_by_genre')
def search_by_genre():
    return render_template('search_by_genre.html')

@app.route('/response',methods=['POST'])
def response():
    g=request.form["genre"]
    r=movie_category(g)
    return render_template('response.html',results=r)

@app.route('/movie_detail/<title>')
def movie_detail(title):
    runtime,plot,language=get_movie_info(title)
    return render_template('movie_detail.html',movie_title=title,movie_runtime=runtime,movie_plot=plot,movie_language=language)

@app.route('/movie_list_pre')
def movie_list_pre():
    connection=sqlite3.connect(DB_NAME)
    cursor=connection.cursor()
    query='''SELECT Rank,Title,ProduceYear,Director,Casts
    FROM Movies'''
    r=cursor.execute(query).fetchall()
    connection.close()
    return render_template('movie_list_pre.html',results=r)

@app.route('/search_by_name')
def search_by_name():
    return render_template('search_by_name.html')

@app.route('/handle_form',methods=['POST'])
def handle_form():
    n=request.form["name"]
    moviename=n.upper()
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    r = cursor.execute("SELECT Rank,Title,ProduceYear,Director,Casts from Movies where Title LIKE '%"+moviename+"%'").fetchall()
    connection.close()
    return render_template('handle_form.html',results=r)

@app.route('/plot')
def plot():
    results=movie_count()
    x_vals=[]
    y_vals=[]
    for r in results:
        x_vals.append(r[1])
        y_vals.append(r[0])
    bars_data=go.Bar(
        x=x_vals,
        y=y_vals
    )
    fig=go.Figure(data=bars_data)
    div=fig.to_html(full_html=False)
    return render_template('plot.html',plot_div=div)

@app.route('/director_count')
def plot_director():
    results=director_count() # eg. (76,'Drama')
    x_vals=[]
    y_vals=[]
    for r in results[0:10]:
        x_vals.append(r[1])
        y_vals.append(r[0])
    bars_data=go.Bar(
        x=x_vals,
        y=y_vals
    )
    fig=go.Figure(data=bars_data)
    div=fig.to_html(full_html=False)
    return render_template('director.html',plot_div=div)


if __name__ == '__main__':  
    app.run(debug=True)








    

