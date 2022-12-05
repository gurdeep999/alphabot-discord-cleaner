# import asyncio
import datetime
import time
from calendar import monthrange

import requests
import discord
import nest_asyncio
from dotenv import load_dotenv
import os

nest_asyncio.apply()

load_dotenv()

# environment variables with your details.
# create a .env file and add your details in key=value format
# Script won't work without these details.
token = os.environ['DISCORD_TOKEN_2']
alphabotCookie = os.environ['ALPHABOT_COOKIE_2']
walletAddress = os.environ['WALLET_2']

# It only works for time period of little over a month from the start date.
# So if you want to remove junk servers from october use start day like 1st october
startday = 1
startmonth = 9
startyear = 2022

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# guilds that you don't want to leave no matter what. Add those guild IDs here
whitelist = [
    # Ex.
    # alpha
    "897718057596747816", "908478124847665183", "972246861555580979", "907692441061175306",
    "1006070289458806844", "951857903877386280", "964611727859793920", "938840599975563334",
    # whitelists
    "995239463271813151", "956264991042965635", "952600647604244551", "931872261886062602",
    # airdrops server
    "972246861555580979",
]


# checks if the user won at least one giveaway of the given guild name
# returns False if yes and True if user didn't win
def check_if_no_winnings(search_str):
    try:
        wins = "&filter=winners"
        pending = "&filter=pending"
        lost = "&filter=lost"
        url = f"https://www.alphabot.app/api/projects?sort=startDate&scope=community&sortDir=-1&showHidden=true&pageSize=16&pageNum=0&search={search_str}{wins}{pending}{lost}"

        cookies = {
            "__Secure-next-auth.session-token": globals()["alphabotCookie"]
        }
        response = requests.get(url, cookies=cookies)
        data = response.json()

        if len(data):
            is_winner_or_pending = False
            is_lost = False
            for entry in data:
                print(f"    entry name:{entry['name']}")
                # print(entry)
                if search_str not in entry["name"].lower() and search_str.replace(" ", "") not in entry["name"].lower():
                    print(f"    entry name doesn't match guild name")
                    continue
                elif entry["isWinner"] or entry["isPending"]:
                    print("    is winner or pending")
                    is_winner_or_pending = True
                    break
                elif entry["isLost"]:
                    print("    is lost")
                    is_lost = True
                    continue
            print(f"isLost:{is_lost},isWinnerOrPending:{is_winner_or_pending}")
            if not is_winner_or_pending and is_lost:
                # print("inside is lost")
                return True
            elif is_winner_or_pending:
                # print("in is w/p")
                return False
            else:
                return False

        else:
            return False
    except Exception as e:
        print(e)


# now_time = datetime.datetime.now().strftime("%m %Y").split(" ")
# while startmonth <= int(now_time[0]) or startyear <= int(now_time[1]):
#     print(startmonth)
#     startmonth+=1
#     if startmonth == 12:
#         startyear+=1
#         startmonth = 1
#     print(startmonth,startyear)
# while time.mktime(datetime.datetime(startyear, startmonth, startday).timetuple()) < time.time():
#     print(startmonth,startyear)
#
#     if startmonth == 12:
#         startyear+=1
#         startmonth=1
#     else:
#         startmonth+=1

# fetches ab calender data
def getAlphaBotCalenderData():
    global startyear, startmonth, startday
    result = []
    while time.mktime(datetime.datetime(startyear, startmonth, startday).timetuple()) < time.time():
        print(startmonth, startyear)
        startdate = time.mktime(datetime.datetime(startyear, startmonth, startday).timetuple()) * 1000
        enddate = time.mktime(datetime.datetime(startyear, startmonth, monthrange(startyear, startmonth)[
            1]).timetuple()) * 1000  # last day of the month selected as end date.

        result += get_given_month_data(startdate, enddate)
        if startmonth == 12:
            startyear += 1
            startmonth = 1
        else:
            startmonth += 1
    print("inside gab ", result)
    return result


def get_given_month_data(startdate, enddate):
    try:
        url = f"https://www.alphabot.app/api/projectData?startDate={startdate}&endDate={enddate}&a={walletAddress}"
        cookies = {
            "__Secure-next-auth.session-token": globals()["alphabotCookie"]
        }
        response = requests.get(url, cookies=cookies)
        data = response.json()

        # def filterFun(el):
        #     if el["isWinner"]:
        #         return True
        #     else:
        #         return False

        def mapFun(el):
            return {
                "projectName": el["name"],
                "isWinner": el["isWinner"],
                "mintDate": el["mintDate"],
                "discordUrl": el["discordUrl"]
            }

        # filtered = filter(filterFun, data["data"])
        # filtered2 = map(mapFun, filtered)

        filtered2 = map(mapFun, data["data"])

        result = []
        for x in filtered2:
            result.append(x)

        print(result)
        return result
    except Exception as e:
        print(e)


# searches for the given guild in data
def findInData(data, name):
    for i in range(len(data)):
        if name.replace(" ", "").lower() in data[i]["projectName"].replace(" ", "").lower():
            return i


# checks if already minted out by comparing current time and mint time fetched from ab calendar
def check_if_already_minted_out(data, name):
    project_index = findInData(data, name)

    if not project_index:
        return False
    elif time.time() * 1000 > data[project_index]["mintDate"]:
        print(data[project_index])
        mint_out_date = datetime.datetime.fromtimestamp(data[project_index]["mintDate"] / 1000).strftime("%d/%m")
        print(f"    {data[project_index]['projectName']} already minted out on {mint_out_date}")
        return True
    else:
        return False


# check only once.
firstLoop = True


@client.event
async def on_ready():
    # try :
    #     invite = await client.fetch_invite("https://discord.gg/WRKTBAX65u")
    #     print(invite.guild.id)
    # except Exception as e:
    #     print(e)
    guilds_to_leave = []
    global firstLoop
    if firstLoop:
        collection_data = getAlphaBotCalenderData()
        print(collection_data)
        for data in collection_data:
            print(data)
            try:
                if data["discordUrl"] != "":
                    invite = await client.fetch_invite(data["discordUrl"])
                    data["guildId"] = invite.guild.id
            except Exception as e:
                print(e)
        print(collection_data)
        if not collection_data:
            print(
                "Your alphabot session token seems expired. Please replace the token with a fresh one and try again. Or you never used alphabot so your seeing this error.")
            return
        for guild in client.guilds:
            if guild.id not in whitelist:
                print(f"Checking any winnings/pendings for {guild.name}")
                to_remove = "sold out" in guild.name.lower() or check_if_no_winnings(
                    guild.name.lower()) or check_if_already_minted_out(collection_data, guild.name.lower())
                print(f"toRemove:{to_remove}")
                if to_remove:
                    guilds_to_leave.append(guild)
                    await guild.leave()
                    print(f"Left {guild.name} server")
        print(f"Found {len(guilds_to_leave)} servers which can be removed")
        if len(guilds_to_leave):
            print(f"guilds removed by bot:")
            for x in guilds_to_leave:
                print("    ", x.name)
            print("Successfully removed junk servers")
        print("You can close the script now")
    firstLoop = False


client.run(token, bot=False)
