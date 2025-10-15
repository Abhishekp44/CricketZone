# matches/templatetags/match_extras.py

from django import template

register = template.Library()

@register.filter
def get_inning_for_team(innings, team):
    return next((inning for inning in innings if inning.batting_team == team), None)

@register.filter
def both_teams(match):
    return [match.team1, match.team2]

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
