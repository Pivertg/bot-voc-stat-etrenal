import discord
from discord.ext import commands, tasks
import os

# Configuration depuis les variables d'environnement
GUILD_ID = 1437060358081745062
CHANNEL_MEMBERS = 1437547102610788543
CHANNEL_ONLINE = 1437547143475757209

# Intents nécessaires
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True

# Créer le bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"📊 Surveillance du serveur ID: {GUILD_ID}")
    
    # Démarrer la mise à jour automatique
    if GUILD_ID and CHANNEL_MEMBERS and CHANNEL_ONLINE:
        update_stats.start()
        print("🔄 Mise à jour automatique démarrée")
    else:
        print("⚠️ Configuration incomplète. Utilisez !setup pour créer les channels")

@tasks.loop(minutes=5)
async def update_stats():
    """Met à jour les statistiques du serveur"""
    try:
        # Récupérer le serveur
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ Serveur {GUILD_ID} introuvable")
            return
        
        # Récupérer les channels
        channel_members = guild.get_channel(CHANNEL_MEMBERS)
        channel_online = guild.get_channel(CHANNEL_ONLINE)
        
        if not channel_members or not channel_online:
            print("❌ Un ou plusieurs channels introuvables")
            return
        
        # Calculer les statistiques
        total_members = guild.member_count
        
        # Compter les membres en ligne (sans les bots)
        online_members = sum(
            1 for member in guild.members 
            if member.status != discord.Status.offline and not member.bot
        )
        
        # Mettre à jour les noms des channels
        try:
            await channel_members.edit(name=f"👥 Membres: {total_members}")
            print(f"✅ Mis à jour: Membres = {total_members}")
        except discord.Forbidden:
            print("❌ Permissions insuffisantes pour modifier le channel Membres")
        except Exception as e:
            print(f"❌ Erreur channel Membres: {e}")
        
        try:
            await channel_online.edit(name=f"🟢 En ligne: {online_members}")
            print(f"✅ Mis à jour: En ligne = {online_members}")
        except discord.Forbidden:
            print("❌ Permissions insuffisantes pour modifier le channel En ligne")
        except Exception as e:
            print(f"❌ Erreur channel En ligne: {e}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        import traceback
        traceback.print_exc()

@update_stats.before_loop
async def before_update_stats():
    """Attendre que le bot soit prêt"""
    await bot.wait_until_ready()

@bot.command(name="stats")
@commands.has_permissions(administrator=True)
async def force_update(ctx):
    """Force une mise à jour immédiate des statistiques (Admin seulement)"""
    await ctx.send("🔄 Mise à jour des statistiques...")
    await update_stats()
    await ctx.send("✅ Statistiques mises à jour !")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_channels(ctx):
    """Crée automatiquement les channels de statistiques (Admin seulement)"""
    guild = ctx.guild
    
    # Créer une catégorie pour les stats
    category = await guild.create_category("📊 STATISTIQUES")
    
    # Créer les channels vocaux
    channel_members = await guild.create_voice_channel(
        name="👥 Membres: ...",
        category=category
    )
    channel_online = await guild.create_voice_channel(
        name="🟢 En ligne: ...",
        category=category
    )
    
    # Verrouiller les channels (personne ne peut se connecter)
    await channel_members.set_permissions(guild.default_role, connect=False)
    await channel_online.set_permissions(guild.default_role, connect=False)
    
    embed = discord.Embed(
        title="✅ Configuration terminée !",
        description="Les channels de statistiques ont été créés.",
        color=discord.Color.green()
    )
    embed.add_field(name="Channel Membres", value=f"ID: `{channel_members.id}`")
    embed.add_field(name="Channel En ligne", value=f"ID: `{channel_online.id}`")
    embed.add_field(
        name="📝 Configuration",
        value=f"Ajoutez ces lignes à votre `.env`:\n```\nGUILD_ID={guild.id}\nCHANNEL_MEMBERS={channel_members.id}\nCHANNEL_ONLINE={channel_online.id}\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)
    
    # Redémarrer la mise à jour auto si elle n'est pas active
    if not update_stats.is_running():
        print("🔄 Démarrage de la mise à jour automatique...")
        update_stats.start()

async def start_bot(token):
    """Fonction appelée par main.py pour démarrer le bot"""
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n⛔ Arrêt du bot...")
        await bot.close()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise