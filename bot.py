import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from flask import Flask
from threading import Thread

# --- SISTEMA KEEP ALIVE (PARA FICAR 24/7) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def painel(ctx):
    embed = discord.Embed(title="🏆 UIBAI APOSTAS", color=COR_ROXA)
    await ctx.send(embed=embed)

@bot.event
async def on_ready(): print(f'✅ BOT ONLINE NA NUVEM!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
