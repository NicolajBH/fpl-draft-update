import pandas as pd
from table2ascii import table2ascii, PresetStyle, Alignment

players_df = pd.read_csv('https://raw.githubusercontent.com/NicolajBH/fpl-draft-update/main/draft_data.csv')
players_df.drop(columns=players_df.columns[0], inplace=True)

# Monthly points
monthly_standings = players_df[['name', 'month', 'playerPoints']][(players_df['played'] == True)].groupby(['name', 'month']).sum('playerPoints').reset_index()
monthly_standings.reset_index(inplace=True)
monthly_standings.drop(columns=monthly_standings.columns[0], inplace=True)

# Cumulative sum overall points
total_points = players_df[players_df['played'] == True].groupby(['name', 'gw', 'month']).sum('playerPoints').reset_index()
total_points = total_points[['name', 'gw', 'month', 'playerPoints']]
total_points = total_points.rename(columns={'playerPoints':'GW Score'})
total_points['Total Points'] = total_points['GW Score'].groupby(total_points['name']).transform('cumsum')
total_points_eom = total_points.sort_values('Total Points', ascending=False).drop_duplicates(subset=['name','month'])

# Join the total points at the end of the month to the monthly standings df and add a monthly rank
monthly_standings = monthly_standings.merge(total_points_eom, left_on=['month', 'name'], right_on=['month', 'name'])
monthly_standings = monthly_standings.sort_values(['gw', 'playerPoints', 'Total Points'], ascending=[True, False, False])
monthly_standings['rank'] = monthly_standings.groupby('month')['playerPoints'].rank(method='first', ascending=False).astype(int)

# Format the dataframe
monthly_standings = monthly_standings.rename(columns={'playerPoints':'Month Score'}).reset_index()
monthly_standings.drop(columns=monthly_standings.columns[0], inplace=True)
monthly_standings = monthly_standings[['name', 'month', 'Month Score', 'rank', 'Total Points']]

# Add the top scoring player for each person every month
top_player = players_df.sort_values('monthlyPoints', ascending=False).drop_duplicates(subset=('name', 'month'))
top_player = top_player.sort_values('deadline')
top_player = top_player[['web_name', 'short_name', 'month', 'name', 'monthlyPoints']]
monthly_standings = monthly_standings.merge(top_player, left_on=['name','month'], right_on=['name', 'month'])

current_month = players_df.sort_values('deadline', ascending=False).values[0][12]
monthList = players_df.month.drop_duplicates().values.tolist()

def standings(month):
    '''
    This function formats the monthly_standings dataframe into ascii format for discord output
    '''
    monthly_df = monthly_standings[['name','Month Score', 'short_name', 'rank']][monthly_standings['month'] == month]
    
    first_place = monthly_df[monthly_df['rank'] == 1].values.flatten().tolist()[:-1]
    second_place = monthly_df[monthly_df['rank'] == 2].values.flatten().tolist()[:-1]
    third_place = monthly_df[monthly_df['rank'] == 3].values.flatten().tolist()[:-1]
    fourth_place = monthly_df[monthly_df['rank'] == 4].values.flatten().tolist()[:-1]
    fifth_place = monthly_df[monthly_df['rank'] == 5].values.flatten().tolist()[:-1]
    
    monthlyTable = table2ascii(
        header=["Name", "Pts", "Player"],
        body=[first_place, second_place, third_place, fourth_place, fifth_place],
        alignments=[Alignment.LEFT, Alignment.LEFT, Alignment.LEFT],
        style=PresetStyle.borderless
        )
    return monthlyTable

monthlyTables = {}
for i in monthList:
    monthlyTables[i] = standings(i)

def player_top5_month(player):
    '''
    This function returns the top 5 players for the current month for player.
    The dataframe is converted to ascii format
    player = ['Mattia', 'Ollie', 'Nicolaj', 'Kris', 'Jesus']
    '''
    player_top_5 = players_df[(players_df.month==current_month) & (players_df.name==player)]\
        .sort_values(['monthlyPoints','draft_rank'], ascending=[False, True])\
        .drop_duplicates(subset=['web_name']).head()
    player_top_5 = player_top_5[['web_name', 'monthlyPoints']].reset_index()
    player_top_5.drop(columns=player_top_5.columns[0], inplace=True)
    player_top_5.rename(columns={'web_name':'Player','monthlyPoints':'Points'}, inplace=True)
    player_top_5.index += 1
    
    player1 = player_top_5.loc[1, :].values.flatten().tolist()
    player2 = player_top_5.loc[2, :].values.flatten().tolist()
    player3 = player_top_5.loc[3, :].values.flatten().tolist()
    player4 = player_top_5.loc[4, :].values.flatten().tolist()
    player5 = player_top_5.loc[5, :].values.flatten().tolist()
    
    playerTop5 = table2ascii(
        header=["Player", "Points"],
        body=[player1, player2, player3, player4, player5],
        first_col_heading=False,
        alignments=[Alignment.LEFT, Alignment.LEFT],
        style=PresetStyle.borderless)
    return playerTop5

nameList = list(monthly_standings.name.unique())
playerTop5 = {}
for i in nameList:
    playerTop5[i] = player_top5_month(i)