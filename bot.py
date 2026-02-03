import discord
from discord.ext import commands
from discord.ui import Button, View
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

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad
md3_control = {} # Placar: {canal_id: {player1_id: wins, player2_id: wins}}

def carregar_dados():
    try:
        with open('stats.json', 'r') as f: return json.load(f)
    except: return {}

def salvar_dados(dados):
    with open('stats.json', 'w') as f: json.dump(dados, f)

# case_insensitive=True resolve o erro do log 111
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

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

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Sistema de ID e Senha: Manda apenas 1 quadro
    linhas = message.content.split('\n')
    if len(linhas) >= 2 and linhas[0].strip().isdigit():
        id_sala, senha_sala = linhas[0].strip(), linhas[1].strip()
        embed = discord.Embed(title="🎮 DADOS DA SALA", color=COR_ROXA)
        embed.description = f"**ID:** `{id_sala}`\n**SENHA:** `{senha_sala}`"
        try: await message.delete() # Apaga a mensagem original para não duplicar
        except: pass
        await message.channel.send(embed=embed, view=CopyIDView(id_sala))
        
    await bot.process_commands(message)

@bot.command()
async def winner(ctx):
    if "🏆" not in ctx.channel.name: return
    dados, vencedor = carregar_dados(), ctx.author
    
    async for msg in ctx.channel.history(oldest_first=True, limit=5):
        if "vs" in msg.content and msg.author == bot.user:
            jogadores = msg.mentions
            if len(jogadores) < 2: return
            perdedor = jogadores[1] if jogadores[0] == vencedor else jogadores[0]
            
            # Lógica MD3
            if ctx.channel.id in md3_control:
                status = md3_control[ctx.channel.id]
                status[vencedor.id] = status.get(vencedor.id, 0) + 1
                v_w, p_w = status[vencedor.id], status.get(perdedor.id, 0)
                
                embed = discord.Embed(title="📊 PLACAR MD3", color=COR_ROXA)
                embed.description = f"{vencedor.mention}: **{v_w} Win**\n{perdedor.mention}: **{p_w} Win**"
                await ctx.send(embed=embed)

                if v_w >= 2:
                    await ctx.send(f"🏆 {vencedor.mention} atingiu 2 Wins e ganhou a MD3!")
                    d_v = dados.get(str(vencedor.id), {"v":0,"d":0,"k":0})
                    d_v["v"] += 1
                    dados[str(vencedor.id)] = d_v
                    d_p = dados.get(str(perdedor.id), {"v":0,"d":0,"k":0})
                    d_p["d"] += 1
                    dados[str(perdedor.id)] = d_p
                    salvar_dados(
