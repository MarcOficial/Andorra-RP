# -----------------------
# Parte 1 — CONFIG, JSON & UTILIDADES 
# -----------------------
import discord
from discord import app_commands, Interaction, Embed
from discord.ui import View, Button, Select, Modal, TextInput  # <-- Añadido Modal y TextInput
from discord.ext import commands
import os, json, random, string, asyncio, datetime, time

# =====================
# CONFIGURACIÓN CENTRALIZADA
# =====================
class Config:
    """Configuración centralizada del bot"""
    # Token del bot
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    # Roles importantes
    STAFF_ROLE_ID = 1419296399547174934
    ECONOMIA_ROLE_ID = 1415040769697382561
    ROL_POLICIA_ID = 1404502808547430451
    ROL_VERIFICADO = 1416109554629873704
    
    # Canales importantes
    CANAL_VERIFICACIONES = 1415651594464137246
    CANAL_SOLICITUDES = 1415652632231677982
    CANAL_LOGS = None  # Se configurará dinámicamente
    
    # Configuración de economía
    SALDO_INICIAL_TARJETA = 1200
    SALDO_INICIAL_EFECTIVO = 0
    
    # Colores para embeds
    COLOR_EXITO = discord.Color.green()
    COLOR_ERROR = discord.Color.red()
    COLOR_ADVERTENCIA = discord.Color.orange()
    COLOR_INFO = discord.Color.blue()
    COLOR_ECONOMICO = discord.Color.gold()
    
    # Mensajes del sistema
    FOOTER_BANCARIO = "Sistema Bancario • Valencia RP ESP"
    FOOTER_ADMINISTRATIVO = "Sistema Administrativo • Valencia RP ESP"
    FOOTER_ERRORES = "Sistema de Errores • Valencia RP ESP"
    FOOTER_INVENTARIO = "Sistema de Inventario • Valencia RP ESP"
    FOOTER_TIENDA = "Sistema de Tienda • Valencia RP ESP"
    FOOTER_POLICIAL = "Sistema Policial • Valencia RP ESP"
    
# Instancia global de configuración
config = Config()

# Bot con intents completos
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Data files (asegura la carpeta data)
DATA_DIR = "data"
# Ensure data directory structure exists
SUBDIRS = ["identity", "economy", "enforcement", "gameplay", "governance", "config", "backups"]
for subdir in [DATA_DIR] + [os.path.join(DATA_DIR, s) for s in SUBDIRS]:
    if not os.path.exists(subdir):
        os.makedirs(subdir)

FILES = {
    # Identity Management
    "dnis": os.path.join(DATA_DIR, "identity", "dnis.json"),
    "carnets": os.path.join(DATA_DIR, "identity", "carnets.json"),
    "oposiciones": os.path.join(DATA_DIR, "identity", "oposiciones.json"),
    
    # Economic System
    "cuentas": os.path.join(DATA_DIR, "economy", "cuentas.json"),
    "prestamos": os.path.join(DATA_DIR, "economy", "prestamos.json"),
    "cuentas_eliminadas": os.path.join(DATA_DIR, "economy", "cuentas_eliminadas.json"),
    
    # Law Enforcement
    "multas": os.path.join(DATA_DIR, "enforcement", "multas.json"),
    "sanciones": os.path.join(DATA_DIR, "enforcement", "sanciones.json"),
    "incautaciones": os.path.join(DATA_DIR, "enforcement", "incautaciones.json"),
    
    # Gameplay & Items
    "inventario": os.path.join(DATA_DIR, "gameplay", "inventario.json"),
    "vehiculos": os.path.join(DATA_DIR, "gameplay", "vehiculos.json"),
    "tienda": os.path.join(DATA_DIR, "gameplay", "tienda.json"),
    
    # Governance
    "votaciones": os.path.join(DATA_DIR, "governance", "votaciones.json"),
    
    # Configuration
    "config": os.path.join(DATA_DIR, "config", "config.json"),
    "alertas": os.path.join(DATA_DIR, "config", "alertas.json")
}

data = {}
for k, path in FILES.items():
    try:
        with open(path, "r", encoding="utf-8") as f:
            data[k] = json.load(f)
    except Exception:
        data[k] = {}
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)

# Helpers
def save_json(key):
    if key not in FILES:
        return
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(data.get(key, {}), f, indent=4, ensure_ascii=False)

def generar_dni():
    return str(random.randint(10000000, 99999999)) + random.choice(string.ascii_uppercase)

def generar_codigo_multa():
    return "M" + "".join(random.choices(string.digits, k=10))

# =====================
# UTILIDADES MEJORADAS
# =====================
def es_staff(user_or_member) -> bool:
    """Verifica si el usuario tiene permisos de staff"""
    if not user_or_member:
        return False
    
    # Si es un User, no puede tener roles
    if isinstance(user_or_member, discord.User):
        return False
    
    # Si es un Member, verificar roles
    if isinstance(user_or_member, discord.Member):
        try:
            return any(r.id == config.STAFF_ROLE_ID for r in user_or_member.roles)
        except (AttributeError, TypeError):
            return False
    
    return False

def es_economia(user_or_member) -> bool:
    """Verifica si el usuario tiene permisos de economía"""
    if not user_or_member:
        return False
    
    # Si es un User, no puede tener roles
    if isinstance(user_or_member, discord.User):
        return False
    
    # Si es un Member, verificar roles
    if isinstance(user_or_member, discord.Member):
        try:
            return any(r.id == config.ECONOMIA_ROLE_ID for r in user_or_member.roles)
        except (AttributeError, TypeError):
            return False
    
    return False

def es_policia(user_or_member) -> bool:
    """Verifica si el usuario es policía"""
    if not user_or_member:
        return False
    
    if isinstance(user_or_member, discord.User):
        return False
    
    if isinstance(user_or_member, discord.Member):
        try:
            return any(r.id == config.ROL_POLICIA_ID for r in user_or_member.roles)
        except (AttributeError, TypeError):
            return False
    
    return False

def obtener_member_seguro(interaction: discord.Interaction, usuario: discord.User = None) -> discord.Member:
    """Obtiene un Member de forma segura desde un User o Interaction"""
    if usuario is None:
        usuario = interaction.user
    
    # Si ya es Member, devolverlo
    if isinstance(usuario, discord.Member):
        return usuario
    
    # Si es User, intentar obtener Member desde el guild
    if isinstance(usuario, discord.User) and interaction.guild:
        member = interaction.guild.get_member(usuario.id)
        if member:
            return member
    
    return None

