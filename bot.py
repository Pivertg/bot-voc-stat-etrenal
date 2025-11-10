import discord
from discord.ext import commands, tasks
import os

# Configuration depuis les variables d'environnement
GUILD_ID = 1437060358081745062
CHANNEL_MEMBERS = 1437547102610788543
CHANNEL_ONLINE = 1437547143475757209

# Configuration règlement
RULES_MESSAGE_ID = 1437555076049801227
VERIFIED_ROLE_ID = 1437555076049801227

# Intents nécessaires
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.message_content = True

# Créer le bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"📊 Surveillance du serveur ID: {GUILD_ID}")
    
    # Démarrer la mise à jour automatique des stats
    if GUILD_ID and CHANNEL_MEMBERS and CHANNEL_ONLINE:
        update_stats.start()
        print("🔄 Mise à jour automatique des stats démarrée")
    else:
        print("⚠️ Configuration stats incomplète. Utilisez !setup pour créer les channels")
    
    # Vérifier la config règlement
    if RULES_MESSAGE_ID and VERIFIED_ROLE_ID:
        print("📜 Système de règlement actif")
    else:
        print("⚠️ Configuration règlement incomplète")

# ========================================
# 📊 SYSTÈME DE STATISTIQUES
# ========================================

@tasks.loop(minutes=5)
async def update_stats():
    """Met à jour les statistiques du serveur"""
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
        
        channel_members = guild.get_channel(CHANNEL_MEMBERS)
        channel_online = guild.get_channel(CHANNEL_ONLINE)
        
        if not channel_members or not channel_online:
            return
        
        total_members = guild.member_count
        online_members = sum(
            1 for member in guild.members 
            if member.status != discord.Status.offline and not member.bot
        )
        
        try:
            await channel_members.edit(name=f"👥 Membres: {total_members}")
            print(f"✅ Stats Membres: {total_members}")
        except Exception as e:
            print(f"❌ Erreur stats membres: {e}")
        
        try:
            await channel_online.edit(name=f"🟢 En ligne: {online_members}")
            print(f"✅ Stats En ligne: {online_members}")
        except Exception as e:
            print(f"❌ Erreur stats en ligne: {e}")
            
    except Exception as e:
        print(f"❌ Erreur update stats: {e}")

@update_stats.before_loop
async def before_update_stats():
    await bot.wait_until_ready()

@bot.command(name="stats")
@commands.has_permissions(administrator=True)
async def force_update(ctx):
    """Force une mise à jour des stats"""
    await ctx.send("🔄 Mise à jour...")
    await update_stats()
    await ctx.send("✅ Stats mises à jour !")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_channels(ctx):
    """Crée les channels de stats"""
    guild = ctx.guild
    
    category = await guild.create_category("📊 STATISTIQUES")
    
    channel_members = await guild.create_voice_channel(
        name="👥 Membres: ...",
        category=category
    )
    channel_online = await guild.create_voice_channel(
        name="🟢 En ligne: ...",
        category=category
    )
    
    await channel_members.set_permissions(guild.default_role, connect=False)
    await channel_online.set_permissions(guild.default_role, connect=False)
    
    embed = discord.Embed(
        title="✅ Configuration terminée !",
        color=discord.Color.green()
    )
    embed.add_field(
        name="📝 Ajoutez dans .env",
        value=f"```\nGUILD_ID={guild.id}\nCHANNEL_MEMBERS={channel_members.id}\nCHANNEL_ONLINE={channel_online.id}\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)
    
    if not update_stats.is_running():
        update_stats.start()

# ========================================
# 📜 SYSTÈME DE RÈGLEMENT
# ========================================

@bot.event
async def on_raw_reaction_add(payload):
    """Détecte quand quelqu'un réagit à un message"""
    
    # Ignorer les réactions du bot
    if payload.user_id == bot.user.id:
        return
    
    # Vérifier si c'est le message du règlement
    if payload.message_id != RULES_MESSAGE_ID:
        return
    
    # Vérifier si c'est la réaction ✅
    if str(payload.emoji) != "✅":
        return
    
    # Récupérer le serveur et le membre
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member:
        return
    
    # Récupérer le rôle vérifié
    role = guild.get_role(VERIFIED_ROLE_ID)
    if not role:
        print(f"❌ Rôle {VERIFIED_ROLE_ID} introuvable")
        return
    
    # Ajouter le rôle au membre
    try:
        await member.add_roles(role)
        print(f"✅ Rôle '{role.name}' ajouté à {member.name}")
        
        # Envoyer un message de bienvenue en MP (optionnel)
        try:
            embed = discord.Embed(
                title="✅ Bienvenue !",
                description=f"Tu as accepté le règlement de **{guild.name}** !\nTu as maintenant accès à tout le serveur. Amuse-toi bien ! 🎉",
                color=discord.Color.green()
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass  # L'utilisateur a bloqué les MPs
            
    except discord.Forbidden:
        print(f"❌ Permissions insuffisantes pour ajouter le rôle à {member.name}")
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du rôle: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    """Retire le rôle si quelqu'un enlève sa réaction"""
    
    if payload.message_id != RULES_MESSAGE_ID:
        return
    
    if str(payload.emoji) != "✅":
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member:
        return
    
    role = guild.get_role(VERIFIED_ROLE_ID)
    if not role:
        return
    
    try:
        await member.remove_roles(role)
        print(f"⚠️ Rôle '{role.name}' retiré de {member.name}")
    except Exception as e:
        print(f"❌ Erreur retrait rôle: {e}")

# ========================================
# 🚀 DÉMARRAGE
# ========================================

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
