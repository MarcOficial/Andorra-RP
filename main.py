import discord
from discord import app_commands
import random
import string

# --- CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- BASE DE DATOS TEMPORAL ---
dnis = {}
carnets = {}

# --- FUNCIÓN PARA GENERAR DNI ---
def generar_dni():
    numeros = str(random.randint(10000000, 99999999))  # 8 dígitos
    letra = random.choice(string.ascii_uppercase)      # Una letra al azar
    return numeros + letra

# --- EVENTOS ---
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Andorra RP"))
    await tree.sync()
    print(f"✅ Bot conectado como {bot.user}")

# --- COMANDOS DE DNI ---
@tree.command(name="crear-dni", description="Crear un DNI automáticamente para un usuario")
@app_commands.describe(
    usuario="Usuario al que se le creará el DNI",
    nombre="Nombre de la persona",
    apellidos="Apellidos de la persona",
    fecha_nacimiento="Año de nacimiento (ej: 2000)",
    sexo="Sexo de la persona"
)
@app_commands.choices(sexo=[
    app_commands.Choice(name="Masculino", value="Masculino"),
    app_commands.Choice(name="Femenino", value="Femenino")
])
async def crear_dni(
    interaction: discord.Interaction,
    usuario: discord.Member,
    nombre: str,
    apellidos: str,
    fecha_nacimiento: str,
    sexo: app_commands.Choice[str]
):
    if usuario.id in dnis:
        await interaction.response.send_message(f"⚠️ {usuario.mention} ya tiene un DNI registrado.")
    else:
        dni = generar_dni()
        dnis[usuario.id] = {
            "nombre": nombre,
            "apellidos": apellidos,
            "fecha": fecha_nacimiento,
            "sexo": sexo.value,
            "dni": dni
        }
        await interaction.response.send_message(f"✅ DNI creado para {usuario.mention}")

@tree.command(name="ver-dni", description="Ver el DNI de un usuario")
async def ver_dni(interaction: discord.Interaction, usuario: discord.Member):
    if usuario.id in dnis:
        datos = dnis[usuario.id]
        embed = discord.Embed(
            title="🪪 DNI Virtual",
            color=discord.Color.blue()
        )
        embed.add_field(name="Nombre", value=datos["nombre"], inline=True)
        embed.add_field(name="Apellidos", value=datos["apellidos"], inline=True)
        embed.add_field(name="Fecha de Nacimiento", value=datos["fecha"], inline=True)
        embed.add_field(name="Sexo", value=datos["sexo"], inline=True)
        embed.add_field(name="Número de DNI", value=datos["dni"], inline=True)
        embed.set_footer(text="Este DNI es ficticio y válido solo dentro del servidor.")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene DNI registrado.")

@tree.command(name="eliminar-dni", description="Eliminar el DNI de un usuario (SOLO STAFF)")
async def eliminar_dni(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("🚫 No tienes permisos para usar este comando.", ephemeral=True)
        return
    if usuario.id in dnis:
        del dnis[usuario.id]
        await interaction.response.send_message(f"🗑️ DNI eliminado para {usuario.mention}")
    else:
        await interaction.response.send_message(f"❌ {usuario.mention} no tenía DNI registrado.")

# --- COMANDOS DE CARNET ---
@tree.command(name="crear-carnet", description="Crear un carnet de conducir usando los datos del DNI")
@app_commands.describe(
    usuario="Usuario al que se le creará el carnet",
    tipo="Tipo de carnet (ej: Tipo A, Tipo B, Tipo C)"
)
async def crear_carnet(interaction: discord.Interaction, usuario: discord.Member, tipo: str):
    if usuario.id not in dnis:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene DNI registrado. Primero usa `/crear-dni`.")
        return

    if usuario.id in carnets:
        await interaction.response.send_message(f"⚠️ {usuario.mention} ya tiene carnet registrado.")
    else:
        # Copiar datos del DNI
        datos_dni = dnis[usuario.id]
        carnets[usuario.id] = {
            "nombre": datos_dni["nombre"],
            "apellidos": datos_dni["apellidos"],
            "fecha": datos_dni["fecha"],
            "sexo": datos_dni["sexo"],
            "tipo": tipo
        }
        await interaction.response.send_message(f"✅ Carnet creado para {usuario.mention}")

@tree.command(name="ver-carnet", description="Ver el carnet de conducir de un usuario")
async def ver_carnet(interaction: discord.Interaction, usuario: discord.Member):
    if usuario.id in carnets:
        datos = carnets[usuario.id]
        embed = discord.Embed(
            title=f"🪪 Carnet de Conducir - {usuario.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Nombre", value=datos["nombre"], inline=True)
        embed.add_field(name="Apellidos", value=datos["apellidos"], inline=True)
        embed.add_field(name="Fecha de Nacimiento", value=datos["fecha"], inline=True)
        embed.add_field(name="Sexo", value=datos["sexo"], inline=True)
        embed.add_field(name="Tipo de Carnet", value=datos["tipo"], inline=True)
        embed.set_footer(text="Carnet ficticio válido solo dentro del servidor.")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene carnet registrado.")

@tree.command(name="eliminar-carnet", description="Eliminar el carnet de conducir de un usuario (SOLO STAFF)")
async def eliminar_carnet(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("🚫 No tienes permisos para usar este comando.", ephemeral=True)
        return
    if usuario.id in carnets:
        del carnets[usuario.id]
        await interaction.response.send_message(f"🗑️ Carnet eliminado para {usuario.mention}")
    else:
        await interaction.response.send_message(f"❌ {usuario.mention} no tenía carnet registrado.")

# --- INICIO DEL BOT ---
bot.run("TU_TOKEN_AQUI")
