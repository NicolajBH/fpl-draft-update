from sqlalchemy import create_engine
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# player names and entry ids
players = {15606:'Nicolaj',24788:'Jesus',42118:'Kris',154393:'Mattia',16133:'Ollie'}
# create engine
engine = create_engine('sqlite:///fpl-draft-db.db')
conn = engine.connect()

# check for existing data
# If no data then request all, else latest gameweek data and remove data where gw = start_gw
# +1 gw after next deadline has passed
try: 
    start_gw = pd.read_sql_query("SELECT MAX(id) FROM deadlines WHERE finished=1",conn).values[0][0]
    now = datetime.now(timezone.utc)
    next_deadline = pd.read_sql_query("SELECT deadline_time FROM deadlines WHERE id = (SELECT MIN(id) FROM deadlines WHERE finished = 0)",conn).values[0][0]
    next_deadline = datetime.strptime(next_deadline, "%Y-%m-%dT%H:%M:%S%z")
    if now > next_deadline:
        end_gw = start_gw+1
    else:
        end_gw = start_gw
    engine.execute(f'DELETE FROM player_picks WHERE gw = {start_gw} AND gw = {end_gw}')
    engine.execute(f'DELETE FROM player_stats WHERE gw = {start_gw} AND gw = {end_gw}')
except:
    url = "https://draft.premierleague.com/api/game"
    headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
    response = requests.request("GET", url, headers=headers)
    data = response.json()
    start_gw = 1
    end_gw = data['current_event']

# get player info from draft game mode
url = "https://draft.premierleague.com/api/bootstrap-static"
headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
response = requests.request("GET", url, headers=headers)
while response.status_code != 200:
    time.sleep(5)
    response = requests.request("GET", url, headers=headers)
data = response.json()
draft_player_info = pd.DataFrame(data['elements'])
draft_player_info.to_sql('draft_player_info',engine,if_exists='replace', index=False)

# get deadlines and add month name
deadlines = pd.DataFrame(data['events']['data'])
deadlines['month'] = pd.DatetimeIndex(deadlines['deadline_time']).month_name()
deadlines.to_sql('deadlines',engine,if_exists='replace', index=False)

# get player info from fantasy game mode
url = "https://fantasy.premierleague.com/api/bootstrap-static/"
headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
response = requests.request("GET", url, headers=headers)
while response.status_code != 200:
    time.sleep(5)
    response = requests.request("GET", url, headers=headers)
data = response.json()
fantasy_player_info = pd.DataFrame(data['elements'])
fantasy_player_info.to_sql('fantasy_player_info',engine,if_exists='replace',index=False)

# get player stats
# loop through gameweeks to scrape player stats and append new data
for gw in range(start_gw, end_gw+1):
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live"
    headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
    response = requests.request("GET", url, headers=headers)
    while response.status_code != 200:
        time.sleep(5)
        response = requests.request("GET", url, headers=headers)
    data = response.json()
    player_stats_new_rows = pd.json_normalize(data,record_path=['elements']).drop(columns=['explain'])
    player_stats_new_rows['gw'] = gw
    # player_stats_new_rows.columns = player_stats_new_rows.columns.str.replace("stats.","",regex=False)
    player_stats_new_rows.to_sql('player_stats',engine,if_exists='append', index=False)

# get fantasy player picks for each player in the league
# loop through gameweeks and entry ids to scrape player pick data and append new data to sql db
player_picks_df = pd.DataFrame()
for gw in range(start_gw, end_gw+1):
    for uid in players.keys():
        url = f"https://draft.premierleague.com/api/entry/{uid}/event/{gw}"
        headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
        response = requests.request("GET", url, headers=headers)
        while response.status_code != 200:
            time.sleep(5)
            response = requests.request("GET", url, headers=headers)
        data = response.json()
        picks_new_rows = pd.DataFrame(data['picks'])
        sub_in = [d['element_in'] for d in data['subs'] if 'element_in' in d]
        sub_out = [d['element_out'] for d in data['subs'] if 'element_out' in d]
        picks_new_rows['gw'] = gw
        picks_new_rows['team_id'] = uid
        picks_new_rows['played'] = np.where(picks_new_rows.position <= 11, True, False)
        picks_new_rows['sub_in'] = np.where(picks_new_rows.element.isin(sub_in), True, False)
        picks_new_rows['sub_out'] = np.where(picks_new_rows.element.isin(sub_out), True, False)
        picks_new_rows.drop(columns=['is_captain','is_vice_captain','multiplier'], inplace=True)
        player_picks_df = pd.concat([player_picks_df,picks_new_rows])
player_picks_df.to_sql('player_picks',engine,if_exists='append', index=False)