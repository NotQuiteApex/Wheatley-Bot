#!/usr/bin/env python3

from os import getenv
from traceback import format_exception
from asyncio import sleep

from discord import errors, Embed, Color
from discord.ext import commands
from discord.utils import get

import toml


bot = commands.Bot(command_prefix='.')
conf = toml.load("conf.toml")

@bot.event
async def on_ready():
    bot.conf = conf
    
    for guild in bot.guilds:
        # This bot is only meant to manage one server.
        # Do not invite your bot to more than one server.
        bot.guild = guild

        # Friends
        bot.admin_role  = get(guild.roles, name="Admin")
        bot.friend_role = get(guild.roles, name="Friend")
        bot.staff_role  = get(guild.roles, name="Admin")
        bot.owner_role  = get(guild.roles, name="Admin")

        # Color roles
        bot.colors = {}
        colors = conf["roles"]["colors"]
        for color, role in colors.items():
            bot.colors[color.lower()] = get(guild.roles, name=role)

        # Stream roles
        bot.streams = {}
        streams = conf["roles"]["streams"]
        for stream, role in streams.items():
            bot.streams[stream.lower()] = get(guild.roles, name=role)

        # Dev channels
        bot.botdev_channel = get(guild.channels, name="bot-dev")
        bot.botdms_channel = get(guild.channels, name="bot-dm")
        bot.logs_channel   = get(guild.channels, name="bot-logs")


    # Load addons
    addons = [
        "general",
        "colors",
        "moderation",
        "stream",
        "system",
    ]

    # Notify if an addon fails to load.
    fail = None
    for addon in addons:
        try:
            bot.load_extension("cogs." + addon)
            print("{} cog loaded.".format(addon))
        except Exception as e:
            if not fail:
                emb = Embed(
                    title="Startup", description="Failed to load Cog", colour=Color.blue())
            fail += 1
            emb.add_field(name=addon, value="{} : {}".format(
                type(e).__name__, e), inline=True)
            print("Failed to load {} :\n{} : {}".format(
                addon, type(e).__name__, e))
    if fail:
        try:
            logchannel = bot.logs_channel
            await logchannel.send("", embed=emb)
        except errors.Forbidden:
            pass

    bot.all_ready = True

    print("Client logged in as {}, in the following guild : {}"
          "".format(bot.user.name, bot.guild.name))
    await bot.botdev_channel.send("Back online!")


@bot.event
async def on_member_join(member):
    await member.add_roles(bot.friend_role)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.errors.CommandNotFound, commands.errors.CheckFailure)):
        return
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        helpm = await bot.formatter.format_help_for(ctx, ctx.command)
        for m in helpm:
            await ctx.send(m)
    elif isinstance(error, commands.errors.CommandOnCooldown):
        message = await ctx.message.channel.send(
            "{} This command was used {:.2f}s ago and is on "
            "cooldown. Try again in {:.2f}s."
            "".format(ctx.message.author.mention,
                error.cooldown.per - error.retry_after,
                error.retry_after)
            )
        await sleep(10)
        await message.delete()
    else:
        await ctx.send("An error occured while processing the `{}` command."
                       "".format(ctx.command.name))
        print(
            'Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        botdev_msg = "Exception occured in `{0.command}` in {0.message.channel.mention}".format(
            ctx)
        tb = format_exception(type(error), error, error.__traceback__)
        print(''.join(tb))
        botdev_channel = bot.botdev_channel
        await botdev_channel.send(botdev_msg + '\n```' + ''.join(tb) + '\n```')


# Run the bot
if __name__ == "__main__":
    bot.run(conf["discord"]["token"])
