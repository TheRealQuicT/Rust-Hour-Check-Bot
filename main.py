import discord
import os
import configparser
import asyncio
from requests.models import Response
import simplejson as json
import requests
import datetime
from discord.ext import commands
from requests.structures import CaseInsensitiveDict


# Read configuration file
config = configparser.ConfigParser()
config.read(os.path.abspath(__file__).replace(os.path.basename(__file__), "config.ini"))

# Tokens
DiscordToken = config["Discord"]["discordToken"]
BMkey = config["Battlemetrics"]["BMkey"]
Steamkey = config["Steam"]["Steamkey"]

intents = discord.Intents.default()
intents.members = True
intents.messages = True

# Bots Prefix
client = commands.Bot(intents=intents, status=discord.Status.dnd, activity=discord.Game("With Time!"), command_prefix = "!")

# Removes the basic discord Help command
client.remove_command("help")

# Will show that the Bot is online in console
@client.event
async def on_ready():
    print(f'{client.user} has logged in')

# Error message if there is a unknown command
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(format(ctx.author.mention) + ",That is not a valid command.")

# Help Command
@client.command()
async def help(ctx):
    helpem = discord.Embed(title=f"The Bot Prefix Is !", value="", color = 0x0008ff)
    helpem.add_field(name="`!hours [SteamID]`", value="This will show the hours this user has on Icefuse servers and on Rust in total.")
    helpem.add_field(name="`!clear [amount]`", value="This will clear the amount of messagess that you tell it to clear. If you do not give a amount to clear it will default to 5.")
    helpem.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)
    await ctx.send(embed=helpem)

# Purge command, Default Purge amount is 5 unless given otherwise
@client.command()
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount)

