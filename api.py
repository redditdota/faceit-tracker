import json
import requests
import time
import pickle
import multiprocessing

from leagues import *
from tokens import *

MAX_TRIES = 10

def _get(url):
    n = 0
    while n < MAX_TRIES:
        try:
            response = requests.get(url)
            if response.status_code == requests.codes.ok:
                return response.json()
            elif response.status_code == requests.codes.not_found:
                return None
            else:
                print("[bot]", url, response.text)
        except requests.exceptions.RequestException as e:
            print("[bot] ", url, e)
        except json.decoder.JSONDecodeError as e:
            print("[bot] ", url, e)
        time.sleep(10)
        n += 1

    return None


def player_info(nickname):
    uri = "https://api.faceit.com/core/v1/nicknames/%s" % nickname
    result = _get(uri)
    if result is None or "result" not in result or "payload" not in result:
        return None
    return result["payload"]


def get_twitch(steam_id):
    uri = "https://api.twitch.tv/api/steam/%s?client_id=%s" % (steam_id, TWITCH_CLIENT_ID)
    result = _get(uri)
    if result is None or "error" in result:
        return None
    print(result)
    return "https://www.twitch.tv/%s" % result["name"]


def is_live(twitch_name):
    uri = "https://api.twitch.tv/kraken/streams/%s?client_id=%s" % (twitch_name, TWITCH_CLIENT_ID)
    result = _get(uri)
    if result is None or "stream" not in result:
        return False
    else:
        if result["stream"] is None:
            return False
        else:
            return True


def get_members(league_id):
    uri = "https://api.faceit.com/hubs/v1/hub/%s/membership/" % league_id
    n = 0
    ret = {}
    while True:
        result = _get(uri + "?limit=100&offset=%s" % (n * 100))
        if result is None or "payload" not in result:
            continue

        payload = result["payload"]
        items = payload["items"]
        if len(items) == 0:
            break

        for item in items:
            user = item["user"]
            info = player_info(user["nickname"])
            steam_id = info["dota2_id"]
            steam_id = steam_id.split(":")[-1][:-1]

            ret[steam_id] = (user["nickname"], get_twitch(info["steam_id_64"]))

        n += 1

    return ret


def get_faceit_matches():
    uri = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/?key=%s" % (STEAM_KEY)
    result = _get(uri)
    if result is None or "result" not in result:
        return []

    ret = []
    for game in result["result"]["games"]:
        if int(game["league_id"]) in LEAGUE_IDS:
            ret.append(game)

    return ret


def get_server_steam_id(lobby_id):
    uri = "http://pub.prod.faceit.paral.in/activeMatches/all"
    result = _get(uri)
    if result is None or len(result) == 0:
        return (None, None)

    for match in result:
        if "State" not in match:
            continue
        state = match['State']
        if "LobbyId" in state and int(state["LobbyId"]) == int(lobby_id):
            return (match["Config"]["name"], state["ServerSteamID"])

    return (None, None)

def get_leaderboards(league_id):
    uri = "http://api.faceit.com/leaderboard/v1/ranking/hub/%s?leaderboardType=hub_season&limit=5&offset=0&season=1" % league_id
    result = _get(uri)
    ret = []
    if result is None or "payload" not in result:
        return ret

    rankings = result["payload"]["rankings"]
    for player in rankings:
        ret.append((player["placement"]["entity_name"], player["played"], player["won"], player["lost"], player["points"]))

    return ret

"""
for league in LEAGUES:
    members = str(get_members(LEAGUES[league]))
    with open("%s.out" % league, 'w') as f:
        f.write(members)

    with open("%s.pkl" % league, 'wb') as f:
        pickle.dump(members, f)
"""
