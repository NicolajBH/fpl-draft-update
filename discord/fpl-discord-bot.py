import discord
from discord.ext import commands 
from discord import app_commands
from discord.app_commands import Choice
import config
from discordfunctions import monthlyTables, playerTop5, monthList
from typing import Literal, Optional

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
   [Choice(name=x, value=x) for x in monthList]
)
@bot.tree.command(description='Returns monthly table')
async def monthly_table(interaction: discord.Interaction, month:Choice[str]):
   embed = discord.Embed(title='Monthly Standings', description="")
   embed.add_field(name=month.name,value=f"```\n{monthlyTables[month.name]}\n```")
   await interaction.response.send_message(embed=embed)

# Slash command to return top 5 scoring players. Lets user choose which person they want to see top scorers for
@bot.tree.command(description='Returns top 5 players')
async def top_scorers(
   interaction: discord.Interaction, 
   manager:Literal['Nicolaj', 'Ollie', 'Kris', 'Jesus', 'Mattia']):
   embed = discord.Embed(title='Top Scorers', description="")
   embed.add_field(name=manager,value=f"```\n{playerTop5[manager]}\n```")
   await interaction.response.send_message(embed=embed)

bot.run(config.TOKEN)