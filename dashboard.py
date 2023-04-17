import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import streamlit as st

# player names and entry ids
players = {15606:'Nicolaj',24788:'Jesus',42118:'Kris',154393:'Mattia',16133:'Ollie'}
# create engine
engine = create_engine('sqlite:///fpl-draft-db.db')
conn = engine.connect()

draft_player_info = pd.read_sql_table('draft_player_info', conn)
fantasy_player_info = pd.read_sql_table('fantasy_player_info',conn)
player_picks = pd.read_sql_table('player_picks',conn)
deadlines = pd.read_sql_table('deadlines',conn)
player_stats = pd.read_sql_table('player_stats',conn)

# match ids in draft player info with fantasy player info
draft_player_info = draft_player_info[['id','first_name','second_name','web_name','draft_rank','element_type', 'team']]
fantasy_player_info = fantasy_player_info[['id','first_name','second_name','web_name','element_type', 'team']]
player_info = draft_player_info.merge(fantasy_player_info, on=['first_name','second_name','web_name','element_type','team'])
player_info = player_info.rename(columns={'id_x':'draft_id','id_y':'fpl_id'})

# player stat dtypes
convert_dict = {col:'float' for col in player_stats.select_dtypes('object').columns.to_list()}
player_stats = player_stats.astype(convert_dict)

# merge player picks with player info, stats and deadlines, add cumulative points
picks_detailed = player_picks.merge(player_info, left_on='element', right_on='draft_id')
picks_detailed = picks_detailed.merge(player_stats, left_on=['fpl_id','gw'], right_on=['id', 'gw']).drop(columns=['id'])
picks_detailed = picks_detailed.merge(deadlines[['deadline_time','month','id']], left_on=['gw'], right_on=['id']).drop(columns=['id'])

# overall table

ppm = picks_detailed.copy()
ppm = picks_detailed[picks_detailed.played==True] # only include points if they played
ppm = ppm[['team_id','gw','month','stats.total_points']]
ppm = ppm.groupby(['team_id','gw','month']).sum('stats.total_points').reset_index()

ppm['overall_points'] = ppm['stats.total_points'].groupby(ppm['team_id']).transform('cumsum')
ppm['overall_rank'] = ppm.groupby('gw')['overall_points'].rank(method='first', ascending=False).astype(int)

ppm['monthly_points'] = ppm.groupby(['team_id', 'month']).transform('cumsum')['stats.total_points']
ppm = ppm.merge(ppm.groupby(['team_id','month']).max()\
         .reset_index()[['monthly_points','team_id','month']], on=['team_id','month'],how='left')
ppm['monthly_rank'] = ppm.sort_values(by=['overall_rank']).groupby(['month','gw'])['monthly_points_x'].rank(method='first', ascending=False).astype(int)
ppm = ppm.rename(columns={'monthly_points_x':'cum_pts_month','monthly_points_y':'eom_pts'})

player_ppm = picks_detailed.copy()
player_ppm['player_cum_pts'] = player_ppm.groupby(['team_id', 'month', 'element'])['stats.total_points'].cumsum()
player_ppm = player_ppm.sort_values(by=['player_cum_pts','draft_rank'], ascending=[False,True])\
    .drop_duplicates(subset=['team_id','gw'])\
    .rename(columns={'web_name':'month_top_scorer'})

overall_table = ppm.merge(player_ppm[['month_top_scorer', 'gw', 'team_id','player_cum_pts']], on=['gw','team_id'],how='left')

def monthly_table(month):    
    df = overall_table[overall_table.month==month]
    df = df[df.gw==df.gw.max()].sort_values(by=['monthly_rank','overall_rank'])
    df = df[['team_id','eom_pts','month_top_scorer','player_cum_pts']].reset_index(drop=True)
    df = df.replace({'team_id': players})
    df = df.rename(columns={'team_id':'Manager','eom_pts':'Monthly Points','month_top_scorer':'Top Scorer','player_cum_pts':'Points'})
    df.index += 1
    return df

