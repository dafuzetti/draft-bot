import discord #import all the necessary modules
from discord import Game
from discord.ext import commands
import os

my_secret = os.environ['TOKEN']
bot = commands.Bot(command_prefix='!') #define command decorator

@bot.command(pass_context=True) #define the first command and set prefix to '!'
async def testt(ctx):
    await ctx.send('Hello!!')

@bot.event #print that the bot is ready to make sure that it actually logged on
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    await bot.change_presence(game=Game(name="in rain ¬ !jhelp"))

bot.run(TOKEN) #run the client using using my bot's token