from dictdiffer import diff
import re


def get_roster_actions(**kwargs):
    return {
        "change": {f"{kwargs['team']}.players.{kwargs['player']}.position":
                   "'''{}''' de {} cambió su posición de '''{}''' a '''{}'''".format(
                       kwargs["player"], kwargs["team"],
                       kwargs["diff"]["action_details"][0],
                       kwargs["diff"]["action_details"][1]),
                   f"{kwargs['team']}.players.{kwargs['player']}.order": "'''{}''' cambió su orden en {} de '''{}''' a "
                                                                         "'''{}'''"
                   .format(kwargs['player'], kwargs['team'], kwargs["diff"]["action_details"][0],
                           kwargs["diff"]["action_details"][1])},
        "add": {f"{kwargs['team']}.players": "'''{}''' se unió a '''{}'''".format(kwargs["diff"]["action_details"][0],
                                                                                  kwargs["diff"]["team"]),
                "": "'''{}''' fue añadido!".format(kwargs["diff"]["action_details"][0])},
        "remove": {f"{kwargs['team']}.players": "'''{}''' dejó '''{}'''".format(kwargs["diff"]["action_details"][0],
                                                                                kwargs["diff"]["team"]),
                   "": "'''{}''' fue eliminado!".format(kwargs["diff"]["action_details"][0])}
    }


def get_diff_args(action_key):
    team = re.search(r'(.*?)\.players', action_key)
    team = team[1] if team else None
    player = re.search(r'players\.(.*?)\.', action_key)
    player = player[1] if player else None
    return {"team": team or "", "player": player or ""}


def process_diff_make_output(difference):
    output = ""
    results = {}
    for change in difference:
        processed_change = [change[0], change[1], change[2]]
        if type(change[2]) != list:
            processed_change[2] = [processed_change[2]]
        for item in processed_change[2]:
            processed_diff = {"action_type": processed_change[0], "action_key": processed_change[1],
                              "action_details": item}
            args = get_diff_args(processed_diff["action_key"])
            processed_diff["team"] = args["team"]
            processed_diff["player"] = args["player"]
            phrases = get_roster_actions(team=processed_diff["team"],
                                         player=processed_diff["player"],
                                         diff=processed_diff).get(processed_diff["action_type"])
            phrase = phrases.get(processed_diff["action_key"])
            if not phrase:
                phrase = (str(change))
            try:
                team = processed_diff["team"] or processed_diff["action_details"][0]
                if team not in results.keys():
                    results[team] = []
                results[team].append(f"{phrase}\n\n")
            except:
                output += f"{phrase}\n\n"
    for team, team_changes in results.items():
        output += f"== {team} ==\n\n"
        for team_change in team_changes:
            output += team_change
    return output


def get_diff(old_rosters, new_rosters):
    difference = list(diff(old_rosters, new_rosters))
    return difference


def run(old_rosters, new_rosters):
    difference = get_diff(old_rosters, new_rosters)
    output = process_diff_make_output(difference)
    return output
