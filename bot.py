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
def keep_alive():
    t = Thread(target=run).start()

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad
queues = {}
md3_control = {} # Armazena placar da MD3 {canal_id: {player1_id: wins, player2_id: wins}}

def carregar_dados():
    try:
        with open('stats.json', 'r') as f: return json.load(f)
    except: return {}

def salvar_dados(dados):
    with open('stats.json', 'w') as f: json.dump(dados, f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BOTÕES ---
class CopyIDView(View):
    def __init__(self, text_to_copy):
        super().__init__(timeout=None)
        self.text_to_copy = text_to_copy

    @discord.ui.button(label="Copiar ID", style=discord.ButtonStyle.grey, emoji="📋")
    async def copy(self, interaction, button):
        # Como o Discord não permite copiar para o clipboard via bot, 
        # enviamos o ID de forma que facilite o clique no celular.
        await interaction.response.send_message(f"`{self.text_to_copy}`", ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Partida", style=discord.ButtonStyle.red, emoji="🔒")
    async def close(self, interaction, button):
        await interaction.response.send_message("Limpando sala em 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- COMANDOS ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Sistema de ID e Senha (Envia apenas 1 vez com botão)
    linhas = message.content.split('\n')
    if len(linhas) >= 2 and linhas[0].strip().isdigit():
        id_sala = linhas[0].strip()
        senha_sala = linhas[1].strip()
        embed = discord.Embed(title="🎮 DADOS DA SALA", color=COR_ROXA)
        embed.description = f"**ID:** `{id_sala}`\n**SENHA:** `{senha_sala}`"
        await message.delete() # Deleta a mensagem original para não poluir
        await message.channel.send(embed=embed, view=CopyIDView(id_sala))
        
    await bot.process_commands(message)

@bot.command()
async def winner(ctx):
    if "🏆" not in ctx.channel.name: return
    
    dados = carregar_dados()
    vencedor = ctx.author
    
    # Localiza quem são os jogadores da sala através da primeira mensagem do bot
    async for msg in ctx.channel.history(oldest_first=True, limit=5):
        if "vs" in msg.content and msg.author == bot.user:
            jogadores = msg.mentions
            if len(jogadores) < 2: return
            
            perdedor = jogadores[1] if jogadores[0] == vencedor else jogadores[0]
            
            # Se estiver em modo MD3
            if ctx.channel.id in md3_control:
                status = md3_control[ctx.channel.id]
                status[vencedor.id] = status.get(vencedor.id, 0) + 1
                
                v_wins = status[vencedor.id]
                p_wins = status.get(perdedor.id, 0)
                
                embed = discord.Embed(title="📊 PLACAR MD3", color=COR_ROXA)
                embed.description = f"{vencedor.mention}: **{v_wins} Win**\n{perdedor.mention}: **{p_wins} Win**"
                
                if v_wins >= 2:
                    embed.title = "🏆 FIM DA MD3"
                    await ctx.send(embed=embed)
                    # Adiciona estatísticas oficiais ao perfil apenas no fim da MD3
                    d_v = dados.get(str(vencedor.id), {"v":0,"d":0,"k":0})
                    d_v["v"] += 1
                    dados[str(vencedor.id)] = d_v
                    d_p = dados.get(str(perdedor.id), {"v":0,"d":0,"k":0})
                    d_p["d"] += 1
                    dados[str(perdedor.id)] = d_p
                    salvar_dados(dados)
                    del md3_control[ctx.channel.id]
                    await ctx.send("Partida finalizada! Use o botão para fechar.", view=CloseView())
                else:
                    await ctx.send(embed=embed)
                    await ctx.send("Mande o próximo ID e Senha para a próxima rodada!")
                return

            # Modo Normal (Sem MD3)
            d_v = dados.get(str(vencedor.id), {"v":0,"d":0,"k":0})
            d_v["v"] += 1
            dados[str(vencedor.id)] = d_v
            
            d_p = dados.get(str(perdedor.id), {"v":0,"d":0,"k":0})
            d_p["d"] += 1
            dados[str(perdedor.id)] = d_p
            
            salvar_dados(dados)
            await ctx.send(f"🏆 {vencedor.mention} venceu a partida!", view=CloseView())
            break

@bot.command()
async def md3(ctx):
    if "🏆" not in ctx.channel.name: return
    
    # Inicia o controle de MD3 para este canal
    async for msg in ctx.channel.history(oldest_first=True, limit=5):
        if "vs" in msg.content and msg.author == bot.user:
            jogadores = msg.mentions
            if len(jogadores) >= 2:
                md3_control[ctx.channel.id] = {jogadores[0].id: 0, jogadores[1].id: 0}
                embed = discord.Embed(title="⚔️ MD3 INICIADA", color=COR_ROXA)
                embed.description = f"O primeiro a vencer 2 rodadas ganha a vitória no perfil!\n\n{jogadores[0].mention}: 0\n{jogadores[1].mention}: 0"
                await ctx.send(embed=embed)
                return

@bot.command()
async def p(ctx, member: discord.Member = None):
    member = member or ctx.author
    dados = carregar_dados()
    u = dados.get(str(member.id), {"v": 0, "d": 0, "k": 0})
    embed = discord.Embed(title=f"👤 Perfil: {member.name}", color=COR_ROXA)
    embed.add_field(name="Vitórias 🏆", value=u["v"])
    embed.add_field(name="Derrotas 💀", value=u["d"])
    await ctx.send(embed=embed)

@bot.event
async def on_ready(): print(f'✅ Bot Online!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
