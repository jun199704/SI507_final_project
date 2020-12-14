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











