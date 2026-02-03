import discord
from discord.ext import commands
from discord.ui import Button, View, Select
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
queues = {} # Dicionário para guardar as filas

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SISTEMA DE FILA E SALAS ---
class QueueView(View):
    def __init__(self, modalidade):
        super().__init__(timeout=None)
        self.modalidade = modalidade

    def atualizar_embed(self):
        fila = queues.get(self.modalidade, [])
        nomes = "\n".join([f"👤 {p.name}" for p in fila]) if fila else "Fila vazia..."
        embed = discord.Embed(title=f"🕹️ Fila: {self.modalidade}", color=COR_ROXA)
        embed.description = f"Aguardando jogadores...\n\n**Jogadores ({len(fila)})**\n{nomes}"
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green)
    async def entrar(self, interaction, button):
        if self.modalidade not in queues: queues[self.modalidade] = []
        if interaction.user in queues[self.modalidade]:
            return await interaction.response.send_message("Você já está na fila!", ephemeral=True)

        queues[self.modalidade].append(interaction.user)
        
        # Se atingir 2 jogadores, cria o canal
        if len(queues[self.modalidade]) >= 2:
            p1 = queues[self.modalidade].pop(0)
            p2 = queues[self.modalidade].pop(0)
            
            # Criar canal privado
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                p1: discord.PermissionOverwrite(read_messages=True),
                p2: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await interaction.guild.create_text_channel(name=f"🏆-aposta-{self.modalidade}", overwrites=overwrites)
            await channel.send(f"🎮 **Partida Iniciada!**\nJogadores: {p1.mention} vs {p2.mention}\nBoa sorte!")
            await interaction.response.send_message(f"✅ Sala criada: {channel.mention}", ephemeral=False)
        else:
            await interaction.response.edit_message(embed=self.atualizar_embed())

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red)
    async def sair(self, interaction, button):
        if self.modalidade in queues and interaction.user in queues[self.modalidade]:
            queues[self.modalidade].remove(interaction.user)
            await interaction.response.edit_message(embed=self.atualizar_embed())
        else:
            await interaction.response.send_message("Você não está na fila!", ephemeral=True)

# --- PAINEL PRINCIPAL ---
@bot.command()
async def painel(ctx):
    class Menu(View):
        @discord.ui.select(placeholder="Escolha a modalidade...", options=[
            discord.SelectOption(label="1x1 MOB 📱", value="1x1 MOB"),
            discord.SelectOption(label="2x2 MOB 📱", value="2x2 MOB"),
            discord.SelectOption(label="1x1 EMU 🖥️", value="1x1 EMU"),
            discord.SelectOption(label="2x2 EMU 🖥️", value="2x2 EMU"),
            discord.SelectOption(label="MISTO 📱🖥️", value="MISTO")
        ])
        async def callback(self, interaction, select):
            v = QueueView(select.values[0])
            # ephemeral=False para todos verem a fila aberta
            await interaction.response.send_message(embed=v.atualizar_embed(), view=v, ephemeral=False)

    await ctx.send(embed=discord.Embed(title="🏆 UIBAI APOSTAS", description="Selecione abaixo para jogar:", color=COR_ROXA), view=Menu())

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ONLINE E PRONTO!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