def month_top_players(name=list(players.values()),month=list(picks_detailed.month.unique())):
    ''''
    Function returns the top 5 scoring players for the given teams in the given months.
    If no month is given then top 5 for the whole season.
    If no name is given then include all teams
    '''
    d_swap = {v: k for k, v in players.items()}
    team_id = [d_swap.get(item,item)  for item in name]
    top_scorers = picks_detailed.copy()
    top_scorers = top_scorers[(picks_detailed.month.isin(month)) & (picks_detailed.team_id.isin(team_id))]
    top_scorers['player_cum_pts'] = top_scorers.groupby(['team_id','element'])['stats.total_points'].cumsum()
    top_scorers = top_scorers.sort_values(by='gw').drop_duplicates(subset=['team_id','element'],keep='last')
    top_scorers = top_scorers.sort_values(by=['player_cum_pts','draft_rank'], ascending=[False,True]).head(10)
    top_scorers = top_scorers[['team_id','web_name','player_cum_pts']].reset_index(drop=True)
    top_scorers = top_scorers.replace({'team_id':players})
    top_scorers = top_scorers.rename(columns={'team_id':'Name','web_name':'Player','player_cum_pts':'Points'})
    top_scorers.index += 1
    return top_scorers.head()

def form_guide(gws, stat):
    by_gw = picks_detailed.copy()
    by_gw = by_gw[by_gw.gw.between(gws[0],gws[1])]
    by_gw = by_gw.groupby(['element', 'team_id']).agg({'web_name':'first','team_id':'first',stat_col[stat]:'sum'})
    by_gw = by_gw.sort_values(by=[stat_col[stat]], ascending=False).reset_index(drop=True)
    by_gw = by_gw.replace({'team_id':players})
    by_gw = by_gw.rename(columns={'web_name':'Player','team_id':'Team',stat_col[stat]:stat_col[stat].replace("stats.","").title()})
    by_gw.index += 1
    return by_gw.head(10)

all_players = player_stats.merge(player_info, left_on='id', right_on='fpl_id',how='left').merge(deadlines[['deadline_time','month','id']], left_on=['gw'], right_on=['id'])

def all_stats(gws, stat):
    by_gw = all_players.copy()
    by_gw = by_gw[by_gw.gw.between(gws[0],gws[1])]
    by_gw = by_gw.groupby(['id_x']).agg({'web_name':'first',stat_col[stat]:'sum'})
    by_gw = by_gw.sort_values(by=[stat_col[stat]], ascending=False).reset_index(drop=True)
    by_gw = by_gw.rename(columns={'web_name':'Player',stat_col[stat]:stat_col[stat].replace("stats.","").title()})
    by_gw.index += 1
    return by_gw.head(10)

st.title('Clueless Dashboard')

st.header('Monthly Table')
months = list(picks_detailed.month.unique())
month_dropdown = st.selectbox('Pick month',months)
st.table(monthly_table(month_dropdown))


st.header('Top Scorers')
months_dropdown = st.multiselect('Select months', months)
manager_dropdown = st.multiselect('Twat', players.values())

if len(manager_dropdown) > 0 and len(months_dropdown) > 0:
    st.table(month_top_players(manager_dropdown,months_dropdown))
elif len(manager_dropdown) > 0 and len(months_dropdown) == 0:
    st.table(month_top_players(name=manager_dropdown))
elif len(manager_dropdown) == 0 and len(months_dropdown) > 0:
    st.table(month_top_players(month=months_dropdown))
else:
    st.table(month_top_players())


st.header('Player Stats')
min_gw = player_stats.gw.min()
max_gw = player_stats.gw.max()

stat_col = picks_detailed.filter(regex='stats').columns.to_list()
pretty = {e.replace('stats.','').title():e for e in stat_col}

stat_dropdown = st.selectbox('Select stat', pretty.keys(), key='select player stats')
stat = stat_col.index(pretty[stat_dropdown])
gws = st.slider('Select gameweeks',int(min_gw),int(max_gw), (int(min_gw),int(max_gw)), key='select players slider')

st.table(form_guide(gws,stat))

st.header('All Player Stats')

stat_dropdown2 = st.selectbox('Select stat', pretty.keys(), key='all player stats')
stat2 = stat_col.index(pretty[stat_dropdown2])
gws2 = st.slider('Select gameweeks',int(min_gw),int(max_gw), (int(min_gw),int(max_gw)), key='all players slider')

st.table(all_stats(gws2, stat2))