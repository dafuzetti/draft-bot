import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
discord.Intents.all()

my_secret = os.environ['TOKEN']
bot = commands.Bot(command_prefix='.', intents=intents)


@bot.command(pass_context=True, name='lose')
async def lose(ctx):
    await ctx.send('Hello!!')
    print('Perdeu')


@bot.command(name='win')
async def win(ctx):
    print('Chamou')
    await ctx.send('ok!')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(message.content)


@bot.event
async def on_ready():
    print('Logged ina as:')
    print(bot.user.name)
    await bot.change_presence()
    print('rodou! {0.user}'.format(bot))

bot.run(my_secret)
