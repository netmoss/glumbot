import os
from dotenv import load_dotenv
import sqlite3
import time
import random

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

load_dotenv()

description = '''Send and recieve GlumboCoin!'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', description=description, intents=intents)

con = sqlite3.connect("glumbocorp.db")
cur = con.cursor()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print("Connected to GlumboCorp database")
    print('------')

async def log_transaction(user_id_1:int, user_id_2:int, amount:int):
    timestamp = int(time.time())
    transaction_id = f"{user_id_1 + user_id_2 + timestamp}"
    cur.execute("INSERT INTO transactions (transaction_id, user_id_1, user_id_2, amount, timestamp) VALUES (?, ?, ?, ?, ?);", (transaction_id, user_id_1, user_id_2, amount, timestamp))
    con.commit()

async def acc_check(user_id: int):
    timestamp = int(time.time()) - 1800
    cur.execute("SELECT exists(SELECT 1 FROM users WHERE user_id = ?) AS row_exists;", (user_id,))
    exists = cur.fetchone()[0]
    if exists == 1:
        return
    else:
        cur.execute("INSERT INTO users (user_id, total_transactions,balance, time_of_last_tx) VALUES (?, 0, 0, ?);", (user_id, timestamp))
        con.commit()

@bot.command()
async def bal(ctx, member: discord.Member = None):
    """Check a balance! E.g .bal or .bal @<USER>""" 
    if member is None:
        member = ctx.author

    user_id = member.id
    await acc_check(user_id)

    cur.execute("SELECT balance FROM users WHERE user_id = ?;", (user_id,))
    balance = cur.fetchone()[0]
    await ctx.reply(f"<@{user_id}>'s balance is: **{balance} GlumboCoin**")

@bot.command()
async def baltop(ctx):
    """Find the rich and eat them! E.g .baltop""" 
    user_id = ctx.message.author.id
    await acc_check(user_id)

    cur.execute("SELECT * FROM users ORDER BY balance DESC LIMIT 10;")
    top_users = cur.fetchall()

    embed = discord.Embed(title="The GlumboCorp One Percent ", color=0x800080)
    for idx, user in enumerate(top_users, start=1):
        user_name = await bot.fetch_user(user[0])
        embed.add_field(name=f"{idx}. {user_name}", value=f"**{user[2]} GlumboCoin**", inline=False)

    await ctx.reply(embed=embed)

@bot.command()
async def send(ctx, member: discord.Member, amount: int):
    """Send other users GlumboCoin! E.g .send @<USER> 100""" 
    if amount < 0:
        await ctx.reply("https://media1.tenor.com/m/mGEW9U82igcAAAAd/gus-fring-gustavo.gif")
        return

    user_id = ctx.message.author.id
    await acc_check(user_id)

    recip_id = member.id
    await acc_check(recip_id)

    cur.execute("SELECT balance FROM users WHERE user_id = ?;", (user_id,))
    balance = cur.fetchone()[0]

    if balance >= amount:
        cur.execute("UPDATE users SET balance = balance - ?, total_transactions = total_transactions + 1 WHERE user_id = ?;", (amount, user_id))
        cur.execute("UPDATE users SET balance = balance + ?, total_transactions = total_transactions + 1 WHERE user_id = ?;", (amount, recip_id))
        con.commit()
        await log_transaction(user_id, recip_id, amount)
        await ctx.reply(f"Sent **{amount} GlumboCoin** to <@{recip_id}>!")

    else:
        await ctx.reply("Insufficient GlumboCoin!")

@bot.command()
async def eat(ctx, amount: int):
    """Eat your GlumboCoin! E.g .eat 10""" 

    if amount < 0:
        await ctx.reply("https://media1.tenor.com/m/mGEW9U82igcAAAAd/gus-fring-gustavo.gif")
        return

    user_id = ctx.message.author.id
    await acc_check(user_id)

    cur.execute("SELECT balance FROM users WHERE user_id = ?;", (user_id,))
    balance = cur.fetchone()[0]

    if balance >= amount:
        cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?;", (amount, user_id))
        con.commit()
        if amount < 1000:
            await ctx.reply(f"Ate **{amount} GlumboCoin!** \n (っ´ཀ`)っ \n ")
        else:
            await ctx.reply(f"Urgghh... ate **{amount} GlumboCoin**... :nauseated_face: \n https://i.imgur.com/I8JmRzN.gif")

    else:
        await ctx.reply("You don't have that many GlumboCoin!")


user_locks = {}
@bot.command()
async def websurf(ctx):
    """Surf the web to earn GlumboCoin! E.g .websurf""" 
    user_id = ctx.message.author.id
    await acc_check(user_id)

    if user_id in user_locks and user_locks[user_id]:
        await ctx.reply("You're already surfing the web! Please wait for the current process to finish.")
        return

    user_locks[user_id] = True

    curr_time = int(time.time())

    cur.execute("SELECT time_of_last_tx FROM users WHERE user_id = ?;", (user_id,))
    last_time = cur.fetchone()[0]

    rand_int = random.randint(10, 50)

    if (curr_time - last_time) >= 1800:
        embed = discord.Embed(
            title="Surfing the web for GlumboCoins...",
            color=discord.Color.purple()
        )
        embed.set_image(url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzFzdmQ5YXl6ZjJiMXNvOGx4ZXE5amxzeHBqbmxpdnI3dmI0ajE1NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/QWkuGmMgphvmE/giphy.gif")

        msg = await ctx.send(embed=embed)

        await asyncio.sleep(7)

        embed.description = f"Surfed the web and found **{rand_int} GlumboCoins!**"

        embed.set_image(url=None)
        await msg.edit(embed=embed)

        cur.execute("UPDATE users SET balance = balance + ?, time_of_last_tx = ? WHERE user_id = ?;", (rand_int, curr_time, user_id))
        con.commit()

    else:
        await ctx.reply(f"Please wait another {1800 - (curr_time - last_time)} seconds!")


    user_locks[user_id] = False
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
