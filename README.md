# fpl-draft-update

Created in order to automate the collection of data for private FPL draft league. 

main.py scrapes data from the FPL website and merges the data into a single dataframe. Some additional calculations that are needed for the private league are added, such as the monthly points for each person. Other columns are added to make it more readable to others. Only scrapes player points and does gameweek score calculations based off of that in order to have "live" scores. The FPL Draft api which contains 'event_points' (i.e. the gameweek score) lags the "real" gameweek score therefore data updates done during a game or at full time were inaccurate. Does not do calculations for bonus points during game and waits for game update.

Uses github actions to run main.py every hour to update the data. Can be changed to different time intervals in actions.yml.

Can be made to work with other draft leagues by editing the 'players' dictionary in main.py

Discord folder contains files to run a bot on discord that outputs some of the information collected.
