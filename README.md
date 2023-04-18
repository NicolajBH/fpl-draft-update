# fpl-draft-update

Created in order to automate the collection of data for private FPL draft league. 

main.py scrapes data from the FPL website and uploads it to a sql database. Checks for latest gameweek data to avoid unnecessary api requests.

Uses github actions to run main.py every hour to update the data. Can be changed to different time intervals in actions.yml.

Can be made to work with other draft leagues by editing the 'players' dictionary in main.py

dashboard.py runs a streamlit dashboard to display various stats for the draft league
