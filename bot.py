import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import os
from flask import Flask
from threading import Thread

# --- KEEP ALIVE ---
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

# --- FILA ---
class QueueView(View):
    def __init__(self, modalidade):
        super().__init__(timeout=None)
        self.modalidade = modalidade
    
    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green)
    async def entrar(self, interaction, button):
        await interaction.response.send_message(f"Você entrou na fila de {self.modalidade}!", ephemeral=True)

# --- COMANDOS ---
@bot.command()
async def painel(ctx):
    class Menu(View):
        @discord.ui.select(placeholder="Escolha a modalidade...", options=[
            discord.SelectOption(label="1x1 MOB", value="1x1 MOB"),
            discord.SelectOption(label="2x2 MOB", value="2x2 MOB")
        ])
        async def callback(self, interaction, select):
            await interaction.response.send_message(f"Fila de {select.values[0]} aberta!", view=QueueView(select.values[0]))

    await ctx.send(embed=discord.Embed(title="🏆 UIBAI APOSTAS", color=COR_ROXA), view=Menu())

@bot.command()
async def rv(ctx):
    await ctx.send(embed=discord.Embed(title="🏆 RANKING VITÓRIAS", description="1º Player - 0 vitórias", color=COR_ROXA))

@bot.command()
async def rk(ctx):
    await ctx.send(embed=discord.Embed(title="🎯 RANKING KILLS", description="1º Player - 0 kills", color=COR_ROXA))

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ONLINE!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
