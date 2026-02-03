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
    with open('stats.json', 'w') as f:
        json.dump(dados, f) # CORREÇÃO: Linha 33 parêntese fechado corretamente

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# --- BOTÕES E INTERFACE ---
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
        try: await interaction.channel.delete()
        except: pass

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
        
        # CORREÇÃO: Linha 73 sintaxe de comparação completa
        if len(queues[self.modalidade]) >= 2:
            p1_id = queues[self.modalidade].pop(0)
            p2_id = queues[self.modalidade].pop(0)
            p1, p2 = await bot.fetch_user(p1_id), await bot.fetch_user(p2_id)
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                p1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                p2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await interaction.guild.create_text_channel(name=f"🏆-{self.modalidade.replace(' ', '-')}", overwrites=overwrites)
            await channel.send(f"🎮 **Partida Iniciada!**\n{p1.mention} vs {p2.mention}", view=CloseView())
            await interaction.response.edit_message(embed=self.gerar_embed())
        else:
            await interaction.response.edit_message(embed=self.gerar_embed())

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red)
    async def sair(self, interaction, button):
        if self.modalidade in queues and interaction.user.id in queues[self.modalidade]:
            queues[self.modalidade].remove(interaction.user.id)
            await interaction.response.edit_message(embed=self.gerar_embed())
        else:
            await interaction.response.send_message("Você não está na fila!", ephemeral=True)

# --- COMANDOS ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    linhas = message.content.split('\n')
    if len(linhas) >= 2 and linhas[0].strip().isdigit():
        id_sala = linhas[0].strip()
        senha_sala = linhas[1].strip()
        embed = discord.Embed(title="🎮 DADOS DA SALA", color=COR_ROXA)
        embed.description = f"**ID:** `{id_sala}`\n**SENHA:** `{senha_sala}`"
        try: await message.delete()
        except: pass
        await message.channel.send(embed=embed, view=CopyIDView(id_sala))
    await bot.process_commands(message)

@bot.command()
async def painel(ctx):
    class SelectMenu(View):
        @discord.ui.select(placeholder="Escolha a modalidade...", options=[
            discord.SelectOption(label="1x1 MOB 📱", value="1x1 MOB"),
            discord.SelectOption(
