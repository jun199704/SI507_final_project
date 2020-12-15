# SI507_final_project
## Introduction
A movie filter that allow users to do movie search by name, category. Also provide related statistics.
## Interaction
API key can be obtained from http://www.omdbapi.com/ for free

The main page of the movie filter contains 5 options for user interaction. The interaction can be divided into 2 parts: movie search and filter, movie statistics.

If a user search the movie by name or category, he will be provided with a list of movie satisfying the search result. Clicking the movie and the user will be directed to a new page shows the movie details such as movie plot and runtime. Users can also choose to view by movie list. Total 100 movies in the database are shown. Users will be directed to movie detail page by clicking the movie. For the above 3 interactions, a button back to the main page is provided at the bottom.

Users can choose to view movie statistics by viewing a plot of movie counts for each category or the top 10 directors with the highest movie counts.
 
## Required Python packages
requests, flask, plotly, sqlites
