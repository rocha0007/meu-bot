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
        json.dump(dados, f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# --- INTERFACE ---
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
            view = QueueView(select.values[0])
            await interaction.response.send_message(embed=view.gerar_embed(), view=view)
    await ctx.send(embed=discord.Embed(title="🏆 UIBAI APOSTAS", color=COR_ROXA), view=SelectMenu())

@bot.command()
async def winner(ctx):
    if "🏆" not in ctx.channel.name: return
    dados, vencedor = carregar_dados(), ctx.author
    async for msg in ctx.channel.history(oldest_first=True, limit=10):
        if "vs" in msg.content and msg.author == bot.user:
            jogadores = msg.mentions
            if len(jogadores) < 2: return
            perdedor = jogadores[1] if jogadores[0] == vencedor else jogadores[0]
            
            d_v = dados.get(str(vencedor.id), {"v":0,"d":0})
            d_p = dados.get(str(perdedor.id), {"v":0,"d":0})
            d_v["v"] += 1
            d_p["d"] += 1
            dados[str(vencedor.id)], dados[str(perdedor.id)] = d_v, d_p
            salvar_dados(dados)

            if ctx.channel.id in md3_control:
                status = md3_control[ctx.channel.id]
                status[vencedor.id] = status.get(vencedor.id, 0) + 1
                v_w, p_w = status[vencedor.id], status.get(perdedor.id, 0)
                
                embed = discord.Embed(title="📊 PLACAR MD3", color=COR_ROXA)
                embed.description = f"{vencedor.mention}: **{v_w} Win**\n{perdedor.mention}: **{p_w} Win**"
                await ctx.send(embed=embed)
                
                if v_w >= 2:
                    await ctx.send(f"🏆 {vencedor.mention} venceu a MD3!", view=CloseView())
                    del md3_control[ctx.channel.id]
                return

            await ctx.send(f"🏆 {vencedor.mention} venceu!", view=CloseView())
            break

@bot.command()
async def rv(ctx):
    dados = carregar_dados()
    if not dados: return await ctx.send("Sem dados registrados.")
    ranking = sorted(dados.items(), key=lambda item: item[1].get('v', 0), reverse=True)
    top_3 = ranking[:3]
    embed = discord.Embed(title="🏆 TOP 3 - RANK DE VITÓRIAS", color=COR_ROXA)
    medalhas, desc = ["🥇", "🥈", "🥉"], ""
    for i, (user_id, stats) in enumerate(top_3):
        desc += f"{medalhas[i]} <@{user_id}> — **{stats.get('v', 0)} Vitórias**\n"
    embed.description = desc if desc else "Ranking vazio."
    await ctx.send(embed=embed)

@bot.command()
async def md3(ctx):
    if "🏆" not in ctx.channel.name: return
    async for msg in ctx.channel.history(oldest_first=True, limit=5):
        if "vs" in msg.content and msg.author == bot.user:
            jogadores = msg.mentions
            if len(jogadores) >= 2:
                md3_control[ctx.channel.id] = {jogadores[0].id: 0, jogadores[1].id: 0}
                await ctx.send(f"⚔️ **MD3 Iniciada!**")
                return

@bot.command()
async def p(ctx, member: discord.Member = None):
    member = member or ctx.author
    u = carregar_dados().get(str(member.id), {"v": 0, "d": 0})
    embed = discord.Embed(title=f"👤 Perfil: {member.name}", color=COR_ROXA)
    embed.add_field(name="Vitórias 🏆", value=u["v"])
    embed.add_field(name="Derrotas 💀", value=u["d"])
    await ctx.send(embed=embed)

@bot.event
async def on_ready(): print(f'✅ Bot Online!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
