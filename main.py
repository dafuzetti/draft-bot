from discord.ext import commands
import discord
import os
# python3 - m pip install - U discord.py


intents = discord.Intents.default()
discord.Intents.all()
client = discord.Client(intents=intents)

my_secret = os.environ['TOKEN']
bot = commands.Bot(command_prefix='!', intents=intents)


@client.event
async def on_ready():
    print('rodou! {0.user}'.format(client))


@bot.command(name='win')
async def win(ctx):
    print("Chamou")
    await ctx.send('ok!')

client.run(my_secret)