# Hourcheck Command, will check hours played on icefuse servers and total amount of hours played on rust
@client.command()
async def hours(ctx,*,steamID : int):
    serverID = [3260244, 9113699, 5192962, 3657891, 2703938, 3481329, 6841036, 4032701, 6842591, 5192054, 2930255, 2801208, 3665933, 3973236, 3044995, 8939401, 2801795, 3410403]

    # Header to use for API request
    bmheader = CaseInsensitiveDict()
    bmheader["Authorization"] = "Bearer " + BMkey
    bmheader["Content-Type"] = "application/json"

    # Get Player BMid
    def steamidtoBMID():
        bm_id_url = "https://api.battlemetrics.com/players/match"
        data = '{"method" : "post","contentType" : "application/json","headers" : {"Authorizaion": "Bearer %s"}, "data" : [{"type" : "identifier","attributes" : {"type" : "steamID","identifier" :"%s"}}]}' % (BMkey,steamID)
        bm = requests.post(bm_id_url, headers=bmheader, data=data)
        # Players BMid
        
        if json.loads(bm.text)['data'] == []:
            BMid = "Has Not Played on Icefuse Servers."
            return BMid
        else:
            BMid = json.loads(bm.text)['data'][0]['relationships']['player']['data']['id']
            return BMid

    BMid = steamidtoBMID()

    def get_steam_pic():
        steam_pic_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=%s&steamids=%s" % (Steamkey, steamID)
        steam = requests.get(steam_pic_url)
        # Players Steam Picture
        steampic = json.loads(steam.text)['response']['players'][0]['avatarfull']

        return steampic

    steampic = get_steam_pic()

    async def get_hours():
            
        BMtime = []
        if BMid == "Has Not Played on Icefuse Servers.":
            pass
        else:
            # Loop all the servers
            for x in serverID:
                bm_hours_url = "https://api.battlemetrics.com/players/%s/servers/%s" % (BMid,x)
                data = '{"method" : "get","contentType" : "application/json","headers" : {"Authorizaion": "Bearer %s"}' % (BMkey)
                bm = requests.get(bm_hours_url, headers=bmheader, params=data)
                bad = '{"errors":[{"status":"400","title":"Bad Request","detail":"That player has not played on that server."}]}'
                if bm.text == bad:
                    BMtime.append(0)
                elif bm.text != bad:
                    # Players Hours
                    BMseconds = json.loads(bm.text)['data']['attributes']['timePlayed']
                    BMtime.append(BMseconds)

        Rusttime = []
        steam_hours_url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%s&steamid=%s&format=json" % (Steamkey,steamID)
        steam = requests.get(steam_hours_url)
        # Total Hours played on Rust
        if json.loads(steam.text)['response'] == {}:
            Rusttime = ("Private Profile")
        else:
            hours = json.loads(steam.text)['response']['games']
            for totalhours in hours:
                if (totalhours['appid'] == 252490) == True:
                        rust_hours = totalhours['playtime_forever']
                        Rusttime.append(rust_hours)
                elif (totalhours['appid'] == 252490) == False:
                        rust_hours = 0
                        Rusttime.append(rust_hours)

        async def response():
                    BMhours = datetime.timedelta(seconds=sum(BMtime))
                    Rusthours = datetime.timedelta(minutes=sum(Rusttime))
                    # Embed message for HourCheck
                    hourem = discord.Embed(title=f"HourCheck Complete", value="", color = 0x0008ff)
                    if BMhours > datetime.timedelta(hours=20) and Rusthours > datetime.timedelta(hours=30):
                        hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(BMhours) + " ✅"), inline=False)
                        hourem.add_field(name="Total Hours played on Rust:", value=format(str(Rusthours) + " ✅"), inline=False)
                        hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
                        hourem.set_thumbnail(url=steampic)
                        hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
                        await ctx.send(embed=hourem)
                        await clear(steamID)
                    elif BMhours < datetime.timedelta(hours=20) and Rusthours > datetime.timedelta(hours=30):
                        hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(BMhours) + " ❌"), inline=False)
                        hourem.add_field(name="Total Hours played on Rust:", value=format(str(Rusthours) + " ✅"), inline=False)
                        hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
                        hourem.set_thumbnail(url=steampic)
                        hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
                        await ctx.send(embed=hourem)
                        await clear(steamID)
                    elif BMhours > datetime.timedelta(hours=20) and Rusthours < datetime.timedelta(hours=30):
                        hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(BMhours) + " ✅"), inline=False)
                        hourem.add_field(name="Total Hours played on Rust:", value=format(str(Rusthours) + " ❌"), inline=False)
                        hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
                        hourem.set_thumbnail(url=steampic)
                        hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
                        await ctx.send(embed=hourem)
                        await clear(steamID)    
                    elif BMhours < datetime.timedelta(hours=20) and Rusthours < datetime.timedelta(hours=30):
                        hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(BMhours) + " ❌"), inline=False)
                        hourem.add_field(name="Total Hours played on Rust:", value=format(str(Rusthours) + " ❌"), inline=False)
                        hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
                        hourem.set_thumbnail(url=steampic)
                        hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
                        await ctx.send(embed=hourem)
                        await clear(steamID)

        # Embed message for HourCheck
        hourem = discord.Embed(title=f"HourCheck Complete", value="", color = 0x0008ff)
        
        # If the player hasnt played on Icefuse
        if BMid == "Has Not Played on Icefuse Servers." and datetime.timedelta(minutes=sum(Rusttime)) > datetime.timedelta(hours=30):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=BMid + " ❌", inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value=format(str(datetime.timedelta(minutes=sum(Rusttime))) + " ✅"), inline=False)
            hourem.add_field(name="Player BM Profile:", value="Does not have a BM link.", inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)
        elif BMid == "Has Not Played on Icefuse Servers." and datetime.timedelta(minutes=sum(Rusttime)) < datetime.timedelta(hours=30):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=BMid + " ❌", inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value=format(str(datetime.timedelta(minutes=sum(Rusttime))) + " ❌"), inline=False)
            hourem.add_field(name="Player BM Profile:", value="Does not have a BM link.", inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)    
        # If the Player hasnt played on rust
        elif Rusttime == "Private Profile" and datetime.timedelta(seconds=sum(BMtime)) > datetime.timedelta(hours=20):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(datetime.timedelta(seconds=sum(BMtime))) + " ✅"), inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value=Rusttime + " ❌", inline=False)
            hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)
        elif Rusttime == "Private Profile" and datetime.timedelta(seconds=sum(BMtime)) < datetime.timedelta(hours=20):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(datetime.timedelta(seconds=sum(BMtime))) + " ❌"), inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value=Rusttime + " ❌", inline=False)
            hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)
        elif datetime.timedelta(minutes=sum(Rusttime)) == datetime.timedelta(seconds=0) and datetime.timedelta(seconds=sum(BMtime)) > datetime.timedelta(hours=20):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(datetime.timedelta(seconds=sum(BMtime))) + " ✅"), inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value="Private Profile ❌", inline=False)
            hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)
        elif datetime.timedelta(minutes=sum(Rusttime)) == datetime.timedelta(seconds=0) and datetime.timedelta(seconds=sum(BMtime)) < datetime.timedelta(hours=20):
            hourem.add_field(name="Total Hours Played on Icefuse Servers:", value=format(str(datetime.timedelta(seconds=sum(BMtime))) + " ❌"), inline=False)
            hourem.add_field(name="Total Hours played on Rust:", value="Private Profile ❌", inline=False)
            hourem.add_field(name="Player BM Profile:", value="https://www.battlemetrics.com/rcon/players/" + BMid, inline=False)
            hourem.set_thumbnail(url=steampic)
            hourem.set_footer(text=f'Latency: {round(client.latency * 1000)}ms')
            await ctx.send(embed=hourem)
            await clear(steamID)
        else:
            await response()
     
    async def main():
        BM = asyncio.create_task(get_hours())
        await BM
        spic = asyncio.create_task(get_steam_pic())
        await spic
    await main()
      
# Clear Error message
@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.CommandError):
        await ctx.send(format(ctx.author.mention) + ", That is not a valid amount.")

client.run(DiscordToken)