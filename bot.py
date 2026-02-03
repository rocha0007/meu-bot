import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from flask import Flask
from threading import Thread
import json
import asyncio

# --- KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- CONFIGURAÇÃO E DADOS ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad
queues = {}
md3_control = {}

def carregar_dados():
    try:
        with open('stats.json', 'r') as f: return json.load(f)
    except: return {}

def salvar_dados(dados):
    with open('stats.json', 'w') as f: json.dump(dados, f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# --- BOTÕES DE SALA ---
class CopyIDView(View):
    def __init__(self, text):
        super().__init__(timeout=None)
        self.text = text
    @discord.ui.button(label="Copiar ID", style=discord.ButtonStyle.grey, emoji="📋")
    async def copy(self, interaction, button):
        await interaction.response.send_message(f"`{self.text}`", ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Fechar Partida", style=discord.ButtonStyle.red, emoji="🔒")
    async def close(self, interaction, button):
        await interaction.response.send_message("Limpando sala em 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- SISTEMA DE FILA ---
class QueueView(View):
    def __init__(self, modalidade):
        super().__init__(timeout=None)
        self.modalidade = modalidade

    def gerar_embed(self):
        fila = queues.get(self.modalidade, [])
        nomes = "\n".join([f"👤 <@{p_id}>" for p_id in fila]) if fila else "Fila vazia..."
        embed = discord.Embed(title=f"🕹️ Fila: {self.modalidade}", color=COR_ROXA)
        embed.description = f"**Jogadores ({len(fila)})**\n{nomes}\n\nUIBAI APOSTAS"
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green)
    async def entrar(self, interaction, button):
        if self.modalidade not in queues: queues[self.modalidade] = []
        if interaction.user.id in queues[self.modalidade]:
            return await interaction.response.send_message("Você já está na fila!", ephemeral=True)
        
        queues[self.modalidade].append(interaction.user.id)
        
        if len(queues[self.modalidade]) >=
