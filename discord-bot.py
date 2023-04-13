import discord
from discord.ext import commands 
from discord import app_commands
from discord.app_commands import Choice

from config import TOKEN
from typing import Literal, Optional
from sqlalchemy import create_engine
import pandas as pd

# player names and entry ids
players = {15606:'Nicolaj',24788:'Jesus',42118:'Kris',154393:'Mattia',16133:'Ollie'}
# create engine
engine = create_engine('sqlite:///fpl-draft-db.db')

overall_table = pd.read_sql('overall_table', engine)
player_picks = pd.read_sql('picks_detailed',engine)
months = list(overall_table.month.unique())

def monthly_table(month):    
    df = overall_table[overall_table.month==month]
    df = df[df.gw==df.gw.max()].sort_values(by=['monthly_rank','overall_rank'])
    df = df[['team_id','eom_pts','month_top_scorer','player_cum_pts']].reset_index(drop=True)
    df = df.replace({'team_id': players})
    df = df.rename(columns={'team_id':'Manager','eom_pts':'Monthly Points','month_top_scorer':'Top Scorer','player_cum_pts':'Points'})
    df.index += 1
    return df

def top5_player(name):
    d_swap = {v: k for k, v in players.items()}
    team_id = d_swap[name]
    top5 = player_picks.copy()
    top5['player_cum_pts'] = top5.groupby(['team_id','element','month'])['stats.total_points'].cumsum()
    top5 = top5[top5.gw == top5.gw.max()].sort_values(by=['player_cum_pts','draft_rank'],ascending=[False,True])
    top5 = top5[top5.team_id == team_id]
    top5 = top5.replace({'team_id':players})
    top5 = top5.rename(columns={'team_id':'Team','web_name':'Player','player_cum_pts':'Points'}).reset_index(drop=True)
    top5.index += 1
    return top5[['Team','Player','Points']].head()

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print('Bot is up and ready!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

# Slash command to return monthly tables. Lets user choose which month they want
@app_commands.choices(month = 
   [Choice(name=x, value=x) for x in months]
)
@bot.tree.command(description='Returns monthly table')
async def monthly_table(interaction: discord.Interaction, month:Choice[str]):
   embed = discord.Embed(title='Monthly Standings', description="")
   embed.add_field(name=month.name,value=monthly_table[month.name])
   await interaction.response.send_message(embed=embed)

# Slash command to return top 5 scoring players. Lets user choose which person they want to see top scorers for
@bot.tree.command(description='Returns top 5 players')
async def top_scorers(
   interaction: discord.Interaction, 
   manager:Literal['Nicolaj', 'Ollie', 'Kris', 'Jesus', 'Mattia']):
   embed = discord.Embed(title='Top Scorers', description="")
   embed.add_field(name=manager,value=top5_player[manager])
   await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
