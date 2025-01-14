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
    await ctx.reply(f"<@{user_id}>'s balance is: **{balance}**")

@bot.command()
async def send(ctx, member: discord.Member, amount: int):
    """Send other users GlumboCoin! E.g .send @<USER> 100""" 
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
        await ctx.reply(f"Sent {amount} GlumboCoins to <@{recip_id}>!")

    else:
        await ctx.reply("Insufficient GlumboCoins!")

@bot.command()
async def websurf(ctx):
    """Surf the web to earn GlumboCoin! E.g .websurf""" 
    user_id = ctx.message.author.id
    await acc_check(user_id)

    curr_time = int(time.time())

    cur.execute("SELECT time_of_last_tx FROM users WHERE user_id = ?;", (user_id,))
    last_time = cur.fetchone()[0]

    rand_int = random.randint(20, 100)

    if (curr_time - last_time) >= 1800:
        await ctx.reply("Surfing the web for GlumboCoins! \n https://tenor.com/view/surf-internet-gif-11385820")
        cur.execute("UPDATE users SET time_of_last_tx = ? WHERE user_id = ?;", (curr_time, user_id))

        msg = await ctx.send("# .")
        for i in range(1, 6):
            await asyncio.sleep(1)
            await msg.edit(content= "# " + ("." * i))
        await ctx.reply(f"Surfed the web and found **{rand_int}** GlumboCoins!")
        cur.execute("UPDATE users SET balance = balance + ?, time_of_last_tx = ? WHERE user_id = ?;", (rand_int, curr_time, user_id))
        con.commit()
    else:
        await ctx.reply(f"Please wait another {1800 - (curr_time - last_time)} seconds!")

token = os.getenv("DISCORD_TOKEN")
bot.run(token)
