import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from flask import Flask
from threading import Thread
import json

# --- KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÃO E DADOS ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad
queues = {}

# Simulação de banco de dados para o comando !p
def carregar_dados():
    try:
        with open('stats.json', 'r') as f: return json.load(f)
    except: return {}

def salvar_dados(dados):
    with open('stats.json', 'w') as f: json.dump(dados, f)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BOTÃO PARA FECHAR CHAT ---
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Partida", style=discord.ButtonStyle.grey, emoji="🔒")
    async def close(self, interaction, button):
        await interaction.response.send_message("Este canal será excluído em 5 segundos...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))
        await interaction.channel.delete()

# --- SISTEMA DE FILA ---
class QueueView(View):
    def __init__(self, modalidade):
        super().__init__(timeout=None)
        self.modalidade = modalidade

    def atualizar_embed(self):
        fila = queues.get(self.modalidade, [])
        nomes = "\n".join([f"👤 {p.name}" for p in fila]) if fila else "Fila vazia..."
        embed = discord.Embed(title=f"🕹️ Fila: {self.modalidade}", color=COR_ROXA)
        embed.description = f"**Jogadores ({len(fila)})**\n{nomes}"
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green)
    async def entrar(self, interaction, button):
        if self.modalidade not in queues: queues[self.modalidade] = []
        if interaction.user in queues[self.modalidade]: return
        
        queues[self.modalidade].append(interaction.user)
        
        if len(queues[self.modalidade]) >= 2:
            p1 = queues[self.modalidade].pop(0)
            p2 = queues[self.modalidade].pop(0)
            
            # ADMs e Bot sempre veem os canais
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                p1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                p2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            # Adiciona permissão para quem tem cargo de Administrador
            for role in interaction.guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True)

            channel = await interaction.guild.create_text_channel(name=f"🏆-partida-{self.modalidade}", overwrites=overwrites)
            await channel.send(f"🎮 **Partida Iniciada!**\n{p1.mention} vs {p2.mention}", view=CloseView())
            await interaction.response.send_message(f"✅ Sala criada: {channel.mention}", ephemeral=False)
        else:
            await interaction.response.edit_message(embed=self.atualizar_embed())

# --- EVENTOS E COMANDOS SOLICITADOS ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # 1. Detectar números para copiar ID
    linhas = message.content.split('\n')
    if len(linhas) >= 2 and linhas[0].isdigit():
        embed = discord.Embed(title="📋 Copiar ID", description=f"```\n{linhas[0]}\n```", color=COR_ROXA)
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

@bot.command()
async def p(ctx, member: discord.Member = None):
    member = member or ctx.author
    dados = carregar_dados()
    user_data = dados.get(str(member.id), {"v": 0, "d": 0, "k": 0})
    
    embed = discord.Embed(title=f"👤 Perfil: {member.name}", color=COR_ROXA)
    embed.add_field(name="Vitórias 🏆", value=user_data["v"])
    embed.add_field(name="Derrotas 💀", value=user_data["d"])
    embed.add_field(name="Kills 🎯", value=user_data["k"])
    await ctx.send(embed=embed)

@bot.command()
async def winner(ctx):
    # Lógica de vencedor (quem usa ganha vitória, o outro derrota)
    if "partida" not in ctx.channel.name: return
    
    dados = carregar_dados()
    vencedor = ctx.author
    # Tenta achar o outro jogador mencionado na sala
    async for msg in ctx.channel.history(oldest_first=True, limit=1):
        jogadores = msg.mentions
        if len(jogadores) >= 2:
            perdedor = jogadores[1] if jogadores[0] == vencedor else jogadores[0]
            
            # Atualiza Vencedor
            d_v = dados.get(str(vencedor.id), {"v": 0, "d": 0, "k": 0})
            d_v["v"] += 1
            dados[str(vencedor.id)] = d_v
            
            # Atualiza Perdedor
            d_p = dados.get(str(perdedor.id), {"v": 0, "d": 0, "k": 0})
            d_p["d"] += 1
            dados[str(perdedor.id)] = d_p
            
            salvar_dados(dados)
            await ctx.send(f"🏆 {vencedor.mention} venceu a partida!")

@bot.command()
async def painel(ctx):
    class Menu(View):
        @discord.ui.select(placeholder="Escolha a modalidade...", options=[
            discord.SelectOption(label="1x1 MOB 📱", value="1x1 MOB"),
            discord.SelectOption(label="2x2 MOB 📱", value="2x2 MOB"),
            discord.SelectOption(label="3x3 MOB 📱", value="3x3 MOB"),
            discord.SelectOption(label="4x4 MOB 📱", value="4x4 MOB"),
            discord.SelectOption(label="2x2 MISTO 1 EMU 📱🖥️", value="2x2 MISTO 1 EMU"),
            discord.SelectOption(label="3X3 MISTO 1 EMU 📱🖥️", value="3X3 MISTO 1 EMU"),
            discord.SelectOption(label="4X4 MISTO 1 EMU 📱🖥️", value="4X4 MISTO 1 EMU"),
            discord.SelectOption(label="3X3 MISTO 2 EMU 📱🖥️", value="3X3 MISTO 2 EMU"),
            discord.SelectOption(label="4X4 MISTO 3 EMU 📱🖥️", value="4X4 MISTO 3 EMU"),
            discord.SelectOption(label="1X1 EMU 🖥️", value="1X1 EMU"),
            discord.SelectOption(label="2X2 EMU 🖥️", value="2X2 EMU"),
            discord.SelectOption(label="3X3 EMU 🖥️", value="3X3 EMU"),
            discord.SelectOption(label="4X4 EMU 🖥️", value="4X4 EMU")
        ])
        async def callback(self, interaction, select):
            v = QueueView(select.values[0])
            await interaction.response.send_message(embed=v.atualizar_embed(), view=v, ephemeral=False)

    await ctx.send(embed=discord.Embed(title="🏆 UIBAI APOSTAS", color=COR_ROXA), view=Menu())

@bot.event
async def on_ready(): print(f'✅ Bot Online!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
