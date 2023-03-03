import requests
import pandas as pd
import numpy as np
import time

# fetch current gw id 
url = "https://draft.premierleague.com/api/game"
headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
response = requests.request("GET", url, headers=headers)
data = response.json()
current_gw = data['current_event']

# empty lists to store data from scraping
playerId = []
gameweek = []
teamId = []
position = []

# fetch each person's player picks for each gameweek
players = {'Nicolaj':15606, 'Jesus':24788,'Kris':42118, 'Mattia':154393, 'Ollie':16133}

for name, uid in players.items():
    for gw in range(1, current_gw+1):
        url = f"https://draft.premierleague.com/api/entry/{uid}/event/{gw}"
        headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
        response = requests.request("GET", url, headers=headers)
        while response.status_code != 200:
            time.sleep(5)
            response = requests.request("GET", url, headers=headers)
        data = response.json()
        for i in data['picks']:
            playerId.append(i['element'])
            position.append(i['position'])
            gameweek.append(gw)
            teamId.append(uid)

# Create dataframe to store data
player_info_df = pd.DataFrame({
    'playerId':playerId,
    'gameweek':gameweek,
    'teamId':teamId,
    'position':position
})

# Get all player points from each gw
gw_points = []
playerId = []
player_gw = []

for gw in range(1, current_gw+1):
    url = f"https://draft.premierleague.com/api/event/{gw}/live"
    headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
    response = requests.request("GET", url, headers=headers)
    while response.status_code != 200:
        time.sleep(5)
        response = requests.request("GET", url, headers=headers)
    data = response.json()
    for count, value in enumerate(data['elements'], start=1):
        try:
            gw_points.append(data['elements'][f'{count}']['stats']['total_points'])
            playerId.append(count)
            player_gw.append(gw)
        except:
            pass

player_points_df = pd.DataFrame({
    'playerId':playerId,
    'playerPoints':gw_points,
    'gw':player_gw
})

player_id = []
first_name = []
second_name = []
web_name = []
draft_rank = []

# fetch player info (id, first_name, second_name, web_name)
url = "https://draft.premierleague.com/api/bootstrap-static"
headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
response = requests.request("GET", url, headers=headers)
data = response.json()


for i in range(len(data['elements'])):
    player_id.append(data['elements'][i]['id'])
    first_name.append(data['elements'][i]['first_name'])
    second_name.append(data['elements'][i]['second_name'])
    web_name.append(data['elements'][i]['web_name'])
    draft_rank.append(data['elements'][i]['draft_rank'])

# create player info dict
player_dict = {}
for i, j in enumerate(player_id):
    player_dict[j] = first_name[i], second_name[i], web_name[i], draft_rank[i]

for key, value in player_dict.items():
    player_points_df.loc[player_points_df['playerId'] == key, 'first_name'] = value[0]
    player_points_df.loc[player_points_df['playerId'] == key, 'second_name'] = value[1]
    player_points_df.loc[player_points_df['playerId'] == key, 'web_name'] = value[2]
    player_points_df.loc[player_points_df['playerId'] == key, 'draft_rank'] = value[3]

# add playerPoints, first_name, second_name, web_name to player_info_df
player_data_df = player_info_df.merge(player_points_df, left_on=['playerId','gameweek'], right_on=['playerId', 'gw'])

# get deadline data
gw_deadline = []
time_deadline = []

for name, uid, in players.items():
    url = "https://draft.premierleague.com/api/bootstrap-static"
    headers = {"Cookie": "pl_euconsent-v2=CPnHJ0HPnHJ0HFCABAENC3CsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}"}
    response = requests.request("GET", url, headers=headers)
    data = response.json()
    for i in data['events']['data']:
        gw_deadline.append(i['id'])
        time_deadline.append(i['deadline_time'])

# add deadlines to the dataframe
deadline = dict(map(lambda i,j : (i,j) , gw_deadline,time_deadline))
for key, value in deadline.items():
    player_data_df.loc[player_data_df['gameweek'] == key, 'deadline'] = value

