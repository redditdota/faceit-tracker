import praw
import sys
import traceback
from api import *
from EU import *
from NA import *
from casters import *
from template import *
from heroes import *

def setup_connection_reddit(code):
    """ Creates a c/#onnection to the reddit API. """
    print("[bot] Setting up connection with reddit")
    password = PASSWORD
    if len(code) > 0:
        password = "%s:%s" % (PASSWORD, code)
    reddit_api = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=USERNAME,
        password=password,
        user_agent="FPL Update Bot".format(SUBREDDIT)
    )
    subreddit = reddit_api.subreddit(SUBREDDIT)
    return (reddit_api, subreddit)

def is_notable(game):
    if "players" not in game:
        return False

    players = game["players"]
    num_notable = 0
    for p in players:
        aid = int(p["account_id"])
        if aid in EU.keys() or aid in NA.keys():
            num_notable += 1

    if num_notable > 5:
        return True
    else:
        return False

def format_match(m):
    dire = []
    radiant = []
    streams = []
    for p in m["players"]:
        if p["team"] != 0 and p["team"] != 1 and p["team"] != 2:
            continue

        aid = int(p["account_id"])
        player_info = EU.get(aid, NA.get(aid))
        if player_info is None:
            print(p)
            continue
            
        player_name = "%s (%s)" % (p['name'], player_info[0])
        if player_info is None:
            print("Unknown player: " + str(p))
            continue

        hero = HEROES[int(p["hero_id"])]
        if player_info[1] is not None and is_live(player_info[1]):
            stream_link = player_info[1]
            streams.append(stream_link)
            if p["team"] == 0:
                radiant.append(("[%s](https://twitch.tv/%s)" %(player_name, stream_link), hero))
            elif p["team"] == 1:
                dire.append(("[%s](https://twitch.tv/%s)" %(player_name, stream_link), hero))
            else:
                continue
        else:
            if p["team"] == 0:
                radiant.append((player_name, hero))
            elif p["team"] == 1:
                dire.append((player_name, hero))
            else:
                continue


    ret = LIVE % (radiant[0][1], radiant[0][0], dire[0][0], dire[0][1],
                  radiant[1][1], radiant[1][0], dire[1][0], dire[1][1], 
                  radiant[2][1], radiant[2][0], dire[2][0], dire[2][1],  
                  radiant[3][1], radiant[3][0], dire[3][0], dire[3][1],  
                  radiant[4][1], radiant[4][0], dire[4][0], dire[4][1])
    return (ret, streams)

def format_leaderboards(leagues):
    NA = get_leaderboards(leagues["NA"])
    EU = get_leaderboards(leagues["EU"])
    tuples = tuple(NA[0]) + tuple(EU[0]) + \
             tuple(NA[1]) + tuple(EU[1]) + \
             tuple(NA[2]) + tuple(EU[2]) + \
             tuple(NA[3]) + tuple(EU[3]) + \
             tuple(NA[4]) + tuple(EU[4])
    return LEADERBOARDS % tuples

def main():
    assert(len(sys.argv) == 2)
    code = input('Enter 2FA Code: ')
    (reddit_api, subreddit) = setup_connection_reddit(code)
    post = reddit_api.submission(id=sys.argv[1])

    while (True):
        try:
            print("[bot] updating...")

            text = "# FaceIT Pro League\n"
            text += "Invite-only inhouse league for professional and high MMR players. \n\n"
            text += "Ten players queue for a game. Two players are chosen as captain, who then pick the remaining players in the 1-2-2-2-1 picking order.\n\n"
            text += "Games are played in captain's mode and points are rewarded based on wins, losses, and streaks.\n\n"
            text += "Leaderboards, ongoing matches, and streams for the NA and EU regions are listed below.\n"

            text += "\n---\n"
            text += "# Leaderboards\n"
            text += format_leaderboards(LEAGUES) + "\n\n"

            text += "* [Full EU Leaderboards](https://www.faceit.com/en/hub/5aa025ad-729c-48b4-8fe3-0145384547ba/FPL%20Europe/leaderboard?season=1) \n"
            text += "* [Full NA Leaderboards](https://www.faceit.com/en/hub/e6329339-66d1-428a-a281-132c194c1bef/FPL%20North%20America/leaderboard?season=1) \n"
            text += "\n---\n"

            matches = get_faceit_matches()
            filtered_matches = [m for m in matches if is_notable(m)]
            if len(filtered_matches) == 0:
                text += "## No Live Matches Currently...\n"
                text += "---"

            for m in filtered_matches:
                (name, server_steam_id) = get_server_steam_id(m["lobby_id"])
                if name is None:
                    name = "Team Radiant vs Team Dire"

                text += "#" + name.replace("team_", "Team ").title().replace("Vs", "vs.") + "\n"

                (players, streams) = format_match(m)
                
                text += players

                if len(streams) > 0:
                    text += "\n**Livestreams:**\n\n"
                    for stream in streams:
                        text += "* [%s](https://twitch.tv/%s)\n" % (stream, stream)

                if server_steam_id is not None:
                    text += "\n**Dotatv Command:**\n\n"
                    text += '`watch_server "%s"`\n\n' % server_steam_id

                text += "\n---\n"

            post.edit(text)
            print("[bot] done...")

            if len(filtered_matches) == 0:
            	time.sleep(60)
            else:
            	time.sleep(5 * 60)
        except Exception as e:
            print("[bot] ERROR: " + str(e))
            traceback.print_exc()

if __name__ == '__main__':
    main()



