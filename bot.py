import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from flask import Flask
from threading import Thread

# --- 1. KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot UIBAI Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURAÇÃO ---
TOKEN = os.getenv('DISCORD_TOKEN')
COR_ROXA = 0x8e44ad
queues = {} 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. SISTEMA DE FILA E SALAS PRIVADAS ---
class QueueView(View):
    def __init__(self, modalidade):
        super().__init__(timeout=None)
        self.modalidade = modalidade

    def gerar_embed(self):
        fila = queues.get(self.modalidade, [])
        nomes = "\n".join([f"👤 {p.name}" for p in fila]) if fila else "Fila vazia..."
        embed = discord.Embed(title=f"🕹️ Fila: {self.modalidade}", color=COR_ROXA)
        embed.description = f"Aguardando jogadores para iniciar.\n\n**Jogadores ({len(fila)})**\n{nomes}\n\nUIBAI APOSTAS"
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        if self.modalidade not in queues: queues[self.modalidade] = []
        if interaction.user in queues[self.modalidade]:
            return await interaction.response.send_message("Você já está nesta fila!", ephemeral=True)

        queues[self.modalidade].append(interaction.user)

        # Lógica simplificada de 2 jogadores para criar a sala (pode ser ajustada conforme a modalidade)
        if len(queues[self.modalidade]) >= 2:
            p1 = queues[self.modalidade].pop(0)
            p2 = queues[self.modalidade].pop(0)

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                p1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                p2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            channel = await interaction.guild.create_text_channel(
                name=f"🏆-{self.modalidade.replace(' ', '-')}",
                overwrites=overwrites
            )

            await channel.send(f"🎮 **PARTIDA FORMADA!**\n{p1.mention} ⚔️ {p2.mention}\n\nUsem este chat privado!")
            await interaction.response.send_message(f"✅ Sala criada: {channel.mention}", ephemeral=False)
        else:
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.danger)
    async def leave(self, interaction, button):
        if self.modalidade in queues and interaction.user in queues[self.modalidade]:
            queues[self.modalidade].remove(interaction.user)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
        else:
            await interaction.response.send_message("Você não está na fila!", ephemeral=True)

# --- 4. MENU COM AS FILAS CORRETAS ---
class SelectMenu(View):
    def __init__(self):
        super().__init__(timeout=None)

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
        discord.SelectOption(label="4X4 EMU 🖥️", value="4X4 EMU"),
    ])
    async def callback(self, interaction, select):
        view = QueueView(select.values[0])
        await interaction.response.send_message(embed=view.gerar_embed(), view=view, ephemeral=False)

# --- 5. COMANDOS ---
@bot.command()
async def painel(ctx):
    embed = discord.Embed(title="🏆 UIBAI APOSTAS", description="Selecione a modalidade abaixo:", color=COR_ROXA)
    await ctx.send(embed=embed, view=SelectMenu())

@bot.event
async def on_ready():
    print(f'✅ UIBAI APOSTAS ONLINE!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
