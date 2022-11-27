import asyncio
import datetime
import time

import requests
import discord
import nest_asyncio

nest_asyncio.apply()
from dotenv import load_dotenv

load_dotenv()
import os

# environment variables with your details.
# create a .env file and add your details in key=value format
# Script won't work without these details.
token = os.environ['DISCORD_TOKEN_0']
alphabotCookie = os.environ['ALPHABOT_COOKIE_0']
walletAddress = os.environ['WALLET_0']

# It only works for time period of little over a month from the start date.
# So if you want to remove junk servers from october use start day like 1st october
startday = 22
startmonth = 10
startyear = 2022

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# guilds that you don't wanna leave no matter what. Add those guild IDs here
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
def checkIfNoWinnings(searchStr):
    try:
        wins = "&filter=winners"
        pending = "&filter=pending"
        lost = "&filter=lost"
        url = f"https://www.alphabot.app/api/projects?sort=startDate&scope=community&sortDir=-1&showHidden=true&pageSize=16&pageNum=0&search={searchStr}{wins}{pending}{lost}"

        cookies = {
            "__Secure-next-auth.session-token": globals()["alphabotCookie"]
        }
        response = requests.get(url, cookies=cookies)
        data = response.json()

        if (len(data)):
            isWinnerOrPending = False
            isLost = False
            for entry in data:
                print(f"    entry name:{entry['name']}")
                if searchStr not in entry["name"].lower() and searchStr.replace(" ","") not in entry["name"].lower():
                    print(f"    entry name doesn't match guild name")
                    continue
                elif entry["isWinner"] or entry["isPending"]:
                    print("    is winner or pending")
                    isWinnerOrPending = True
                    break
                elif entry["isLost"]:
                    print("    is lost")
                    isLost = True
                    continue

            if not isWinnerOrPending and isLost:
                return True
            elif isWinnerOrPending:
                return False
            else:
                return False

        else:
            return False
    except Exception as e:
        print(e)

# fetches ab calender data
def getAlphaBotCalenderData():
    try:
        startdate = time.mktime(datetime.datetime(startyear,startmonth,startday).timetuple())*1000
        enddate = time.time() * 1000
        print(startdate,enddate)
        # url = "https://www.alphabot.app/api/projectData?calendar=true&startDate=1666722600000&endDate=1670351400000&selectedMonth=11&a=0xc5c11ec3ca8e38fb6af06beb25b9ea76b5b1e0f9"
        url = f"https://www.alphabot.app/api/projectData?startDate={startdate}&endDate={enddate}&selectedMonth=10&a={walletAddress}"
        cookies = {
            "__Secure-next-auth.session-token": globals()["alphabotCookie"]
        }
        response = requests.get(url,cookies=cookies)
        data = response.json()

        def filterFun(el):
            if el["isWinner"]:
                return True
            else:
                return False

        def mapFun(el):
            return {
                "projectName": el["name"],
                "isWinner": el["isWinner"],
                "mintDate": el["mintDate"]
            }

        filtered = filter(filterFun,data["data"])
        filtered2 = map(mapFun, filtered)

        result = []
        for x in filtered2:
            result.append(x)

        print(result)
        return result
    except Exception as e:
        print(e)


# searches for the given guild in data
def findInData(data, str):
    for i in range(len(data)):
        if str.replace(" ","").lower() in data[i]["projectName"].replace(" ","").lower():
            return i

# checks if already minted out by comparing current time and mint time fetched from ab calender
def checkIfAlreadyMintedOut(data,str):
    projectIndex = findInData(data,str)

    if not projectIndex:
        return False
    elif time.time()*1000 > data[projectIndex]["mintDate"]:
        print(data[projectIndex])
        mintOutDate = datetime.datetime.fromtimestamp(data[projectIndex]["mintDate"]/1000).strftime("%d/%m")
        print(f"    {data[projectIndex]['projectName']} already minted out on {mintOutDate}")
        return True
    else:
        return False

# check only once.
firstLoop = True

@client.event
async def on_ready():
    guildsToLeave = []
    global firstLoop
    if firstLoop:
        collectionData = getAlphaBotCalenderData()
        for guild in client.guilds:
            if guild.id not in whitelist:
                print(f"Checking any winnings/pendings for {guild.name}")
                toRemove = "sold out" in guild.name.lower() or checkIfNoWinnings(guild.name.lower()) or checkIfAlreadyMintedOut(collectionData,guild.name.lower())
                print(toRemove)
                if toRemove == True:
                    guildsToLeave.append(guild)
                    await guild.leave()
                    print(f"Left {guild.name} server")
        print(f"Found {len(guildsToLeave)} servers which can be removed")
        if len(guildsToLeave):
            print(f"guilds removed by bot:")
            for x in guildsToLeave:
                print("    ",x.name)
            print("Successfully removed junk servers")
        print("You can close the script now")
    firstLoop = False


client.run(token, bot=False)