# add names of each person
names = {'Nicolaj':15606, 'Jesus':24788,'Kris':42118, 'Mattia':154393, 'Ollie':16133} 
for key, value in names.items():
    player_data_df.loc[player_data_df['teamId'] == value, 'name'] = key

# add month names to the dataframe.
player_data_df['month'] = pd.DatetimeIndex(player_data_df['deadline']).month_name()
# create monthlyPoints column and calculate monthly points for each player 
player_data_df['monthlyPoints'] = player_data_df.groupby(['teamId', 'month', 'playerId'])['playerPoints'].cumsum()
# column to show whether a player was in the "scoring" 11
player_data_df['played'] = np.where(player_data_df.position <= 11, True, False)
player_data_df.draft_rank = player_data_df.draft_rank.astype(int) # convert draft rank to int

# create short name column to avoid formatting issue on Discord mobile app 
player_data_df['short_name'] = np.where(player_data_df.web_name.str.len() > 12, player_data_df.web_name.str[:12], player_data_df.web_name)

# columns for when player joined/left team
gws = list(player_data_df.gw.unique())
teamIds = list(player_data_df.teamId.unique())
teamIdList = []
playerIdList = []
gwList = []
gw_in = []

# compare each consecutive gamweek to track changes in player picks
for teamid in teamIds:
    for gw in gws:
        df1 = player_data_df[(player_data_df['teamId'] == teamid) & (player_data_df['gw'] == gw)]
        list1 = df1[['playerId']].values.flatten().tolist()
        list1 = sorted(list1)

        df2 = player_data_df[(player_data_df['teamId'] == teamid) & (player_data_df['gw'] == gw-1)]
        list2 = df2[['playerId']].values.flatten().tolist()
        list2 = sorted(list2)

        transferIn = list(set(list1) - set(list2))

        for count, values in enumerate(transferIn):
            teamIdList.append(teamid)
            playerIdList.append(values)
            gwList.append(gw)
            gw_in.append(gw)

transfer_in_df = pd.DataFrame({
    'teamId':teamIdList,
    'playerId':playerIdList,
    'gw':gwList,
    'bought':gw_in,
})

teamIdList = []
playerIdList = []
gwList = []
gw_out = []

for teamid in teamIds:
    for gw in gws[:-1]:
        df1 = player_data_df[(player_data_df['teamId'] == teamid) & (player_data_df['gw'] == gw)]
        list1 = df1[['playerId']].values.flatten().tolist()
        list1 = sorted(list1)
        
        df2 = player_data_df[(player_data_df['teamId'] == teamid) & (player_data_df['gw'] == gw+1)]
        list2 = df2[['playerId']].values.flatten().tolist()
        list2 = sorted(list2)
        
        transferOut = list(set(list1) - set(list2))
        
        for count, values in enumerate(transferOut):
            teamIdList.append(teamid)
            playerIdList.append(values)
            gwList.append(gw)
            gw_out.append(gw+1)

transfer_out_df = pd.DataFrame({
    'teamId':teamIdList,
    'playerId':playerIdList,
    'gw':gwList,
    'sold':gw_out,
})
# merge transfer in and out gameweeks to main dataframe
player_data_df = player_data_df.merge(transfer_in_df, left_on=['playerId','teamId', 'gw'], right_on=['playerId','teamId','gw'], how='left')
player_data_df = player_data_df.merge(transfer_out_df, left_on=['playerId', 'teamId', 'gw'], right_on=['playerId','teamId','gw'], how='left')
# fill nan values with in and out values for the weeks where the player didn't transfer
player_data_df.bought=player_data_df.groupby(['web_name', 'name']).bought.apply(lambda x : x.ffill().bfill())
player_data_df.sold=player_data_df.sort_values('gw', ascending=False).groupby(['web_name', 'name']).sold.apply(lambda x : x.ffill().bfill())
# fix values where sold gw is earlier than bought. Issue for when a previously owned player comes back into team but hasnt been sold yet
player_data_df['sold'] = np.where(player_data_df.sold < player_data_df.bought, np.nan, player_data_df.sold)


player_data_df.to_csv('draft_data.csv')