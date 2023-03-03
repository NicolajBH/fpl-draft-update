# fpl-draft-update

Created in order to automate the collection of data for private FPL draft league. Only scrapes player points and does total points calculations based off of that in order to have "live" scores. The FPL Draft api which contains 'event_points' (i.e. the gameweek score) lags the "real" gameweek score therefore it wasn't possible to display a live table at, for example, half time. Does not do calculations for bonus points during game and waits for game update.

main.py scrapes data from the FPL website and merges the data into a single dataframe. Some additional calculations that are needed for the private league are added, such as the monthly points for each person. Other columns are added to make it more readable to others.
