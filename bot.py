import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import os
from flask import Flask
from threading import Thread

# --- 1. SISTEMA KEEP ALIVE (PARA FICAR 24/7) ---
app = Flask('')
@app.route('/')
def home(): return "Bot UIBAI Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURAÇÃO SEGURA ---
# Usando o cofre do Render para proteger seu Token
TOKEN = os.getenv('DISCORD_TOKEN') 
COR_ROXA = 0x8e44ad 
URL_LOGO = "https://cdn.discordapp.com/attachments/1468161206152986705/1468192059679834206/uibai_dog.png"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
queues = {}
partidas_ativas = {}

# --- 3. BANCO DE DADOS (JSON) ---
def carregar_ranking():
    if os.path.exists('ranking.json'):
        with open('ranking.json', 'r') as f: return json.load(f)
    return {}

def salvar_ranking(dados):
    with open('ranking.json', 'w') as f: json.dump(dados, f, indent=4)

def update_stats(user_id, win=0, loss=0, kills=0):
    dados = carregar_ranking()
    uid = str(user_id)
    if uid not in dados: dados[uid] = {"wins": 0, "losses": 0, "kills": 0}
    dados[uid]["wins"] += win
    dados[uid]["losses"] = dados[uid].get("losses", 0) + loss
    dados[uid]["kills"] = dados[uid].get("kills", 0) + kills
    salvar_ranking(dados)

# --- 4. INTERFACES (BOTÕES E FILA) ---
class QueueView(View):
    def __init__(self, q_id):
        super().__init__(timeout=None)
        self.q_id = q_id

    def gerar_embed(self):
        fila = queues.get(self.q_id, [])
        nomes = "\n".join([f"👤 {p.name}" for p in fila]) if fila else "Fila vazia..."
        embed = discord.Embed(title=f"🕹️ Fila: {self.q_id}", color=0x2b2d31)
        embed.description = f"Aguardando jogadores para iniciar {self.q_id}.\n\n**Jogadores ({len(fila)})**\n{nomes}\n\nUIBAI APOSTAS"
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        if self.q_id not in queues: queues[self.q_id] = []
        if interaction.user in queues[self.q_id]: 
            return await interaction.response.send_message("Você já está na fila!", ephemeral=True)
        
        queues[self.q_id].append(interaction.user)
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.danger)
    async def leave(self, interaction, button):
        if self.q_id in queues and interaction.user in queues[self.q_id]:
            queues[self.q_id].remove(interaction.user)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
        else:
            await interaction.response.send_message("Você não está na fila!", ephemeral=True)

class SelectMenu(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(placeholder="Escolha a modalidade...", options=[
        discord.SelectOption(label="1x1 MOB 📱", value="1x1 MOB"),
        discord.SelectOption(label="2x2 MOB 📱", value="2x2 MOB"),
        discord.SelectOption(label="1x1 EMU 🖥️", value="1x1 EMU"),
        discord.SelectOption(label="2x2 MISTO 📱🖥️", value="2x2 MISTO"),
    ])
    async def callback(self, interaction, select):
        v = QueueView(select.values[0])
        await interaction.response.send_message(embed=v.gerar_embed(), view=v, ephemeral=True)

# --- 5. COMANDOS ---
@bot.command()
async def painel(ctx):
    embed = discord.Embed(title="🏆 UIBAI APOSTAS", color=COR_ROXA)
    embed.description = "Selecione abaixo a modalidade que deseja jogar para entrar na fila."
    await ctx.send(embed=embed, view=SelectMenu())

@bot.command(name="rk")
async def rk_ranking(ctx):
    d = carregar_ranking()
    r = sorted(d.items(), key=lambda x: x[1].get('kills', 0), reverse=True)[:3]
    m = ["🥇", "🥈", "🥉"]
    t = "".join([f"{m[i]} **{(await bot.fetch_user(u)).name}** — {s.get('kills',0)} abates\n" for i, (u, s) in enumerate(r)])
    await ctx.send(embed=discord.Embed(title="🎯 TOP 3 - ABATES", description=t or "Ranking vazio", color=COR_ROXA))

@bot.event
async def on_ready():
    print(f'✅ UIBAI APOSTAS ONLINE!')

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