def crear_embed_error(titulo: str, descripcion: str, footer: str = None) -> discord.Embed:
    """Crea un embed de error estandarizado"""
    embed = discord.Embed(
        title=f"❌ {titulo}",
        description=descripcion,
        color=config.COLOR_ERROR
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def crear_embed_exito(titulo: str, descripcion: str, footer: str = None) -> discord.Embed:
    """Crea un embed de éxito estandarizado"""
    embed = discord.Embed(
        title=f"✅ {titulo}",
        description=descripcion,
        color=config.COLOR_EXITO
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def crear_embed_info(titulo: str, descripcion: str, footer: str = None) -> discord.Embed:
    """Crea un embed informativo estandarizado"""
    embed = discord.Embed(
        title=f"ℹ️ {titulo}",
        description=descripcion,
        color=config.COLOR_INFO
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

# =====================
# MANEJO DE ERRORES MEJORADO
# =====================
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Maneja errores de comandos de aplicación de forma global y profesional."""
    import logging
    import traceback
    
    # Configurar logging si no está configurado
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Log del error para depuración
    comando = interaction.command.name if interaction.command else "Desconocido"
    logging.error(f"Error en comando '{comando}': {error}")
    
    # Determinar el mensaje de error apropiado
    if isinstance(error, app_commands.CommandInvokeError):
        original_error = error.original
        
        if isinstance(original_error, discord.NotFound):
            if "Unknown interaction" in str(original_error):
                # Interacción ya respondida o expirada
                logging.warning(f"Interacción expirada/duplicada en comando '{comando}'")
                return
            else:
                error_msg = "🔍 **Recurso no encontrado**\nEl elemento solicitado no existe o ha sido eliminado."
        
        elif isinstance(original_error, discord.Forbidden):
            error_msg = "🚫 **Sin permisos**\nNo tengo los permisos necesarios para ejecutar esta acción."
        
        elif isinstance(original_error, discord.HTTPException):
            error_msg = "🌐 **Error de conexión**\nProblemas de comunicación con Discord. Inténtalo nuevamente."
        
        elif isinstance(original_error, (ValueError, TypeError)):
            error_msg = "📝 **Datos inválidos**\nLos datos proporcionados no son válidos. Verifica tu entrada."
        
        else:
            # Error genérico con más detalles para staff
            error_msg = "⚙️ **Error interno del sistema**\nSe ha producido un error inesperado."
            logging.error(f"Error no manejado en '{comando}': {traceback.format_exc()}")
    
    elif isinstance(error, app_commands.CommandOnCooldown):
        tiempo = f"{error.retry_after:.1f}"
        error_msg = f"⏰ **Comando en cooldown**\nEspera {tiempo} segundos antes de usar este comando nuevamente."
    
    elif isinstance(error, app_commands.MissingPermissions):
        permisos = ", ".join([p.replace('_', ' ').title() for p in error.missing_permissions])
        error_msg = f"🔐 **Permisos insuficientes**\nNecesitas los siguientes permisos: {permisos}"
    
    elif isinstance(error, app_commands.BotMissingPermissions):
        permisos = ", ".join([p.replace('_', ' ').title() for p in error.missing_permissions])
        error_msg = f"🤖 **Bot sin permisos**\nEl bot necesita los siguientes permisos: {permisos}"
    
    elif isinstance(error, app_commands.CommandNotFound):
        error_msg = "❓ **Comando no encontrado**\nEste comando no existe o ha sido deshabilitado."
    
    else:
        error_msg = "❗ **Error desconocido**\nSe ha producido un error inesperado. Contacta al staff si persiste."
        logging.error(f"Error no categorizado en '{comando}': {error}")
    
    # Intentar enviar la respuesta de error
    try:
        embed = crear_embed_error(
            "Error en el comando",
            error_msg,
            config.FOOTER_ERRORES
        )
        
        # Agregar información adicional para staff
        if interaction.user and es_staff(interaction.user):
            embed.add_field(
                name="🔧 Info para Staff",
                value=f"**Comando:** `{comando}`\n**Error:** `{type(error).__name__}`",
                inline=False
            )
        
        # Enviar respuesta
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        # Último recurso: mensaje simple
        logging.error(f"No se pudo enviar embed de error: {e}")
        try:
            mensaje_simple = f"❌ Error en el comando. Contacta al staff si persiste."
            if not interaction.response.is_done():
                await interaction.response.send_message(mensaje_simple, ephemeral=True)
            else:
                await interaction.followup.send(mensaje_simple, ephemeral=True)
        except:
            logging.error("No se pudo enviar ningún tipo de respuesta de error")

from keep_alive import keep_alive  # 👈 añade esto arriba de tu código

keep_alive()  # 👈 ponlo antes de bot.run()


# On ready
@bot.event
async def on_ready():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Valencia RP ESP V2 | /ayuda para comandos"
        )
    )
    await tree.sync()
    print(f"✅ Bot listo como {bot.user} ({len(bot.guilds)} guilds)")
    print(f"✅ Comandos sincronizados: {len(tree.get_commands())}")
    bot.loop.create_task(pagos_prestamos_diarios())

# ----------------------
# Economía, cuentas, transferencias y préstamos
# ----------------------
# Crear cuenta (si no existe)
# ----------------------
# --- COMANDO: CUENTA CREAR ---
# ----------------------
# =====================
# CONFIGURACIÓN DE BANCOS
# =====================
BANCOS_VALENCIA = {
    "Banco Sabadell": {
        "nombre": "Banco Sabadell",
        "logo": "https://www.bancsabadell.com/cs/Satellite?blobcol=urldata&blobheader=image%2Fpng&blobkey=id&blobtable=MungoBlobs&blobwhere=1317473918946&ssbinary=true",
        "descripcion": "Banco líder en Valencia con más de 130 años de experiencia"
    },
    "CaixaBank": {
        "nombre": "CaixaBank",
        "logo": "https://www.caixabank.com/deployedfiles/caixabank_com/Estaticos/Imagenes/infocaixabank/logocaixabank.png",
        "descripcion": "El banco más grande de España, presente en Valencia"
    },
    "Banco Santander": {
        "nombre": "Banco Santander",
        "logo": "https://www.santander.com/content/dam/santander-com/logos/banco-santander-logo.png",
        "descripcion": "Banco internacional con fuerte presencia en la Comunidad Valenciana"
    },
    "BBVA": {
        "nombre": "BBVA",
        "logo": "https://www.bbva.com/wp-content/uploads/2021/01/BBVA-logo-2019.png",
        "descripcion": "Banco digital líder en innovación financiera"
    },
    "Bankinter": {
        "nombre": "Bankinter",
        "logo": "https://www.bankinter.com/www2/logo_bankinter_web.png",
        "descripcion": "Banco especializado en banca personal y de empresas"
    }
}

bancos_disponibles = list(BANCOS_VALENCIA.keys())

# Logo por defecto para bancos
LOGO_BANCO_DEFAULT = "https://cdn.discordapp.com/emojis/881912302932930600.png"

@tree.command(name="cuenta-crear", description="🏦 Crear una nueva cuenta bancaria")
@app_commands.describe(
    usuario="Usuario para quien crear la cuenta bancaria",
    banco="Banco donde abrir la cuenta"
)
@app_commands.choices(banco=[app_commands.Choice(name=f"{b} - {BANCOS_VALENCIA[b]['descripcion'][:50]}...", value=b) for b in bancos_disponibles])
async def cuenta_crear(interaction: Interaction, usuario: discord.Member, banco: app_commands.Choice[str]):
    """Crea una nueva cuenta bancaria para un usuario"""
    
    # Verificar permisos (solo staff puede crear cuentas)
    if not es_staff(interaction.user):
        embed = crear_embed_error(
            "Sin permisos",
            "Solo el personal autorizado puede crear cuentas bancarias.",
            config.FOOTER_ADMINISTRATIVO
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Validar usuario
    if not usuario:
        embed = crear_embed_error(
            "Usuario inválido",
            "No se pudo encontrar el usuario especificado.",
            config.FOOTER_BANCARIO
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    uid = str(usuario.id)
    
    # Verificar si ya existe cuenta
    if uid in data["cuentas"]:
        cuenta_existente = data["cuentas"][uid]
        embed = discord.Embed(
            title="⚠️ Cuenta ya existente",
            description=f"**{usuario.display_name}** ya posee una cuenta bancaria activa.",
            color=config.COLOR_ADVERTENCIA
        )
        embed.add_field(
            name="🏦 Banco actual",
            value=cuenta_existente.get("banco", "No especificado"),
            inline=True
        )
        embed.add_field(
            name="💳 Saldo en tarjeta",
            value=f"{cuenta_existente.get('tarjeta', 0):,}€",
            inline=True
        )
        embed.add_field(
            name="💵 Efectivo",
            value=f"{cuenta_existente.get('efectivo', 0):,}€",
            inline=True
        )
        embed.add_field(
            name="💡 Sugerencia",
            value="Usa `/cuenta-ver` para consultar los detalles completos de la cuenta",
            inline=False
        )
        embed.set_footer(text=config.FOOTER_BANCARIO)
        embed.set_thumbnail(url=usuario.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Obtener información del banco seleccionado
    banco_info = BANCOS_VALENCIA.get(banco.value, {})
    
    # Crear cuenta nueva
    nueva_cuenta = {
        "banco": banco.value,
        "tarjeta": config.SALDO_INICIAL_TARJETA,
        "efectivo": config.SALDO_INICIAL_EFECTIVO,
        "fecha_creacion": datetime.datetime.now().isoformat(),
        "creado_por": str(interaction.user.id)
    }
    
    data["cuentas"][uid] = nueva_cuenta
    save_json("cuentas")

    # Respuesta con embed mejorado
    embed = discord.Embed(
        title="🏦 ¡Cuenta bancaria creada exitosamente!",
        description=f"Se ha abierto una nueva cuenta bancaria para **{usuario.display_name}**.",
        color=config.COLOR_EXITO
    )
    
    # Información del banco
    embed.add_field(
        name="🏦 Banco seleccionado",
        value=f"**{banco.value}**\n{banco_info.get('descripcion', 'Banco de confianza en Valencia')}",
        inline=False
    )
    
    # Saldos iniciales
    embed.add_field(
        name="💳 Saldo inicial en tarjeta",
        value=f"**{config.SALDO_INICIAL_TARJETA:,}€**",
        inline=True
    )
    embed.add_field(
        name="💵 Efectivo inicial",
        value=f"**{config.SALDO_INICIAL_EFECTIVO:,}€**",
        inline=True
    )
    embed.add_field(
        name="📊 Total",
        value=f"**{config.SALDO_INICIAL_TARJETA + config.SALDO_INICIAL_EFECTIVO:,}€**",
        inline=True
    )
    
    # Información adicional
    embed.add_field(
        name="🔄 Próximos pasos",
        value="• Usa `/cuenta-ver` para consultar tu cuenta\n• Usa `/dinero-dar` para transferir dinero\n• Usa `/retirar-efectivo` para sacar dinero del banco",
        inline=False
    )
    
    embed.set_footer(text=f"{config.FOOTER_BANCARIO} • Creada por {interaction.user.display_name}")
    embed.set_thumbnail(url=banco_info.get('logo', LOGO_BANCO_DEFAULT))
    embed.set_author(name=usuario.display_name, icon_url=usuario.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    await interaction.response.send_message(embed=embed)

@tree.command(name="cuenta-ver", description="Ver la cuenta bancaria de un usuario")
@app_commands.describe(usuario="Usuario a consultar (opcional)")
async def cuenta_ver(interaction: Interaction, usuario: discord.Member = None):
    target = usuario or interaction.user
    uid = str(target.id)
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Cuenta No Encontrada",
            description=f"{target.mention} no tiene una cuenta bancaria registrada.",
            color=discord.Color.red()
        )
        embed.add_field(name="💼 Usuario", value=target.mention, inline=True)
        embed.add_field(name="💡 Solución", value="El usuario debe usar `/cuenta-crear` primero", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    c = data["cuentas"][uid]
    banco = c.get("banco", "-")
    
    embed = Embed(title=f"🏦 Cuenta - {target.display_name}", color=discord.Color.gold())
    embed.add_field(name="Banco", value=banco)
    embed.add_field(name="Saldo en tarjeta", value=f"{c.get('tarjeta',0)}€")
    embed.add_field(name="Efectivo", value=f"{c.get('efectivo',0)}€")
    
    # Agregar logo del banco como thumbnail
    banco_info = BANCOS_VALENCIA.get(banco, {})
    logo_url = banco_info.get('logo', LOGO_BANCO_DEFAULT)
    embed.set_thumbnail(url=logo_url)
    
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="top", description="Ver ranking de los usuarios más ricos de Valencia RP")
async def top_ricos(interaction: Interaction):
    if not data.get("cuentas"):
        embed = discord.Embed(
            title="📊 Ranking Económico",
            description="No hay cuentas bancarias registradas en el sistema.",
            color=discord.Color.light_grey()
        )
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Calcular patrimonio total de cada usuario
    rankings = []
    for uid, cuenta in data["cuentas"].items():
        try:
            user = interaction.guild.get_member(int(uid))
            if user:  # Solo incluir usuarios que están en el servidor
                tarjeta = cuenta.get("tarjeta", 0)
                efectivo = cuenta.get("efectivo", 0)
                total = tarjeta + efectivo
                banco = cuenta.get("banco", "N/A")
                
                rankings.append({
                    "user": user,
                    "tarjeta": tarjeta,
                    "efectivo": efectivo,
                    "total": total,
                    "banco": banco
                })
        except:
            continue  # Ignorar usuarios que no se pueden obtener
    
    # Ordenar por patrimonio total (de mayor a menor)
    rankings.sort(key=lambda x: x["total"], reverse=True)
    
    if not rankings:
        embed = discord.Embed(
            title="📊 Ranking Económico",
            description="No hay usuarios válidos con cuentas bancarias.",
            color=discord.Color.light_grey()
        )
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Crear embed con el ranking
    embed = discord.Embed(
        title="💰 Top Usuarios Más Ricos de Valencia RP",
        description="Ranking basado en patrimonio total (tarjeta + efectivo)",
        color=discord.Color.gold()
    )
    
    # Mostrar top 10
    top_count = min(10, len(rankings))
    
    for i in range(top_count):
        user_data = rankings[i]
        user = user_data["user"]
        posicion = i + 1
        
        # Iconos especiales para los primeros 3 puestos
        if posicion == 1:
            icono = "🥇"
        elif posicion == 2:
            icono = "🥈"
        elif posicion == 3:
            icono = "🥉"
        else:
            icono = f"{posicion}."
        
        # Formatear información del usuario
        info_text = f"""**Patrimonio:** {user_data['total']:,}€
**Tarjeta:** {user_data['tarjeta']:,}€ | **Efectivo:** {user_data['efectivo']:,}€
**Banco:** {user_data['banco']}"""
        
        embed.add_field(
            name=f"{icono} {user.display_name}",
            value=info_text,
            inline=False
        )
    
    # Información adicional
    total_usuarios = len(rankings)
    total_dinero = sum(r["total"] for r in rankings)
    promedio = total_dinero // total_usuarios if total_usuarios > 0 else 0
    
    embed.add_field(
        name="📈 Estadísticas Generales", 
        value=f"**Total usuarios:** {total_usuarios}\n**Dinero total:** {total_dinero:,}€\n**Promedio:** {promedio:,}€", 
        inline=False
    )
    
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="cuenta-eliminar", description="Eliminar cuenta bancaria de un usuario - SOLO STAFF")
@app_commands.describe(usuario="Usuario cuya cuenta se eliminará")
async def cuenta_eliminar(interaction: Interaction, usuario: discord.Member):
    # VERIFICACIÓN CRÍTICA: Solo staff puede eliminar cuentas
    if not es_staff(interaction.user):
        embed = discord.Embed(
            title="🚫 Acceso Denegado",
            description="Solo el personal autorizado puede eliminar cuentas bancarias.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚖️ Requerido", value="Permisos de Staff/Admin", inline=True)
        embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    uid = str(usuario.id)
    
    # Verificar que el usuario tenga cuenta
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Cuenta No Encontrada",
            description=f"{usuario.mention} no tiene cuenta bancaria registrada.",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="📋 Estado", value="Sin cuenta bancaria", inline=True)
        embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Obtener datos actuales antes de eliminar
    cuenta_actual = data["cuentas"][uid].copy()
    saldo_tarjeta = cuenta_actual.get("tarjeta", 0)
    saldo_efectivo = cuenta_actual.get("efectivo", 0)
    banco = cuenta_actual.get("banco", "Unknown")
    
    # BACKUP PERSISTENTE: Guardar registro de eliminación
    if "cuentas_eliminadas" not in data:
        data["cuentas_eliminadas"] = []
    
    backup_record = {
        "usuario_id": uid,
        "usuario_name": usuario.display_name,
        "usuario_mention": usuario.mention,
        "banco": banco,
        "saldo_tarjeta": saldo_tarjeta,
        "saldo_efectivo": saldo_efectivo,
        "total_perdido": saldo_tarjeta + saldo_efectivo,
        "staff_id": str(interaction.user.id),
        "staff_name": interaction.user.display_name,
        "staff_mention": interaction.user.mention,
        "fecha_eliminacion": datetime.date.today().isoformat(),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    data["cuentas_eliminadas"].append(backup_record)
    save_json("cuentas_eliminadas")
    
    # Eliminar la cuenta
    del data["cuentas"][uid]
    save_json("cuentas")
    
    # Respuesta con embed profesional
    embed = discord.Embed(
        title="🗑️ Cuenta Bancaria Eliminada",
        description=f"La cuenta bancaria de {usuario.mention} ha sido eliminada del sistema.",
        color=discord.Color.orange()
    )
    embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
    embed.add_field(name="🏦 Banco", value=banco, inline=True)
    embed.add_field(name="🚔 Staff", value=interaction.user.mention, inline=True)
    embed.add_field(name="💳 Saldo en Tarjeta", value=f"{saldo_tarjeta}€ (perdido)", inline=True)
    embed.add_field(name="💵 Efectivo", value=f"{saldo_efectivo}€ (perdido)", inline=True)
    embed.add_field(name="📅 Fecha", value=datetime.date.today().strftime("%d/%m/%Y"), inline=True)
    
    total_perdido = saldo_tarjeta + saldo_efectivo
    if total_perdido > 0:
        embed.add_field(
            name="⚠️ Dinero Perdido", 
            value=f"**{total_perdido}€** eliminados del sistema", 
            inline=False
        )
    
    embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
    embed.set_author(name=f"Eliminación de Cuenta", icon_url=interaction.user.display_avatar.url)
    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="dinero-dar", description="Dar dinero desde tu tarjeta a otro usuario")
@app_commands.describe(usuario="Usuario receptor", cantidad="Cantidad a transferir", tipo="Tipo de transferencia")
@app_commands.choices(tipo=[
    app_commands.Choice(name="En efectivo", value="efectivo"),
    app_commands.Choice(name="Bancario", value="bancario")
])
async def dinero_dar(interaction: Interaction, usuario: discord.Member, cantidad: int, tipo: app_commands.Choice[str]):
    if cantidad <= 0:
        embed = discord.Embed(
            title="❌ Cantidad Inválida",
            description="La cantidad debe ser mayor que 0.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    pid = str(interaction.user.id); tid = str(usuario.id)
    if pid not in data["cuentas"] or data["cuentas"][pid]["tarjeta"] < cantidad:
        embed = discord.Embed(
            title="❌ Saldo Insuficiente",
            description="No tienes suficiente saldo en tu tarjeta para realizar esta transferencia.",
            color=discord.Color.red())
        saldo_actual = data["cuentas"].get(pid, {}).get("tarjeta", 0)
        embed.add_field(name="💳 Tu Saldo", value=f"{saldo_actual}€", inline=True)
        embed.add_field(name="💰 Requerido", value=f"{cantidad}€", inline=True)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    # Verificar que el usuario destinatario tenga cuenta
    if tid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Usuario Sin Cuenta",
            description=f"{usuario.mention} no tiene una cuenta bancaria registrada.",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="💡 Solución", value="El usuario debe usar `/cuenta-crear` primero", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Procesar según el tipo de transferencia
    tipo_valor = tipo.value
    if tipo_valor == "efectivo":
        data["cuentas"][pid]["tarjeta"] -= cantidad
        data["cuentas"][tid]["efectivo"] += cantidad
        tipo_desc = "💵 En Efectivo"
        destino_desc = f"Efectivo de {usuario.mention}"
    else:  # bancario
        data["cuentas"][pid]["tarjeta"] -= cantidad
        data["cuentas"][tid]["tarjeta"] += cantidad
        tipo_desc = "🏦 Bancario"
        destino_desc = f"Cuenta de {usuario.mention}"
    
    save_json("cuentas")
    
    # Respuesta con embed
    embed = discord.Embed(
        title="💸 Transferencia Completada",
        description=f"Has transferido **{cantidad}€** a {usuario.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="💰 Cantidad", value=f"{cantidad}€", inline=True)
    embed.add_field(name="📤 Destinatario", value=usuario.mention, inline=True)
    embed.add_field(name="🔄 Tipo", value=tipo_desc, inline=True)
    embed.add_field(name="📥 Destino", value=destino_desc, inline=True)
    embed.add_field(name="💳 Tu saldo restante", value=f"{data['cuentas'][pid]['tarjeta']}€", inline=True)
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="dinero-agregar", description="Añadir dinero a un usuario (compensaciones, robos) - SOLO STAFF")
@app_commands.describe(usuario="Usuario receptor", cantidad="Cantidad a agregar", tipo="Destino del dinero", motivo="Motivo de la compensación")
@app_commands.choices(tipo=[
    app_commands.Choice(name="A efectivo", value="efectivo"),
    app_commands.Choice(name="A cuenta bancaria", value="tarjeta")
])
async def dinero_agregar(interaction: Interaction, usuario: discord.Member, cantidad: int, tipo: app_commands.Choice[str], motivo: str):
    # VERIFICACIÓN CRÍTICA: Solo staff puede generar dinero
    if not es_staff(interaction.user):
        embed = discord.Embed(
            title="🚫 Acceso Denegado",
            description="Solo el personal autorizado puede generar dinero administrativo.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚖️ Requerido", value="Permisos de Staff/Admin", inline=True)
        embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if cantidad <= 0:
        embed = discord.Embed(
            title="❌ Cantidad Inválida",
            description="La cantidad debe ser mayor que 0.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    uid = str(usuario.id)
    
    # Verificar que el usuario tenga cuenta
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Usuario Sin Cuenta",
            description=f"{usuario.mention} no tiene cuenta bancaria registrada.",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="💡 Solución", value="El usuario debe usar `/cuenta-crear` primero", inline=False)
        embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Agregar dinero según el tipo especificado
    tipo_valor = tipo.value
    if tipo_valor == "efectivo":
        data["cuentas"][uid]["efectivo"] += cantidad
        destino_desc = "💵 Efectivo"
        saldo_final = data["cuentas"][uid]["efectivo"]
    else:  # tarjeta
        data["cuentas"][uid]["tarjeta"] += cantidad
        destino_desc = "🏦 Cuenta Bancaria"
        saldo_final = data["cuentas"][uid]["tarjeta"]
    
    save_json("cuentas")
    
    # Respuesta con embed profesional
    embed = discord.Embed(
        title="💰 Dinero Administrativo Agregado",
        description=f"Se han agregado **{cantidad}€** a {usuario.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="👤 Beneficiario", value=usuario.mention, inline=True)
    embed.add_field(name="💰 Cantidad", value=f"{cantidad}€", inline=True)
    embed.add_field(name="📥 Destino", value=destino_desc, inline=True)
    embed.add_field(name="📋 Motivo", value=motivo, inline=False)
    embed.add_field(name="💳 Saldo Final", value=f"{saldo_final}€", inline=True)
    embed.add_field(name="🚔 Staff", value=interaction.user.mention, inline=True)
    
    embed.set_footer(text="Sistema Administrativo • Valencia RP ESP")
    embed.set_author(name=f"Compensación para {usuario.display_name}", icon_url=usuario.display_avatar.url)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="retirar-efectivo", description="Retirar dinero de tu tarjeta a efectivo")
@app_commands.describe(cantidad="Cantidad a retirar de la tarjeta")
async def retirar_efectivo(interaction: Interaction, cantidad: int):
    if cantidad <= 0:
        embed = discord.Embed(
            title="❌ Cantidad Inválida",
            description="La cantidad debe ser mayor que 0.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    uid = str(interaction.user.id)
    
    # Verificar que tenga cuenta
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Cuenta No Encontrada",
            description="No tienes cuenta bancaria. Necesitas crear una primero.",
            color=discord.Color.red()
        )
        embed.add_field(name="💡 Solución", value="Usa `/cuenta-crear` para crear tu cuenta", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Verificar saldo suficiente en tarjeta
    if data["cuentas"][uid]["tarjeta"] < cantidad:
        saldo_actual = data["cuentas"][uid]["tarjeta"]
        embed = discord.Embed(
            title="❌ Saldo Insuficiente",
            description="No tienes suficiente dinero en tu tarjeta para retirar esa cantidad.",
            color=discord.Color.red()
        )
        embed.add_field(name="💳 Tu Saldo", value=f"{saldo_actual}€", inline=True)
        embed.add_field(name="📤 Solicitado", value=f"{cantidad}€", inline=True)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Realizar la transferencia interna
    data["cuentas"][uid]["tarjeta"] -= cantidad
    data["cuentas"][uid]["efectivo"] += cantidad
    save_json("cuentas")
    
    # Respuesta con embed
    cuenta = data["cuentas"][uid]
    embed = discord.Embed(
        title="💸 Retiro de Efectivo",
        description=f"Has retirado **{cantidad}€** de tu tarjeta a efectivo.",
        color=discord.Color.green()
    )
    embed.add_field(name="💳 Saldo en Tarjeta", value=f"{cuenta['tarjeta']}€", inline=True)
    embed.add_field(name="💵 Efectivo", value=f"{cuenta['efectivo']}€", inline=True)
    embed.add_field(name="🏦 Banco", value=cuenta.get("banco", "N/A"), inline=True)
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ----------------------
    # --- COMANDO: SUELDO ---
    # ----------------------
@tree.command(name="sueldo", description="Cobrar el sueldo según el rol más alto")
async def cobrar_sueldo(interaction: Interaction):
    uid = str(interaction.user.id)

    # Verificar que el usuario tenga cuenta
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Cuenta No Encontrada",
            description="No tienes cuenta bancaria. Necesitas crear una primero.",
            color=discord.Color.red()
        )
        embed.add_field(name="💡 Solución", value="Usa `/cuenta-crear` para crear tu cuenta", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Diccionario de sueldos por ID de rol
    sueldos_roles = {
        1401538045567565875: 1900,
        1401538045567565876: 1800,
        1401538045567565877: 1770,
        1401538045567565881: 1500,
        1401538045567565882: 1400,
        1401538045567565883: 1267,
        1401538045584605204: 1800,
        1401538045584605205: 1700,
        1401538045584605206: 1500,
        1401538045634674790: 600
    }

    # Detectar el rol del usuario con mayor sueldo
    roles_usuario = [role.id for role in interaction.user.roles]
    sueldo_bruto = 0
    rol_trabajo = "Ciudadano"

    for rol_id, sueldo in sueldos_roles.items():
        if rol_id in roles_usuario and sueldo > sueldo_bruto:
            sueldo_bruto = sueldo
            rol_trabajo = f"<@&{rol_id}>"

        if sueldo_bruto == 0:
            sueldo_bruto = 1200  # Sueldo por defecto si no tiene rol de trabajo

    # Calcular impuestos (7% de ejemplo)
    impuestos = int(sueldo_bruto * 0.065)
    sueldo_neto = sueldo_bruto - impuestos

    # Agregar dinero a la cuenta del usuario
    data["cuentas"][uid]["tarjeta"] += sueldo_neto
    save_json("cuentas")

    # Mensaje inicial
    await interaction.response.send_message(
        "💼 | Cheque recibido exitosamente, canjeando en el banco; descontando impuestos"
    )

    # Embed con desglose
    embed = discord.Embed(
        title="💰 Sueldo Cobrado",
        description=f"Sueldo recibido exitosamente y depositado en tu cuenta bancaria.",
        color=discord.Color.green()
    )
    embed.add_field(name="💵 Sueldo bruto", value=f"{sueldo_bruto}€", inline=True)
    embed.add_field(name="🏢 Trabajo(s)", value=rol_trabajo, inline=True)
    embed.add_field(name="💳 Cheque recibido", value=f"{sueldo_bruto}€", inline=True)
    embed.add_field(name="💸 Impuestos descontados", value=f"{impuestos}€", inline=True)
    embed.add_field(name="💰 Sueldo neto", value=f"{sueldo_neto}€", inline=True)
    embed.add_field(name="⏳ Estado", value="Ingresando a la cuenta...", inline=False)
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

    await interaction.followup.send(embed=embed)


# Comando Opos Pasadas
    @tree.command(name="opos-pasadas", description="Registrar oposición pasada - Sistema de formación")
    @app_commands.describe(usuario="Usuario que superó la oposición", instructor="Instructor que impartió la formación", corporacion="Corporación que realiza la formación")
    @app_commands.choices(corporacion=[
        app_commands.Choice(name="Policía Local de Valencia", value="policia_local"),
        app_commands.Choice(name="SUM (Servei Urgent Mèdic)", value="sum"),
        app_commands.Choice(name="Bomberos de Valencia", value="bombers"),
        app_commands.Choice(name="Emergencias Valencia", value="assistencia")
    ])
    async def opos_pasadas(interaction: Interaction, usuario: discord.Member, instructor: discord.Member, corporacion: app_commands.Choice[str]):
        # Asegurar que existe el sistema de oposiciones
        if "oposiciones" not in data:
            data["oposiciones"] = {}

        uid = str(usuario.id)
        if uid not in data["oposiciones"]:
            data["oposiciones"][uid] = []

        corp_nombre = {
            "policia_local": "Policía Local de Valencia",
            "sum": "SUM (Servei Urgent Mèdic)",
            "bombers": "Bomberos de Valencia",
            "assistencia": "Emergencias Valencia"
        }

        # Generar código único de formación
        codigo_formacion = f"FORM{random.randint(100000, 999999)}"

        # Registrar la oposición
        nueva_oposicion = {
            "codigo": codigo_formacion,
            "corporacion": corporacion.value,
            "corporacion_nombre": corp_nombre[corporacion.value],
            "instructor": instructor.mention,
            "instructor_name": instructor.display_name,
            "fecha": datetime.date.today().isoformat(),
            "estado": "Aprobada"
        }

        data["oposiciones"][uid].append(nueva_oposicion)
        save_json("oposiciones")

        embed = discord.Embed(
            title="OPOSICIONES {corp_nombre[corporacion.value]}",
            description=f"Valencia RP | ER:LC OPOSICIONES {corp_nombre[corporacion.value]}\n¡Felicidades {usuario.mention}! Has pasado las oposiciones de {corp_nombre[corporacion.value]} junto al instructor {instructor.mention}.",
            color=discord.Color.green()
        )
        embed.set_author(name="Valencia RP ESP | ER:LC")
        embed.set_footer(text=f"BOT Valencia RP APP — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        await interaction.response.send_message(embed=embed)


# ----------------------
# Préstamos (pedir / pagar / ver) con pagos automáticos diarios
# ----------------------
@tree.command(name="pedir-prestamo", description="Solicitar préstamo. Especifica cantidad y meses de devolución")
@app_commands.describe(cantidad="Cantidad solicitada", meses="Plazo en meses (ej: 3)")
async def pedir_prestamo(interaction: Interaction, cantidad: int, meses: int):
    uid = str(interaction.user.id)
    if uid not in data["cuentas"]:
        embed = discord.Embed(
            title="❌ Cuenta Requerida",
            description="Necesitas tener una cuenta bancaria para solicitar préstamos.",
            color=discord.Color.red()
        )
        embed.add_field(name="💡 Solución", value="Usa `/cuenta-crear` para crear tu cuenta primero", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    if cantidad <= 0 or meses <= 0:
        embed = discord.Embed(
            title="❌ Valores Inválidos",
            description="La cantidad y los meses deben ser mayores que 0.",
            color=discord.Color.red()
        )
        embed.add_field(name="💰 Cantidad Mínima", value="1€", inline=True)
        embed.add_field(name="🗺️ Meses Mínimos", value="1 mes", inline=True)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    # si existe préstamo activo con restante > 0
    if uid in data["prestamos"] and data["prestamos"][uid].get("restante",0) > 0:
        embed = discord.Embed(
            title="⚠️ Préstamo Activo",
            description="Ya tienes un préstamo activo. Debes pagarlo completamente antes de solicitar otro.",
            color=discord.Color.orange()
        )
        restante = data["prestamos"][uid].get("restante", 0)
        embed.add_field(name="💰 Monto Restante", value=f"{restante}€", inline=True)
        embed.add_field(name="💡 Acción", value="Usa `/pagar-prestamo` para pagar", inline=True)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    fecha = datetime.date.today().isoformat()
    total_dias = meses * 30
    cuota_diaria = max(1, cantidad // total_dias)
    data["prestamos"][uid] = {
        "cantidad": cantidad,
        "restante": cantidad,
        "fecha": fecha,
        "meses": meses,
        "dias_totales": total_dias,
        "cuota_diaria": cuota_diaria,
        "ultimo_descuento": None
    }
    data["cuentas"][uid]["tarjeta"] += cantidad
    save_json("prestamos"); save_json("cuentas")
    
    # Respuesta con embed
    embed = discord.Embed(
        title="💰 Préstamo Concedido",
        description=f"Se te ha concedido un préstamo de **{cantidad}€**",
        color=discord.Color.gold()
    )
    embed.add_field(name="💰 Cantidad", value=f"{cantidad}€", inline=True)
    embed.add_field(name="📅 Plazo", value=f"{meses} meses", inline=True)
    embed.add_field(name="📊 Cuota diaria aprox.", value=f"{cuota_diaria}€", inline=True)
    embed.add_field(name="💳 Saldo actual", value=f"{data['cuentas'][uid]['tarjeta']}€", inline=False)
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="pagar-prestamo", description="Pagar cantidad al préstamo")
@app_commands.describe(cantidad="Cantidad a pagar")
async def pagar_prestamo(interaction: Interaction, cantidad: int):
    uid = str(interaction.user.id)
    if uid not in data["prestamos"] or data["prestamos"][uid]["restante"] <= 0:
        embed = discord.Embed(
            title="❌ Sin Préstamo Pendiente",
            description="No tienes ningún préstamo activo para pagar.",
            color=discord.Color.red()
        )
        embed.add_field(name="💡 Alternativa", value="Puedes solicitar un préstamo con `/pedir-prestamo`", inline=False)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    if uid not in data["cuentas"] or data["cuentas"][uid]["tarjeta"] < cantidad:
        embed = discord.Embed(
            title="❌ Saldo Insuficiente",
            description="No tienes suficiente saldo en tu tarjeta para pagar el préstamo.",
            color=discord.Color.red()
        )
        saldo_actual = data["cuentas"].get(uid, {}).get("tarjeta", 0)
        embed.add_field(name="💳 Tu Saldo", value=f"{saldo_actual}€", inline=True)
        embed.add_field(name="💰 Necesario", value=f"{cantidad}€", inline=True)
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    
    # Realizar el pago
    data["cuentas"][uid]["tarjeta"] -= cantidad
    data["prestamos"][uid]["restante"] -= cantidad
    if data["prestamos"][uid]["restante"] < 0:
        data["prestamos"][uid]["restante"] = 0
    
    # Obtener información del préstamo para el mensaje
    prestamo = data["prestamos"][uid]
    restante = prestamo["restante"]
    save_json("cuentas"); save_json("prestamos")
    
    # Respuesta pública con embed
    embed_publico = discord.Embed(
        title="💳 Pago Realizado",
        description=f"Has pagado **{cantidad}€** de tu préstamo",
        color=discord.Color.blue()
    )
    embed_publico.add_field(name="💰 Pagado", value=f"{cantidad}€", inline=True)
    embed_publico.add_field(name="📊 Restante", value=f"{restante}€", inline=True)
    if restante == 0:
        embed_publico.add_field(name="🎉 Estado", value="**¡PRÉSTAMO LIQUIDADO!**", inline=False)
        embed_publico.color = discord.Color.green()
    embed_publico.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed_publico.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed_publico)
    
    # Enviar notificación por mensaje directo
    try:
        user = bot.get_user(int(uid))
        if user:
            embed = discord.Embed(
                title="💳 Pago de Préstamo Registrado",
                description=f"Has realizado un pago de **{cantidad}€** a tu préstamo.",
                color=discord.Color.blue()
            )
            embed.add_field(name="💰 Cantidad Pagada", value=f"{cantidad}€", inline=True)
            embed.add_field(name="📊 Restante", value=f"{restante}€", inline=True)
            if restante == 0:
                embed.add_field(name="🎉 Estado", value="**¡PRÉSTAMO LIQUIDADO!**", inline=False)
                embed.color = discord.Color.green()
            embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
            embed.timestamp = discord.utils.utcnow()
            
            await user.send(embed=embed)
    except Exception:
        # Si falla el MD, no afecta la operación principal
        pass

@tree.command(name="prestamos", description="Ver estado de tu préstamo")
async def prestamos_ver(interaction: Interaction):
    uid = str(interaction.user.id)
    p = data["prestamos"].get(uid)
    if not p or p.get("restante",0) <= 0:
        embed = discord.Embed(
            title="✅ Sin Préstamos",
            description="No tienes préstamos pendientes actualmente.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    
    # Calcular progreso
    total = p.get("cantidad", 0)
    restante = p.get("restante", 0)
    pagado = total - restante
    porcentaje = (pagado / total * 100) if total > 0 else 0
    
    embed = discord.Embed(
        title="📄 Estado de tu Préstamo",
        description=f"Información detallada de tu préstamo activo",
        color=discord.Color.orange()
    )
    embed.add_field(name="💰 Cantidad Original", value=f"{total}€", inline=True)
    embed.add_field(name="💸 Ya Pagado", value=f"{pagado}€", inline=True)
    embed.add_field(name="📊 Restante", value=f"{restante}€", inline=True)
    embed.add_field(name="📅 Fecha Inicio", value=p.get("fecha", "N/A"), inline=True)
    embed.add_field(name="💵 Cuota Diaria", value=f"≈ {p.get('cuota_diaria', 0)}€", inline=True)
    embed.add_field(name="📈 Progreso", value=f"{porcentaje:.1f}%", inline=True)
    embed.set_footer(text="Sistema Bancario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ----------------------
# Parte 3 — TAREA DIARIA PARA DESCONTAR PRÉSTAMOS Y ENVIAR MD
# (PEGA justo después de la Parte 2)
# ----------------------
async def pagos_prestamos_diarios():
    await bot.wait_until_ready()
    while not bot.is_closed():
        hoy = datetime.date.today().isoformat()
        for uid, p in list(data.get("prestamos", {}).items()):
            if p.get("restante",0) <= 0:
                continue
            # aplicar una cuota diaria si no aplicada hoy
            ultimo = p.get("ultimo_descuento")
            if ultimo == hoy:
                continue
            cuota = p.get("cuota_diaria", max(1, p["cantidad"] // max(1,p["dias_totales"])))
            # asegurar cuenta
            if uid in data["cuentas"] and data["cuentas"][uid]["tarjeta"] >= cuota:
                data["cuentas"][uid]["tarjeta"] -= cuota
                p["restante"] -= cuota
                p["ultimo_descuento"] = hoy
                save_json("cuentas"); save_json("prestamos")
                # notificar por MD con embed
                user = bot.get_user(int(uid))
                if user:
                    try:
                        embed_md = discord.Embed(
                            title="💸 Pago Automático de Préstamo",
                            description=f"Se ha descontado automáticamente **{cuota}€** de tu cuenta para el pago de tu préstamo.",
                            color=discord.Color.blue()
                        )
                        embed_md.add_field(name="💰 Descontado", value=f"{cuota}€", inline=True)
                        embed_md.add_field(name="📊 Restante", value=f"{p['restante']}€", inline=True)
                        embed_md.add_field(name="💳 Saldo en tarjeta", value=f"{data['cuentas'][uid]['tarjeta']}€", inline=True)
                        if p['restante'] == 0:
                            embed_md.add_field(name="🎉 ¡Préstamo Completado!", value="Has liquidado completamente tu préstamo.", inline=False)
                            embed_md.color = discord.Color.green()
                        embed_md.set_footer(text="Sistema Bancario Automático • Valencia RP ESP")
                        embed_md.timestamp = discord.utils.utcnow()
                        
                        await user.send(embed=embed_md)
                    except:
                        pass
            else:
                # si no tiene saldo suficiente se registra intento y no se paga
                p["ultimo_descuento"] = hoy  # evitar bucle diario, se intentará descontar cada día pero no quitar más
                save_json("prestamos")
        await asyncio.sleep(24*60*60)  # dormir 24h

# ----------------------
# Parte 4 — INVENTARIO, TIENDA, ENTREGAR/ROBAR OBJETOS
# ----------------------
# Ver inventario propio
@tree.command(name="inventario", description="Ver tu inventario")
async def inventario(interaction: Interaction):
    uid = str(interaction.user.id)
    inv = data["inventario"].get(uid, {})
    
    if not inv:
        embed = discord.Embed(
            title="🎒 | Inventario",
            description="Tu inventario está vacío. ¡Compra objetos en la tienda o comercia con otros jugadores!",
            color=discord.Color.light_grey()
        )
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    
    # Contar total de items
    total_items = sum(inv.values())
    
    embed = discord.Embed(
        title="📦 Tu Inventario",
        description=f"Tienes **{total_items}** objetos en total",
        color=discord.Color.blue()
    )
    
    # Mostrar items en chunks para evitar límite de fields
    items_text = []
    for item, cantidad in inv.items():
        items_text.append(f"**{item}**: {cantidad}")
    
    # Dividir en grupos de 10 para mejor visualización
    for i in range(0, len(items_text), 10):
        chunk = items_text[i:i+10]
        embed.add_field(
            name=f"📋 Objetos ({i+1}-{min(i+10, len(items_text))})" if len(items_text) > 10 else "📋 Tus Objetos",
            value="\n".join(chunk),
            inline=True
        )
    
    embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="mirar-inventario", description="Ver inventario de otro usuario")
@app_commands.describe(usuario="Usuario")
async def mirar_inventario(interaction: Interaction, usuario: discord.Member):
    tid = str(usuario.id)
    inv = data["inventario"].get(tid, {})
    
    if not inv:
        embed = discord.Embed(
            title="📦 Inventario Vacío",
            description=f"{usuario.mention} no tiene objetos en su inventario.",
            color=discord.Color.light_grey()
        )
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    
    # Contar total de items
    total_items = sum(inv.values())
    
    embed = discord.Embed(
        title=f"📦 Inventario de {usuario.display_name}",
        description=f"Tiene **{total_items}** objetos en total",
        color=discord.Color.purple()
    )
    
    # Mostrar items
    items_text = []
    for item, cantidad in inv.items():
        items_text.append(f"**{item}**: {cantidad}")
    
    # Dividir en grupos para mejor visualización
    for i in range(0, len(items_text), 10):
        chunk = items_text[i:i+10]
        embed.add_field(
            name=f"📋 Objetos ({i+1}-{min(i+10, len(items_text))})" if len(items_text) > 10 else "📋 Sus Objetos",
            value="\n".join(chunk),
            inline=True
        )
    
    embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
    embed.set_thumbnail(url=usuario.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="entregar-objeto", description="Entregar un objeto a otro usuario")
@app_commands.describe(usuario="Usuario", objeto="Nombre del objeto", cantidad="Cantidad")
async def entregar_objeto(interaction: Interaction, usuario: discord.Member, objeto: str, cantidad: int):
    if cantidad <= 0:
        embed = discord.Embed(
            title="❌ Cantidad Inválida",
            description="La cantidad debe ser mayor que 0.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    uid = str(interaction.user.id); tid = str(usuario.id)
    inv = data["inventario"].get(uid, {})
    if inv.get(objeto,0) < cantidad:
        embed = discord.Embed(
            title="❌ Inventario Insuficiente",
            description=f"No tienes suficiente **{objeto}** en tu inventario.",
            color=discord.Color.red()
        )
        tengo = inv.get(objeto, 0)
        embed.add_field(name="📦 Tienes", value=f"{tengo} {objeto}", inline=True)
        embed.add_field(name="📤 Necesitas", value=f"{cantidad} {objeto}", inline=True)
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    inv[objeto] -= cantidad
    if inv[objeto] <= 0:
        del inv[objeto]
    data["inventario"][uid] = inv
    target_inv = data["inventario"].get(tid, {})
    target_inv[objeto] = target_inv.get(objeto,0) + cantidad
    data["inventario"][tid] = target_inv
    save_json("inventario")
    
    # Respuesta con embed
    embed = discord.Embed(
        title="✅ Objeto Entregado",
        description=f"Has entregado exitosamente **{cantidad}x {objeto}** a {usuario.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="📦 Objeto", value=objeto, inline=True)
    embed.add_field(name="🔢 Cantidad", value=f"{cantidad}x", inline=True)
    embed.add_field(name="👤 Destinatario", value=usuario.mention, inline=True)
    embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="robar-inventario", description="Intentar robar un objeto del inventario de otro (éxito aleatorio)")
@app_commands.describe(objeto="Objeto a robar", usuario="Objetivo")
async def robar_inventario(interaction: Interaction, usuario: discord.Member, objeto: str):
    uid = str(interaction.user.id); tid = str(usuario.id)
    target_inv = data["inventario"].get(tid, {})
    if target_inv.get(objeto,0) <= 0:
        embed = discord.Embed(
            title="❌ Objeto No Encontrado",
            description=f"{usuario.mention} no tiene **{objeto}** en su inventario.",
            color=discord.Color.red()
        )
        embed.add_field(name="🔎 Objetivo", value=usuario.mention, inline=True)
        embed.add_field(name="📦 Objeto Buscado", value=objeto, inline=True)
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    # probabilidad simple
    if random.random() < 0.5:
        # exito
        target_inv[objeto] -= 1
        if target_inv[objeto] <= 0: del target_inv[objeto]
        data["inventario"][tid] = target_inv
        inv = data["inventario"].get(uid, {})
        inv[objeto] = inv.get(objeto,0) + 1
        data["inventario"][uid] = inv
        save_json("inventario")
        
        # Robo exitoso - embed
        embed = discord.Embed(
            title="💰 Robo Exitoso",
            description=f"Has robado exitosamente **1x {objeto}** de {usuario.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="🎯 Objetivo", value=usuario.mention, inline=True)
        embed.add_field(name="📦 Objeto Robado", value=objeto, inline=True)
        embed.add_field(name="🍀 Suerte", value="¡Éxito!", inline=True)
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        # Robo fallido - embed
        embed = discord.Embed(
            title="❌ Robo Fallido",
            description=f"No lograste robar el **{objeto}** de {usuario.mention}. ¡Mala suerte!",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="🎯 Objetivo", value=usuario.mention, inline=True)
        embed.add_field(name="📦 Objeto", value=objeto, inline=True)
        embed.add_field(name="💔 Resultado", value="Fallido", inline=True)
        embed.set_footer(text="Sistema de Inventario • Valencia RP ESP")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Tienda y compra de objetos
TIENDA = {
    "Linterna":50, "Cuchillo":100, "Martillo":100, "Bate de béisbol":150,
    "Palanca":250, "Beretta M9":900, "LEMAT Revolver":1000, "COLT M1911":1200
}

@tree.command(name="tienda", description="Ver tienda")
async def tienda(interaction: Interaction):
    embed = discord.Embed(
        title="🛒 | Tienda",
        description="Los objetos que están en stock aparecerán en la lista:",
        color=discord.Color.gold()
    )
    
    # Organizar items por precio
    items_ordenados = sorted(TIENDA.items(), key=lambda x: x[1])
    
    items_text = []
    for item, precio in items_ordenados:
        items_text.append(f"**{item}**: `{precio}€`")
    
    # Dividir en columnas para mejor visualización
    mid = len(items_text) // 2
    if items_text:
        embed.add_field(
            name="📦 Artículos (1-5)", 
            value="\n".join(items_text[:mid]),
            inline=True
        )
        embed.add_field(
            name="📦 Artículos (6+)", 
            value="\n".join(items_text[mid:]) if mid < len(items_text) else "─",
            inline=True
        )
    
    embed.add_field(
        name="💡 Cómo Comprar",
        value="Usa `/comprar-objeto` seguido del nombre exacto del objeto",
        inline=False
    )
    embed.set_footer(text="Sistema de Tienda • Valencia RP ESP")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="comprar-objeto", description="Comprar objeto de la tienda")
@app_commands.describe(objeto="Nombre exacto del objeto")
async def comprar_objeto(interaction: Interaction, objeto: str):
    if objeto not in TIENDA:
        embed = discord.Embed(
            title="❌ Objeto No Disponible",
            description=f"El objeto **{objeto}** no está disponible en la tienda.",
            color=discord.Color.red()
        )
        embed.add_field(name="💡 Sugerencia", value="Usa `/tienda` para ver todos los productos disponibles.", inline=False)
        embed.set_footer(text="Sistema de Tienda • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    precio = TIENDA[objeto]
    uid = str(interaction.user.id)
    if uid not in data["cuentas"] or data["cuentas"][uid]["tarjeta"] < precio:
        embed = discord.Embed(
            title="❌ Dinero Insuficiente",
            description="No tienes suficiente dinero en tu tarjeta para comprar este objeto.",
            color=discord.Color.red()
        )
        saldo_actual = data["cuentas"].get(uid, {}).get("tarjeta", 0)
        embed.add_field(name="💳 Tu Saldo", value=f"{saldo_actual}€", inline=True)
        embed.add_field(name="💰 Precio", value=f"{precio}€", inline=True)
        embed.add_field(name="📦 Objeto", value=objeto, inline=True)
        embed.set_footer(text="Sistema de Tienda • Valencia RP ESP")
        await interaction.response.send_message(embed=embed, ephemeral=True); return
    data["cuentas"][uid]["tarjeta"] -= precio
    inv = data["inventario"].get(uid, {})
    inv[objeto] = inv.get(objeto,0) + 1
    data["inventario"][uid] = inv
    save_json("cuentas"); save_json("inventario")
    
    # Respuesta con embed
    embed = discord.Embed(
        title="✅ Compra Realizada",
        description=f"Has comprado exitosamente **{objeto}** por **{precio}€**",
        color=discord.Color.green()
    )
    embed.add_field(name="🛍️ Objeto", value=objeto, inline=True)
    embed.add_field(name="💰 Precio", value=f"{precio}€", inline=True)
    embed.add_field(name="💳 Saldo restante", value=f"{data['cuentas'][uid]['tarjeta']}€", inline=True)
    embed.set_footer(text="Sistema de Tienda • Valencia RP ESP")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ----------------------
# Parte 5 — MULTAS, ELIMINAR MULTA, VEHÍCULOS, DOCUMENTACIÓN
# ----------------------
# Código Penal Completo de Valencia
CODIGO_PENAL = {
    # Título I: Delitos contra la seguridad del Tránsito
    "1.1": {"descripcion":"Conducción sin permiso","precio":300},
    "1.2": {"descripcion":"Conducción bajo efectos del alcohol","precio":500},
    "1.3": {"descripcion":"Conducción temeraria","precio":600},
    "1.4": {"descripcion":"Conducción sin seguro obligatorio","precio":400},
    "1.5": {"descripcion":"Uso del móvil al conducir","precio":150},
    
    # Título II: Delitos contra la propiedad
    "2.1": {"descripcion":"Hurto menor","precio":200},
    "2.2": {"descripcion":"Daños a la propiedad","precio":250},
    "2.3": {"descripcion":"Usurpación de identidad","precio":300},
    "2.4": {"descripcion":"Vandalismo","precio":350},
    "2.5": {"descripcion":"Apropiación indebida","precio":400},
    
    # Título III: Delitos contra la salud pública
    "3.1": {"descripcion":"Consumo de sustancias ilegales","precio":300},
    "3.2": {"descripcion":"Posesión de sustancias ilegales","precio":400},
    "3.3": {"descripcion":"Tráfico de sustancias ilegales","precio":500},
    "3.4": {"descripcion":"Producción de sustancias ilegales","precio":600},
    "3.5": {"descripcion":"Cultivo de sustancias ilegales","precio":700},
    
    # Título IV: Delitos contra la persona (penas de prisión - multas simbólicas para RP)
    "4.1": {"descripcion":"Homicidio - Pena de prisión de 10 a 20 años","precio":2000},
    "4.2": {"descripcion":"Lesiones graves - Pena de prisión de 5 a 10 años","precio":1500},
    "4.3": {"descripcion":"Amenazas graves - Pena de prisión de 2 a 5 años","precio":800},
    "4.4": {"descripcion":"Acoso - Pena de prisión de 3 a 6 años","precio":1000},
    "4.5": {"descripcion":"Violencia doméstica - Pena de prisión de 4 a 8 años","precio":1200},
    
    # Título V: Delitos contra la libertad
    "5.1": {"descripcion":"Secuestro - Pena de prisión de 8 a 15 años","precio":2500},
    "5.2": {"descripcion":"Coacciones - Pena de prisión de 3 a 6 años","precio":1000},
    "5.3": {"descripcion":"Amenazas - Pena de prisión de 2 a 4 años","precio":800},
    "5.4": {"descripcion":"Tortura - Pena de prisión de 6 a 12 años","precio":2000},
    "5.5": {"descripcion":"Tráfico de personas - Pena de prisión de 10 a 20 años","precio":3000},
    
    # Título VI: Delitos contra el orden público
    "6.1": {"descripcion":"Terrorismo - Pena de prisión de 15 a 30 años","precio":5000},
    "6.2": {"descripcion":"Rebelión - Pena de prisión de 12 a 25 años","precio":4000},
    "6.3": {"descripcion":"Sedición - Pena de prisión de 8 a 15 años","precio":3000},
    "6.4": {"descripcion":"Desórdenes públicos - Pena de prisión de 1 a 3 años","precio":600},
    "6.5": {"descripcion":"Atentado contra la autoridad - Pena de prisión de 2 a 5 años","precio":1000}
}

# ID del rol de Policía (cámbialo por el tuyo)
ROL_POLICIA_ID = 1401538045567565877  

@tree.command(name="multas-poner", description="Poner multas mediante códigos (ej: 1.1,2.3) - SOLO POLICÍA")
@app_commands.describe(usuario="Usuario a multar", articulos="Códigos separados por coma")
async def multas_poner(interaction: Interaction, usuario: discord.Member, articulos: str):
    # 🔒 Verificación: solo usuarios con rol Policía
    if ROL_POLICIA_ID not in [r.id for r in interaction.user.roles]:
        embed = discord.Embed(
            title="🚫 Acceso Denegado",
            description="Este comando solo puede ser usado por la Policía Local de Valencia.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚖️ Requerido", value="Rol de Policía", inline=True)
        embed.set_footer(text="Sistema de Multas • Código Penal de Valencia")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    cods = [c.strip() for c in articulos.split(",") if c.strip()]
    lista = []; total = 0
    for c in cods:
        if c in CODIGO_PENAL:
            lista.append({"codigo":c, **CODIGO_PENAL[c]})
            total += CODIGO_PENAL[c]["precio"]

    codigo = generar_codigo_multa()
    uid = str(usuario.id)
    if uid not in data["multas"]:
        data["multas"][uid] = []
    data["multas"][uid].append({
        "codigo":codigo, 
        "agente":interaction.user.mention, 
        "articulos":lista, 
        "total":total, 
        "fecha": datetime.date.today().isoformat()
    })
    save_json("multas")

    # Embed profesional
    embed = discord.Embed(
        title="⚖️ Multa Impuesta",
        description=f"Se ha impuesto una multa a {usuario.mention}",
        color=discord.Color.red()
    )
    embed.add_field(name="🚔 Agente", value=interaction.user.mention, inline=True)
    embed.add_field(name="📄 Código", value=codigo, inline=True)
    embed.add_field(name="💰 Total", value=f"{total}€", inline=True)

    articulos_texto = []
    for art in lista:
        articulos_texto.append(f"**Art. {art['codigo']}**: {art['descripcion']} ({art['precio']}€)")

    if articulos_texto:
        embed.add_field(
            name="📋 Artículos Infringidos", 
            value="\n".join(articulos_texto), 
            inline=False
        )

    embed.set_footer(text="Sistema de Multas • Código Penal de Valencia")
    embed.set_author(name=f"Multa para {usuario.display_name}", icon_url=usuario.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    await interaction.response.send_message(embed=embed)


@tree.command(name="multas-ver", description="Ver historial de multas de un usuario")
@app_commands.describe(usuario="Usuario")
async def multas_ver(interaction: Interaction, usuario: discord.Member):
    uid = str(usuario.id)
    embed = discord.Embed(
        title=f"📄 Registro de multas de {usuario.display_name}",
        description="Antecedentes del usuario seleccionado",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=usuario.display_avatar.url)
    
    multas = data.get("multas", {}).get(uid, [])
    if not multas:
        embed.add_field(name="✅ Antecedentes", value="Sin antecedentes de multas", inline=False)
        embed.add_field(name="🔍 Estado de búsqueda", value="Limpio", inline=True)
        embed.add_field(name="🚗 Vehículo robado", value="Los papeles están en orden", inline=True)
        embed.add_field(name="📄 Licencia", value=("Posee la licencia en orden" if uid in data.get("carnets",{}) else "No posee licencia"), inline=True)
        embed.add_field(name="🛡️ Seguro vehículo", value="Seguro inactivo", inline=True)
        embed.set_footer(text="Sistema de Consultas • Código Penal de Valencia")
        await interaction.response.send_message(embed=embed); return
    
    total_all = 0
    for i, m in enumerate(multas, start=1):
        # Formato exacto como el ejemplo del usuario
        articulos_text = []
        for a in m["articulos"]:
            articulos_text.append(f"Artículo {a['codigo']}: {a['descripcion']} - {a['precio']}€")
        
        multa_info = f"""**Agente:** {m['agente']}
**Artículos:** {', '.join(articulos_text)}
**Código:** {m['codigo']}
**Fecha:** {m.get('fecha', 'No registrada')}"""
        
        embed.add_field(
            name=f"⚖️ Multa Nº {i}",
            value=multa_info,
            inline=False
        )
        total_all += m['total']
    
    # Estado general del usuario
    embed.add_field(name="📊 Total Acumulado", value=f"**{total_all}€**", inline=True)
    embed.add_field(name="📄 Licencia", value=("✅ Posee licencia" if uid in data.get("carnets",{}) else "❌ Sin licencia"), inline=True)
    embed.add_field(name="🚗 Estado Vehicular", value="En revisión", inline=True)
    
    embed.set_footer(text="Sistema de Consultas • Código Penal de Valencia")
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="pagar-multas", description="Pagar multa por código")
@app_commands.describe(codigo="Código de multa", cantidad="Cantidad a pagar")
async def pagar_multas(interaction: Interaction, codigo: str, cantidad: int):
    uid_user = str(interaction.user.id)
    for uid, lista in data["multas"].items():
        for multa in lista:
            if multa["codigo"] == codigo:
                if uid_user not in data["cuentas"] or data["cuentas"][uid_user]["tarjeta"] < cantidad:
                    await interaction.response.send_message("❌ No tienes saldo para pagar.", ephemeral=True); return
                if cantidad < multa["total"]:
                    await interaction.response.send_message(f"❌ Debes pagar al menos {multa['total']}€", ephemeral=True); return
                data["cuentas"][uid_user]["tarjeta"] -= cantidad
                lista.remove(multa)
                save_json("multas"); save_json("cuentas")
                
                # Respuesta con embed profesional
                embed = discord.Embed(
                    title="✅ Multa Pagada",
                    description=f"Has pagado exitosamente la multa **{codigo}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="📄 Código de Multa", value=codigo, inline=True)
                embed.add_field(name="💰 Cantidad Pagada", value=f"{cantidad}€", inline=True)
                embed.add_field(name="💳 Saldo Restante", value=f"{data['cuentas'][uid_user]['tarjeta']}€", inline=True)
                embed.add_field(name="📊 Total de Multa", value=f"{multa['total']}€", inline=True)
                embed.add_field(name="📅 Fecha de Pago", value=datetime.date.today().strftime("%d/%m/%Y"), inline=True)
                embed.add_field(name="✅ Estado", value="**LIQUIDADA**", inline=True)
                embed.set_footer(text="Sistema de Multas • Código Penal de Valencia")
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                
                await interaction.response.send_message(embed=embed)
                return
    await interaction.response.send_message("❌ Código no encontrado.", ephemeral=True)

@tree.command(name="multas-eliminar", description="Eliminar una multa por código (SOLO STAFF)")
@app_commands.describe(usuario="Usuario", codigo="Código de la multa")
async def multas_eliminar(interaction: Interaction, usuario: discord.Member, codigo: str):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff.", ephemeral=True); return
    uid = str(usuario.id)
    lista = data.get("multas", {}).get(uid, [])
    for m in lista:
        if m["codigo"] == codigo:
            lista.remove(m); save_json("multas")
            # Respuesta con embed profesional
            embed = discord.Embed(
                title="🗑️ Multa Eliminada",
                description=f"La multa **{codigo}** ha sido eliminada del historial de {usuario.mention}",
                color=discord.Color.blue()
            )
            embed.add_field(name="📄 Código", value=codigo, inline=True)
            embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="🚔 Staff", value=interaction.user.mention, inline=True)
            embed.set_footer(text="Sistema Administrativo • Código Penal de Valencia")
            embed.set_author(name="Eliminación de Multa", icon_url=interaction.user.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=embed)
            return
    await interaction.response.send_message("❌ No encontrada.", ephemeral=True)

# ID del rol de Policía (cámbialo por el tuyo)
ROL_POLICIA_ID = 1401538045567565877  

# Vehículos: incautar
@tree.command(name="incautar", description="Incautar vehículo a un usuario - SOLO POLICÍA")
@app_commands.describe(usuario="Usuario", matricula="Matrícula", modelo="Modelo", articulos="Artículos/motivo")
async def incautar(interaction: Interaction, usuario: discord.Member, matricula: str, modelo: str, articulos: str):
    # 🔒 Verificación: solo rol Policía
    if ROL_POLICIA_ID not in [r.id for r in interaction.user.roles]:
        embed = discord.Embed(
            title="🚫 Acceso Denegado",
            description="Este comando solo puede ser usado por la Policía.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚖️ Requerido", value="Rol de Policía", inline=True)
        embed.set_footer(text="Sistema de Vehículos • Policía de Valencia")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    uid = str(usuario.id)
    if uid not in data["vehiculos"]:
        data["vehiculos"][uid] = []
    data["vehiculos"][uid].append({
        "matricula": matricula, 
        "modelo": modelo, 
        "motivo": articulos, 
        "fecha": datetime.date.today().isoformat()
    })
    save_json("vehiculos")
    await interaction.response.send_message(
        f"✅ Vehículo **{modelo}** ({matricula}) incautado a {usuario.mention}"
    )


# Vehículos: retirar
@tree.command(name="retirar", description="Retirar licencia o devolver vehículo - SOLO POLICÍA")
@app_commands.describe(usuario="Usuario", licencia="Retirar licencia (Sí/No)", vehiculo="Retirar vehículo (Sí/No)")
@app_commands.choices(
    licencia=[app_commands.Choice(name="Sí", value="SI"), app_commands.Choice(name="No", value="NO")],
    vehiculo=[app_commands.Choice(name="Sí", value="SI"), app_commands.Choice(name="No", value="NO")]
)
async def retirar(interaction: Interaction, usuario: discord.Member, licencia: app_commands.Choice[str], vehiculo: app_commands.Choice[str]):
    # 🔒 Verificación: solo rol Policía
    if ROL_POLICIA_ID not in [r.id for r in interaction.user.roles]:
        embed = discord.Embed(
            title="🚫 Acceso Denegado",
            description="Este comando solo puede ser usado por la Policía.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚖️ Requerido", value="Rol de Policía", inline=True)
        embed.set_footer(text="Sistema de Vehículos • Policía de Valencia")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    uid = str(usuario.id)
    mensajes = []

    if licencia.value == "SI":
        if uid in data["carnets"]:
            del data["carnets"][uid]
            save_json("carnets")
            mensajes.append("🚫 Licencia retirada")
        else:
            mensajes.append("ℹ️ No tenía licencia")

    if vehiculo.value == "SI":
        if uid in data["vehiculos"] and data["vehiculos"][uid]:
            data["vehiculos"].pop(uid, None)
            save_json("vehiculos")
            mensajes.append("🚔 Vehículos retirados")
        else:
            mensajes.append("ℹ️ No tenía vehículos incautados")

    await interaction.response.send_message("\n".join(mensajes))


# ----------------------
# Parte 6 — SANCIONES (poner / quitar / ver) — EMBED bonito
# ----------------------
@tree.command(name="poner-sancion", description="Imponer sanción a un usuario (SOLO STAFF)")
@app_commands.describe(usuario="Usuario sancionado", motivo="Motivo", apelable="Apelable (🟩/🟥)", tipo="Tipo (Sancion 1..8)")
@app_commands.choices(apelable=[app_commands.Choice(name="🟩", value="🟩"), app_commands.Choice(name="🟥", value="🟥")],
                      tipo=[app_commands.Choice(name=f"Sancion {i}", value=f"Sancion {i}") for i in range(1,9)])
async def poner_sancion(interaction: Interaction, usuario: discord.Member, motivo: str, apelable: app_commands.Choice[str], tipo: app_commands.Choice[str]):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff puede.", ephemeral=True); return
    uid = str(usuario.id)
    s = {"staff": interaction.user.mention, "motivo": motivo, "fecha": datetime.date.today().strftime("%d/%m/%Y"), "apelable": apelable.value, "tipo": tipo.value}
    data["sanciones"].setdefault(uid, []).append(s)
    save_json("sanciones")
    # mensaje público
    embed = Embed(title="⚠️ Nueva sanción impuesta", color=discord.Color.red())
    embed.add_field(name="Usuario", value=usuario.mention, inline=True)
    embed.add_field(name="Impuesta por", value=interaction.user.mention, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    embed.add_field(name="Tipo", value=tipo.value, inline=True)
    embed.add_field(name="Apelable", value=apelable.value, inline=True)
    embed.set_footer(text="Si desea apelar, visite el servidor de apelaciones.")
    await interaction.response.send_message(embed=embed)

@tree.command(name="quitar-sancion", description="Quitar sanción por número (SOLO STAFF)")
@app_commands.describe(usuario="Usuario", numero="Número de sanción (ej: 1)")
async def quitar_sancion(interaction: Interaction, usuario: discord.Member, numero: int):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff.", ephemeral=True); return
    uid = str(usuario.id)
    if uid not in data["sanciones"] or numero < 1 or numero > len(data["sanciones"][uid]):
        await interaction.response.send_message("❌ Número inválido.", ephemeral=True); return
    elim = data["sanciones"][uid].pop(numero-1); save_json("sanciones")
    embed = Embed(title="✅ Sanción eliminada", color=discord.Color.green())
    embed.add_field(name="Usuario", value=usuario.mention)
    embed.add_field(name="Motivo eliminado", value=elim.get("motivo","-"))
    await interaction.response.send_message(embed=embed)

@tree.command(name="sanciones-ver", description="Ver sanciones de un usuario (público)")
@app_commands.describe(usuario="Usuario a consultar")
async def sanciones_ver(interaction: Interaction, usuario: discord.Member):
    uid = str(usuario.id)
    sancs = data.get("sanciones", {}).get(uid, [])
    if not sancs:
        embed = Embed(title=f"Registro de sanciones de {usuario.display_name}", color=discord.Color.green())
        embed.add_field(name="Antecedentes", value="Sin sanciones", inline=False)
        await interaction.response.send_message(embed=embed); return
    embed = Embed(title=f"📋 Sanciones de {usuario.display_name}", description=f"Este usuario tiene {len(sancs)} sanción(es):", color=discord.Color.orange())
    for i, s in enumerate(sancs, start=1):
        embed.add_field(name=f"Sanción Nº {i}", value=f"{s.get('staff')}\n{s.get('motivo')} - {s.get('fecha')}\nApelable: {s.get('apelable')}\nTipo: {s.get('tipo')}", inline=False)
    await interaction.response.send_message(embed=embed)

# ----------------------
# Parte 7 — VOTACIONES, RECLAMAR ROBO (confirmación negociador), MANTENIMIENTO y ADMIN
# ----------------------
# Votaciones con botón hasta 5 votos; staff puede abrir manualmente
class VotacionView(View):
    def __init__(self, tema):
        super().__init__(timeout=None)
        self.tema = tema
        self.votantes = set()
        self.btn_votar = Button(label="Votar (0/5)", style=discord.ButtonStyle.green)
        self.btn_votar.callback = self.votar
        self.add_item(self.btn_votar)
        self.btn_abrir = Button(label="Abrir Server (Staff)", style=discord.ButtonStyle.red)
        self.btn_abrir.callback = self.abrir_server
        self.add_item(self.btn_abrir)

    async def votar(self, interaction: Interaction):
        if interaction.user.id in self.votantes:
            await interaction.response.send_message("❌ Ya votaste.", ephemeral=True); return
        self.votantes.add(interaction.user.id)
        self.btn_votar.label = f"Votar ({len(self.votantes)}/5)"
        await interaction.response.edit_message(view=self)
        if len(self.votantes) >= 5:
            usuarios_ping = " ".join(f"<@{uid}>" for uid in self.votantes)
            await interaction.followup.send(f"✅ Votación completada. Pingeando a: {usuarios_ping}")
            self.stop()

    async def abrir_server(self, interaction: Interaction):
        if not es_staff(interaction.user):
            await interaction.response.send_message("🚫 Solo staff.", ephemeral=True); return
        # enviar mensaje de apertura en el canal (no editar el mensaje original)
        await interaction.response.send_message(f"🔓 {interaction.user.mention} abrió el server manualmente.", ephemeral=False)
        self.stop()

@tree.command(name="abrir-votacion", description="Abrir una votación con botón")
@app_commands.describe(tema="Tema de la votación")
async def abrir_votacion(interaction: Interaction, tema: str):
    embed = Embed(title="📢 Nueva votación", description=f"**Tema:** {tema}\nPulsa el botón para votar. Se necesitan 5 votos.", color=discord.Color.blurple())
    view = VotacionView(tema)
    await interaction.response.send_message(embed=embed, view=view)

# Reclamar robo: se envía embed, bot pregunta al negociador (se le @), negociador responde haciendo REPLY con "Confirmo" al mensaje del bot.
@tree.command(name="reclamar-robo", description="Solicitar cobro de robo (negociador debe confirmar)")
@app_commands.describe(establecimiento="Establecimiento", atracadores="Número de atracadores", rehenes="Número de rehenes", negociador="Negociador (mención)", negociado="Negociado/negociaciones", tipo="Limpio/Sucio", botin_reducido="Botín reducido (%)", prueba="Prueba o nota")
@app_commands.choices(establecimiento=[app_commands.Choice(name=e, value=e) for e in ["Gasolinera","Casa","Tienda","Armería","Joyería","Banco","Furgón Blindado"]],
                      tipo=[app_commands.Choice(name=t, value=t) for t in ["Limpio","Sucio"]])
async def reclamar_robo(interaction: Interaction, establecimiento: app_commands.Choice[str], atracadores: int, rehenes: int, negociador: discord.Member, negociado: str, tipo: app_commands.Choice[str], botin_reducido: int, prueba: str):
    # calcular botin estimado simple
    botin_estimado = max(0, atracadores * 1000 - int(botin_reducido/100 * atracadores * 1000))
    embed = Embed(title="🚨 | Solicitud de robo", color=discord.Color.red(), timestamp=discord.utils.utcnow())
    embed.add_field(name="🏢 Establecimiento", value=establecimiento.value, inline=True)
    embed.add_field(name="💰 Botín estimado", value=f"{botin_estimado}€", inline=True)
    embed.add_field(name="👥 Atracadores", value=str(atracadores), inline=True)
    embed.add_field(name="🔫 Rehenes", value=str(rehenes), inline=True)
    embed.add_field(name="💬 Negociaciones", value=(negociado or "n/a no vinieron"), inline=True)
    embed.add_field(name="🤝 Negociador", value=negociador.mention, inline=True)
    embed.add_field(name="✅ Robo limpio", value=tipo.value, inline=True)
    embed.add_field(name="📉 Botín reducido", value=f"{botin_reducido}%", inline=True)
    embed.add_field(name="Prueba/Nota", value=prueba or "N/A", inline=False)
    embed.set_footer(text=f"Atraco solicitado por {interaction.user.name} a las {datetime.datetime.utcnow().strftime('%H:%M:%S UTC')}")
    # enviar embed y luego mensaje pidiendo confirmación (guardar mensaje)
    await interaction.response.send_message(embed=embed)
    confirm_msg = await interaction.followup.send(f"{negociador.mention}, podría confirmar el robo? Si es así responde A ESTE MENSAJE con **Confirmo** (usa reply).")
    # check: author is negociador, content "confirmo", and message is a reply to confirm_msg
    def check(m):
        return m.author.id == negociador.id and m.content.lower().strip() == "confirmo" and m.reference and m.reference.message_id == confirm_msg.id
    try:
        msg = await bot.wait_for("message", timeout=3600.0, check=check)
        # si confirma, ping al rol economía
        guild = interaction.guild
        rol = guild.get_role(ECONOMIA_ROLE_ID) if guild else None
        if rol:
            await interaction.channel.send(f"{rol.mention} ✅ El negociador ha confirmado el robo. Procedan a entregar el dinero.")
        else:
            await interaction.channel.send("⚠️ No se encontró el rol Encargado Economía.")
    except asyncio.TimeoutError:
        await interaction.channel.send(f"❌ Tiempo de confirmación expirado. El negociador {negociador.mention} no respondió.")

# Mantenimiento: encender/apagar (solo staff)
@tree.command(name="mantenimiento", description="Activar/desactivar modo mantenimiento (SOLO STAFF)")
@app_commands.describe(activar="Activar o desactivar (Sí/No)")
@app_commands.choices(activar=[app_commands.Choice(name="Activar", value="SI"), app_commands.Choice(name="Desactivar", value="NO")])
async def mantenimiento(interaction: Interaction, activar: app_commands.Choice[str]):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff.", ephemeral=True); return
    config = data.get("config", {})
    config["mantenimiento"] = True if activar.value == "SI" else False
    data["config"] = config; save_json("config")
    await interaction.response.send_message(f"🔧 Mantenimiento {'activado' if config['mantenimiento'] else 'desactivado'}.")

# ----------------------
# --- COMANDOS DE DNI ---
# ----------------------
# La función generar_dni ya está definida en la sección de utilidades (línea 74)

@tree.command(name="solicitar-dni", description="Solicitar un DNI")
@app_commands.describe(
    usuario="Usuario",
    apellidos="Apellidos",
    nombre="Nombre",
    edad="Edad",
    sexo="Sexo",
    nacimiento="Fecha de nacimiento",
    nacionalidad="Nacionalidad",
    foto="Adjunta una foto (PNG)"
)
@app_commands.choices(sexo=[
    app_commands.Choice(name="Masculino", value="Masculino"),
    app_commands.Choice(name="Femenino", value="Femenino")
])
async def solicitar_dni(
    interaction: Interaction,
    usuario: discord.Member,
    apellidos: str,
    nombre: str,
    edad: int,
    sexo: app_commands.Choice[str],
    nacimiento: str,
    nacionalidad: str,
    foto: discord.Attachment
):
    # Validación de la imagen
    if not foto.content_type.startswith("image/"):
        await interaction.response.send_message("La foto debe ser una imagen.", ephemeral=True)
        return
    if not foto.content_type.endswith("/png"):
        await interaction.response.send_message("La foto debe ser en formato PNG.", ephemeral=True)
        return

    canal_revision = interaction.guild.get_channel(1415316625397387318)

    # Hacer ping al rol de revisión
    await canal_revision.send("<@&1416126180888674374>")

    # Crear embed de solicitud
    embed_solicitud = Embed(title="🪪 Solicitud de DNI", color=discord.Color.blue())
    embed_solicitud.add_field(name="Usuario", value=usuario.mention, inline=True)
    embed_solicitud.add_field(name="Nombre completo", value=f"{nombre} {apellidos}", inline=True)
    embed_solicitud.add_field(name="Edad", value=edad, inline=True)
    embed_solicitud.add_field(name="Sexo", value=sexo.value, inline=True)
    embed_solicitud.add_field(name="Fecha de nacimiento", value=nacimiento, inline=True)
    embed_solicitud.add_field(name="Nacionalidad", value=nacionalidad, inline=True)
    embed_solicitud.set_image(url=foto.url)

    # Crear botones de aceptación y rechazo
    view = View()
    view.add_item(Button(label="Aceptar", style=discord.ButtonStyle.green, custom_id="aceptar"))
    view.add_item(Button(label="Rechazar", style=discord.ButtonStyle.red, custom_id="rechazar"))

    # Enviar embed con botones
    mensaje_revision = await canal_revision.send(embed=embed_solicitud, view=view)

    # Función para esperar la interacción del botón
    def check(inter):
        return inter.message.id == mensaje_revision.id

    await interaction.response.send_message("Solicitud de DNI enviada para revisión.", ephemeral=True)

    # Esperar a que alguien presione un botón
    interaction_revision = await interaction.client.wait_for("interaction", check=check)

    # Procesar la acción de aceptar o rechazar
    if interaction_revision.data["custom_id"] == "aceptar":
        dni = generar_dni()
        embed_aprobacion = Embed(
            title="✅ | Solicitud de DNI ha sido aprobada",
            description="Tu solicitud de DNI ha sido aprobada, hecha un vistazo a estos detalles importantes:",
            color=discord.Color.green()
        )
        embed_aprobacion.add_field(name="Número de DNI", value=dni, inline=True)
        embed_aprobacion.add_field(name="Fecha de emisión", value=datetime.date.today().strftime("%d/%m/%Y"), inline=True)
        embed_aprobacion.add_field(name="Fecha de caducidad", value=(datetime.date.today() + datetime.timedelta(days=3650)).strftime("%d/%m/%Y"), inline=True)
        embed_aprobacion.add_field(name="Información adicional", value="Puedes ver tu DNI con el comando `/ver-dni`", inline=False)

        await usuario.send(embed=embed_aprobacion)

    elif interaction_revision.data["custom_id"] == "rechazar":
        modal = Modal(title="Motivo de rechazo")
        modal.add_item(TextInput(label="Motivo de rechazo", placeholder="Ingrese el motivo de rechazo"))
        await interaction_revision.response.send_modal(modal)
        await modal.wait()
        motivo_rechazo = modal.children[0].value

        motivo_rechazo = modal.children[0].value
        embed_denegacion = Embed(title="❌ | Tu solicitud de DNI a sido denegada", color=discord.Color.red())
        embed_denegacion.add_field(name="Motivo", value=motivo_rechazo, inline=True)

        await usuario.send(embed=embed_denegacion)


@tree.command(name="ver-dni", description="Ver el DNI de un usuario")
@app_commands.describe(usuario="Usuario a consultar (opcional, por defecto tú)")
async def ver_dni(interaction: Interaction, usuario: discord.Member = None):
    if usuario is None:
        usuario = interaction.user
    
    uid = str(usuario.id)
    if uid not in data["dnis"]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene DNI registrado.", ephemeral=True)
        return
    
    datos = data["dnis"][uid]
    embed = Embed(title="📃 Documento Nacional de Identidad 📃", color=discord.Color.blue())
    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.add_field(name="Nombre", value=datos["nombre"], inline=True)
    embed.add_field(name="Apellidos", value=datos["apellidos"], inline=True)
    embed.add_field(name="Fecha de Nacimiento", value=datos["fecha"], inline=True)
    embed.add_field(name="Sexo", value=datos["sexo"], inline=True)
    embed.add_field(name="Número de DNI", value=datos["dni"], inline=True)
    embed.set_footer(text="DNI ficticio válido solo dentro del servidor.")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="eliminar-dni", description="Eliminar DNI de un usuario (SOLO STAFF)")
@app_commands.describe(usuario="Usuario")
async def eliminar_dni(interaction: Interaction, usuario: discord.Member):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff.", ephemeral=True)
        return
    
    uid = str(usuario.id)
    if uid not in data["dnis"]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene DNI registrado.", ephemeral=True)
        return
    
    # También eliminar carnet si tiene
    if uid in data["carnets"]:
        del data["carnets"][uid]
        save_json("carnets")
    
    del data["dnis"][uid]
    save_json("dnis")
    
    await interaction.response.send_message(f"✅ DNI (y carnet si existía) eliminado de {usuario.mention}")

# ----------------------
# --- COMANDOS DE CARNETS DE CONDUCIR ---
# ----------------------
@tree.command(name="crear-carnet", description="Crear carnet de conducir (REQUIERE DNI)")
@app_commands.describe(usuario="Usuario", tipo="Tipo de licencia")
@app_commands.choices(tipo=[
    app_commands.Choice(name="🏍️ Motocicleta (A)", value="A"),
    app_commands.Choice(name="🚗 Turismo (B)", value="B"),
    app_commands.Choice(name="🚚 Camión (C)", value="C"),
    app_commands.Choice(name="🚌 Autobús (D)", value="D")
])
async def crear_carnet(interaction: Interaction, usuario: discord.Member, tipo: app_commands.Choice[str]):
    uid = str(usuario.id)
    
    # ¡VALIDACIÓN CLAVE! No puede crear carnet sin DNI
    if uid not in data["dnis"]:
        embed = Embed(title="❌ DNI Requerido", color=discord.Color.red())
        embed.description = f"{usuario.mention} **debe tener un DNI registrado** antes de obtener una licencia de conducir."
        embed.add_field(name="Solución", value="Usa `/crear-dni` primero para obtener tu DNI.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if uid in data["carnets"]:
        await interaction.response.send_message(f"⚠️ {usuario.mention} ya tiene una licencia de conducir.", ephemeral=True)
        return
    
    # Obtener datos del DNI para el carnet
    datos_dni = data["dnis"][uid]
    numero_carnet = f"LC{random.randint(100000, 999999)}"
    fecha_expedicion = datetime.date.today().strftime("%d/%m/%Y")
    
    data["carnets"][uid] = {
        "numero": numero_carnet,
        "tipo": tipo.value,
        "nombre": datos_dni["nombre"],
        "apellidos": datos_dni["apellidos"],
        "dni": datos_dni["dni"],
        "fecha_expedicion": fecha_expedicion,
        "valido": True
    }
    save_json("carnets")
    
    embed = Embed(title="🚗 Licencia de Conducir Expedida", color=discord.Color.green())
    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.add_field(name="Conductor", value=f"{datos_dni['nombre']} {datos_dni['apellidos']}", inline=False)
    embed.add_field(name="DNI", value=datos_dni["dni"], inline=True)
    embed.add_field(name="Número de Licencia", value=numero_carnet, inline=True)
    embed.add_field(name="Tipo", value=f"{tipo.name}", inline=True)
    embed.add_field(name="Fecha de Expedición", value=fecha_expedicion, inline=True)
    embed.set_footer(text="Licencia ficticia válida solo dentro del servidor.")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="ver-carnet", description="Ver licencia de conducir de un usuario")
@app_commands.describe(usuario="Usuario a consultar (opcional, por defecto tú)")
async def ver_carnet(interaction: Interaction, usuario: discord.Member = None):
    if usuario is None:
        usuario = interaction.user
    
    uid = str(usuario.id)
    if uid not in data["carnets"]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene licencia de conducir.", ephemeral=True)
        return
    
    datos = data["carnets"][uid]
    tipo_icons = {"A": "🏍️", "B": "🚗", "C": "🚚", "D": "🚌"}
    icon = tipo_icons.get(datos["tipo"], "🚗")
    
    embed = Embed(title=f"{icon} 📃 Licencia de conducir 📃", color=discord.Color.blue())
    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.add_field(name="Conductor", value=f"{datos['nombre']} {datos['apellidos']}", inline=False)
    embed.add_field(name="DNI", value=datos["dni"], inline=True)
    embed.add_field(name="Número de Licencia", value=datos["numero"], inline=True)
    embed.add_field(name="Tipo", value=f"{icon} Tipo {datos['tipo']}", inline=True)
    embed.add_field(name="Fecha de Expedición", value=datos["fecha_expedicion"], inline=True)
    embed.add_field(name="Estado", value="✅ Válida" if datos.get("valido", True) else "❌ Retirada", inline=True)
    embed.set_footer(text="Licencia ficticia válida solo dentro del servidor.")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="eliminar-carnet", description="Eliminar licencia de conducir (SOLO STAFF)")
@app_commands.describe(usuario="Usuario")
async def eliminar_carnet(interaction: Interaction, usuario: discord.Member):
    if not es_staff(interaction.user):
        await interaction.response.send_message("🚫 Solo staff.", ephemeral=True)
        return
    
    uid = str(usuario.id)
    if uid not in data["carnets"]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene licencia de conducir.", ephemeral=True)
        return
    
    del data["carnets"][uid]
    save_json("carnets")
    
    await interaction.response.send_message(f"✅ Licencia de conducir eliminada de {usuario.mention}")

    from discord.ui import Button, View
    from discord import ButtonStyle
    import discord
    import asyncio
    from datetime import datetime, timezone

    # ----------------------- 
    # Parte 2 — SISTEMA DE VERIFICACIÓN
    # -----------------------

    import discord
    from discord.ext import commands
    from discord.ui import View, Button

# Configuración (IDs de canales)
# Las constantes ahora están centralizadas en la clase Config
# Embed de solicitud
def embed_solicitud_verificacion(mensaje: discord.Message) -> discord.Embed:
    embed = discord.Embed(
        title="📩 Nueva Solicitud de Verificación",
        description=mensaje.content,
        color=discord.Color.blue()
    )
    embed.set_author(
        name=mensaje.author.display_name,
        icon_url=mensaje.author.avatar.url if mensaje.author.avatar else None
    )
    embed.set_footer(text=f"ID del usuario: {mensaje.author.id}")
    return embed

# Modal para motivo de rechazo
class ModalRechazo(Modal, title="❌ Rechazar Solicitud"):
    motivo = TextInput(
        label="Motivo del rechazo",
        placeholder="Explica por qué se rechaza esta solicitud...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    def __init__(self, usuario: discord.Member):
        super().__init__()
        self.usuario = usuario

    async def on_submit(self, interaction: discord.Interaction):
        canal_solicitudes = interaction.guild.get_channel(config.CANAL_SOLICITUDES)

        # Mensaje público en el canal de solicitudes
        if canal_solicitudes:
            await canal_solicitudes.send(
                f"❌ La solicitud de {self.usuario.mention} fue rechazada.\n**Motivo:** {self.motivo.value}"
            )

        # Mensaje privado al usuario
        try:
            await self.usuario.send(
                f"🚫 Tu solicitud de verificación fue rechazada.\n**Motivo:** {self.motivo.value}"
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Has rechazado la solicitud de {self.usuario.mention} con el motivo:\n**{self.motivo.value}**",
            ephemeral=True
        )

# Vista con botones
class VerificarRechazar(View):
    def __init__(self, usuario: discord.Member):
        super().__init__(timeout=None)
        self.usuario = usuario

    @discord.ui.button(label="✅ Verificar", style=discord.ButtonStyle.green)
    async def verificar(self, interaction: discord.Interaction, button: Button):
        rol = interaction.guild.get_role(config.ROL_VERIFICADO)
        if rol:
            await self.usuario.add_roles(rol, reason="Solicitud de verificación aceptada")
            await interaction.response.send_message(
                f"✅ {self.usuario.mention} ha sido verificado correctamente.",
                ephemeral=False
            )
            try:
                await self.usuario.send(
                    "🎉 ¡Felicidades! Tu solicitud de verificación ha sido aceptada y ya tienes acceso al servidor."
                )
            except discord.Forbidden:
                pass
        else:
            await interaction.response.send_message(
                "⚠️ No se encontró el rol de verificado. Revisa la configuración.",
                ephemeral=True
            )

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: Button):
        # Mostrar modal para escribir el motivo
        await interaction.response.send_modal(ModalRechazo(self.usuario))

# Evento para leer solicitudes
@bot.event
async def on_message(mensaje: discord.Message):
    if mensaje.author.bot:
        return

    if mensaje.channel.id == config.CANAL_VERIFICACIONES:
        canal_solicitudes = bot.get_channel(config.CANAL_SOLICITUDES)
        if canal_solicitudes:
            embed = embed_solicitud_verificacion(mensaje)
            await canal_solicitudes.send(embed=embed, view=VerificarRechazar(mensaje.author))
        await mensaje.delete()  # Borra el mensaje original para mantener limpio

    await bot.process_commands(mensaje)

# =====================
# SISTEMA DE ALERTAS VALENCIA RP  
# =====================
    
@bot.tree.command(name="say", description="Hace que el bot diga algo")
async def say(interaction: discord.Interaction, mensaje: str):
    if interaction.user.id == 1394639946643411048:
        await interaction.response.send_message("Mensaje enviado", ephemeral=True)
        await interaction.channel.send(mensaje)
    else:
        await interaction.response.send_message("No tienes permiso para usar este comando", ephemeral=True)

# ----------------------
# --- COMANDO /ALERTAS CON MENSAJES MUY LARGOS ---
# ----------------------
from discord import app_commands, Interaction, Embed

# Colores por nivel de alerta (1-5)
ALERTA_COLORES = {
    "Nivel 1 - Verde": 0x00FF00,      # Verde
    "Nivel 2 - Amarillo": 0xFFFF00,  # Amarillo
    "Nivel 3 - Naranja": 0xFFA500,   # Naranja
    "Nivel 4 - Rojo": 0xFF0000,      # Rojo
    "Nivel 5 - Negro": 0x000000      # Negro
}

# Mensajes por nivel de alerta
ALERTA_MENSAJES = {
    "Nivel 1 - Verde": (
        "🟢 **NIVEL 1 - ALERTA VERDE**\n\n"
        "📊 **Estado:** Situación normal y controlada\n"
        "🔹 **Acción requerida:** Vigilancia estándar\n"
        "🔹 **Protocolo:** Mantener patrullaje rutinario\n"
        "🔹 **Comunicación:** Reportes normales cada hora\n\n"
        "Todo se encuentra en condiciones normales. Mantener vigilancia estándar."
    ),
    "Nivel 2 - Amarillo": (
        "🟡 **NIVEL 2 - ALERTA AMARILLA**\n\n"
        "⚠️ **Estado:** Riesgo menor detectado\n"
        "🔸 **Acción requerida:** Extremar precauciones\n"
        "🔸 **Protocolo:** Verificar equipos y sistemas\n"
        "🔸 **Comunicación:** Reportes cada 30 minutos\n\n"
        "Se recomienda aumentar la vigilancia y estar preparados."
    ),
    "Nivel 3 - Naranja": (
        "🟠 **NIVEL 3 - ALERTA NARANJA**\n\n"
        "🚨 **Estado:** Amenaza moderada confirmada\n"
        "🔶 **Acción requerida:** Activar protocolos de seguridad\n"
        "🔶 **Protocolo:** Preparación para intervención\n"
        "🔶 **Comunicación:** Reportes cada 15 minutos\n\n"
        "Situación de riesgo que requiere preparación inmediata."
    ),
    "Nivel 4 - Rojo": (
        "🔴 **NIVEL 4 - ALERTA ROJA**\n\n"
        "🚨 **Estado:** Amenaza grave e inminente\n"
        "🔻 **Acción requerida:** Despliegue inmediato\n"
        "🔻 **Protocolo:** Activación de equipos de emergencia\n"
        "🔻 **Comunicación:** Canal abierto permanente\n\n"
        "Peligro inmediato. Todos los equipos deben actuar ahora."
    ),
    "Nivel 5 - Negro": (
        "⚫ **NIVEL 5 - ALERTA NEGRA**\n\n"
        "💀 **Estado:** CRISIS MÁXIMA - EMERGENCIA TOTAL\n"
        "⬛ **Acción requerida:** RESPUESTA INMEDIATA Y TOTAL\n"
        "⬛ **Protocolo:** TODOS LOS RECURSOS DISPONIBLES\n"
        "⬛ **Comunicación:** PRIORIDAD ABSOLUTA\n\n"
        "**SITUACIÓN CRÍTICA EXTREMA. MÁXIMA PRIORIDAD.**"
    )
}

@tree.command(name="alerta", description="🚨 Establecer nivel de alerta de emergencia")
@app_commands.describe(nivel="Selecciona el nivel de alerta (1-5)")
@app_commands.choices(nivel=[
    app_commands.Choice(name="🟢 Nivel 1 - Verde (Normal)", value="Nivel 1 - Verde"),
    app_commands.Choice(name="🟡 Nivel 2 - Amarillo (Precaución)", value="Nivel 2 - Amarillo"),
    app_commands.Choice(name="🟠 Nivel 3 - Naranja (Amenaza)", value="Nivel 3 - Naranja"),
    app_commands.Choice(name="🔴 Nivel 4 - Rojo (Grave)", value="Nivel 4 - Rojo"),
    app_commands.Choice(name="⚫ Nivel 5 - Negro (Crisis)", value="Nivel 5 - Negro")
])
async def alerta(interaction: Interaction, nivel: app_commands.Choice[str]):
    """Sistema de alertas de emergencia de Valencia RP"""
    
    # Verificar permisos (solo staff puede activar alertas)
    if not es_staff(interaction.user):
        embed = crear_embed_error(
            "Sin permisos",
            "Solo el personal autorizado puede activar alertas de emergencia.",
            config.FOOTER_POLICIAL
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Obtener color y mensaje
    color = ALERTA_COLORES.get(nivel.value, 0xFFFFFF)
    mensaje = ALERTA_MENSAJES.get(nivel.value, "Alerta desconocida.")
    
    # Crear embed de alerta
    embed_alerta = discord.Embed(
        title=f"🚨 SISTEMA DE ALERTAS - VALENCIA RP 🚨",
        description=mensaje,
        color=color
    )
    
    # Información adicional
    embed_alerta.add_field(
        name="👮 Staff responsable",
        value=interaction.user.mention,
        inline=True
    )
    embed_alerta.add_field(
        name="📅 Fecha y hora",
        value=f"<t:{int(time.time())}:F>",
        inline=True
    )
    embed_alerta.add_field(
        name="📍 Canal",
        value=interaction.channel.mention,
        inline=True
    )
    
    embed_alerta.set_footer(text=f"{config.FOOTER_POLICIAL} • Activado por {interaction.user.display_name}")
    embed_alerta.timestamp = discord.utils.utcnow()
    
    # Guardar alerta en el sistema
    if "alertas" not in data:
        data["alertas"] = []
    
    nueva_alerta = {
        "nivel": nivel.value,
        "staff_id": str(interaction.user.id),
        "staff_name": interaction.user.display_name,
        "canal_id": str(interaction.channel.id),
        "fecha": datetime.datetime.now().isoformat(),
        "timestamp": int(time.time())
    }
    
    data["alertas"].append(nueva_alerta)
    save_json("alertas")
    
    # Responder con la alerta
    await interaction.response.send_message(embed=embed_alerta)
    
    # Mensaje adicional para niveles críticos (4 y 5)
    if "4" in nivel.value or "5" in nivel.value:
        await interaction.followup.send(
            f"⚠️ **ATENCIÓN GENERAL** ⚠️\n\n"
            f"Se ha activado una **{nivel.value.upper()}**\n"
            f"Todos los equipos deben seguir los protocolos de emergencia.\n\n"
            f"Staff responsable: {interaction.user.mention}",
            ephemeral=False
        )



# ----------------------
# --- FIN: INICIO DEL BOT ---
# ----------------------
if not config.TOKEN:
    print("❌ TOKEN no encontrado en variables de entorno (Secrets).")
    print("Por favor, configura la variable DISCORD_TOKEN en Replit Secrets.")
else:
    print("🚀 Iniciando Spanish City RP Bot...")
    bot.run(config.TOKEN)
