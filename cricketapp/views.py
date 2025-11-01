from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from .serializers import BulkMatchSquadSerializer
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
# from datetime import datetime
from cricketapp.forms import *
from django.contrib import messages
import razorpay

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
import json
from decimal import Decimal
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from datetime import datetime, timedelta
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone



class InningCreateAPIView(APIView):
    def post(self, request):
        is_bulk = isinstance(request.data, list)
        serializer = InningSerializer(data=request.data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BattingScoreCreateAPIView(APIView):
    def post(self, request):
        is_bulk = isinstance(request.data, list)
        serializer = BattingScoreSerializer(data=request.data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BowlingScoreCreateAPIView(APIView):
    def post(self, request):
        is_bulk = isinstance(request.data, list)
        serializer = BowlingScoreSerializer(data=request.data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlayerCreateAPIView(APIView):
    def post(self, request):
        is_bulk = isinstance(request.data, list)
        serializer = PlayerSerializer(data=request.data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamCreateAPIView(APIView):
    def post(self, request):
        # Check if input is a list for bulk create
        is_bulk = isinstance(request.data, list)

        serializer = TeamSerializer(data=request.data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MatchCreateAPIView(APIView):
    def post(self, request):
        serializer = MatchSerializer(data=request.data, many=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Matches created successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MatchSquadCreateAPIView(APIView):
    def post(self, request):
        serializer = BulkMatchSquadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Squads added successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
def home(request):
    latest_news = NewsArticle.objects.all()[:3]

    
    context = {
        'articles': latest_news
    }
    return render(request, 'index.html',context)

def news_detail(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id)
    
    context = {
        'article': article
    }
    return render(request, 'news_detail.html', context)


def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


def admin_required_404(view_func):
    @wraps(view_func)
    @login_required  # Ensure the user is logged in
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise Http404("Page not found")
    return _wrapped_view




@csrf_exempt
@admin_required_404
def match_squad(request):
    matches = Match.objects.filter(is_active=False)
    if request.method == 'POST':
        print("POST received")
        print("Request.POST:", request.POST)

        if "chkmatch" in request.POST:
            mid = request.POST.get('mid', '').strip()

            if not mid:
                return JsonResponse("Match Not Found", safe=False, status=400)

            try:
                match = Match.objects.get(match_id=int(mid))

                teams = [[match.team1.tid, match.team1.tname],
                         [match.team2.tid, match.team2.tname]]

                team1_players = list(Player.objects.filter(teams__tid=match.team1.tid).values('pid', 'pname'))
                team2_players = list(Player.objects.filter(teams__tid=match.team2.tid).values('pid', 'pname'))


                context = {
                    "teams" : teams,
                    "team1_players" : team1_players,
                    "team2_players" : team2_players,
                }

                return JsonResponse(context)
            except Match.DoesNotExist:
                return JsonResponse({"error": "Match not found"}, status=404)
            except ValueError:
                return JsonResponse({"error": "Invalid Match ID"}, status=400)

        if "msave" in request.POST:
            mid = request.POST.get('mid', '').strip()
            players_json = request.POST.get('players', '[]')

            # Check if match exists
            try:
                match = Match.objects.get(pk=mid)
            except Match.DoesNotExist:
                return JsonResponse({"error": "Match not found"}, status=404)

            # Check if squad already exists for this match
            if MatchSquad.objects.filter(match=match).exists():
                return JsonResponse({"error": "Squad already exists for the selected match"}, status=400)

            # Parse players list
            try:
                players = json.loads(players_json)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid player data"}, status=400)

            # Loop and save to MatchSquad
            for entry in players:
                try:
                    is_playing = bool(entry[0])   # Index 0
                    pname = entry[1].strip()      # Index 1
                    team_name = entry[2].strip()


                    # Fetch player and team objects
                    team = Team.objects.get(tname=team_name)

                    # Get Player object by pname and team (assumes players are unique per team)
                    player = Player.objects.get(pname=pname)

                    # Save to MatchSquad
                    MatchSquad.objects.create(
                        match=match,
                        team=team,
                        player=player,
                        is_playing=is_playing
                    )
                except (Player.DoesNotExist, Team.DoesNotExist):
                    continue  # Or log error and continue

            match.is_active = True
            match.save()

            return JsonResponse({"message": "Squad saved successfully"})

        return JsonResponse("chkmatch not found in POST", safe=False, status=400)

    return render(request, 'match_squad.html', {'matches': matches})



@csrf_exempt
@admin_required_404
def scorecard_entry(request):
    matches = Match.objects.filter(is_active=True, is_completed=False)
    if request.method == 'POST':

        if "chkmatch" in request.POST:
            mid = request.POST.get('mid', '').strip()
            try:
                match = Match.objects.get(match_id=int(mid))
                teams = [[match.team1.tid, match.team1.tname], [match.team2.tid, match.team2.tname]]
                return JsonResponse(teams, safe=False)
            except (Match.DoesNotExist, ValueError):
                return JsonResponse({"error": "Match not found"}, status=404)

        if "chktoss" in request.POST:
            mid = request.POST.get('match', '').strip()
            toss_winner_id = request.POST.get('tossw', '').strip()
            toss_decision = request.POST.get('tossd', '').strip()
            try:
                match = Match.objects.get(match_id=int(mid))
                if toss_winner_id and toss_decision:
                    match.toss_winner_id = int(toss_winner_id)
                    match.toss_decision = toss_decision
                    match.is_live = True
                    match.save()
                team_players = MatchSquad.objects.filter(match=match, is_playing=True) \
                    .values_list('player__pid', 'player__pname', 'team__tid')
                return JsonResponse(list(team_players), safe=False)
            except (Match.DoesNotExist, ValueError):
                return JsonResponse({"error": "Match not found"}, status=404)

        if "save_ball" in request.POST:
            state_data = json.loads(request.POST.get('state'))
            match_id = int(request.POST.get('match_id'))

            try:
                match = Match.objects.get(match_id=match_id)
                match.max_overs = state_data.get('maxOvers', match.max_overs or 20)
                try:
                    # Find the striker and non-striker from the state
                    striker_data = next(b for b in state_data['batsmen'] if b['onStrike'])
                    non_striker_data = next(b for b in state_data['batsmen'] if not b['onStrike'])
                    bowler_data = state_data['bowler']
                    
                    match.current_striker_id = striker_data['id']
                    match.current_non_striker_id = non_striker_data['id']
                    match.current_bowler_id = bowler_data['id']
                except (StopIteration, KeyError):
                    # This might fail if state is weird, so we clear them
                    match.current_striker = None
                    match.current_non_striker = None
                    match.current_bowler = None

                # FIX: Added 'overs' to defaults and use dynamic inning number
                inning, _ = Inning.objects.get_or_create(
                    match=match,
                    number=state_data['inning']['number'],
                    defaults={
                        'batting_team_id': state_data['battingTeam']['id'],
                        'overs': Decimal('0.0')
                    }
                )

                # --- NEW DELETION LOGIC FOR UNDO ---
                # Get all player IDs that are supposed to be in this inning
                
                # 1. Get batsmen currently at the crease
                current_batsman_ids = [b['id'] for b in state_data['batsmen']]
                # 2. Get batsmen who are already out
                current_batsman_ids.extend(state_data.get('outBatsmenIds', []))
                
                # 3. Get all bowlers who have bowled
                current_bowler_ids = [int(bid) for bid in state_data['bowlingFigures'].keys()]

                # Delete any BattingScore records for this inning whose
                # player is NOT in the current state.
                BattingScore.objects.filter(inning=inning).exclude(
                    player_id__in=set(current_batsman_ids)
                ).delete()
                
                # Delete any BowlingScore records for this inning whose
                # player is NOT in the current state.
                BowlingScore.objects.filter(inning=inning).exclude(
                    player_id__in=set(current_bowler_ids)
                ).delete()

                # 3. Delete orphaned FallOfWicket entries
                current_wicket_count = state_data['inning']['wickets']
                FallOfWicket.objects.filter(
                    inning=inning,
                    wicket_number__gt=current_wicket_count
                ).delete()
                # --- END OF NEW DELETION LOGIC ---

                # 1. Update Inning object
                inning.total_runs = state_data['inning']['runs']
                inning.total_wickets = state_data['inning']['wickets']
                total_overs_decimal = Decimal(f"{state_data['inning']['balls'] // 6}.{state_data['inning']['balls'] % 6}")
                inning.overs = total_overs_decimal
                inning.save()

                # 2. Update Batting Scores for current batsmen
                for batsman_state in state_data['batsmen']:
                    batsman_obj = Player.objects.get(pid=batsman_state['id'])
                    BattingScore.objects.update_or_create(
                        inning=inning,
                        player=batsman_obj,
                        defaults={
                            'runs': batsman_state['runs'],
                            'balls': batsman_state['balls'],
                            'fours': batsman_state['fours'],
                            'sixes': batsman_state['sixes'],
                            'dismissal_type': 'Not Out'
                        }
                    )

                # 3. Update Bowling Figures for all bowlers who have bowled
                for bowler_id, bowler_stats in state_data['bowlingFigures'].items():
                    bowler_obj = Player.objects.get(pid=bowler_id)
                    overs_decimal = Decimal(f"{bowler_stats['balls'] // 6}.{bowler_stats['balls'] % 6}")
                    BowlingScore.objects.update_or_create(
                        inning=inning,
                        player=bowler_obj,
                        defaults={
                            'overs': overs_decimal,
                            'maidens': bowler_stats.get('maidens', 0),
                            'runs_conceded': bowler_stats.get('runs', 0),
                            'wickets': bowler_stats.get('wickets', 0),
                            'no_balls': bowler_stats.get('no_balls', 0),
                            'wides': bowler_stats.get('wides', 0)
                        }
                    )

                # 4. Update Extras
                extras_data = state_data['inning']['extras']
                Extras.objects.update_or_create(
                    inning=inning,
                    defaults={
                        'byes': extras_data.get('b', 0),
                        'leg_byes': extras_data.get('lb', 0),
                        'wides': extras_data.get('wd', 0),
                        'no_balls': extras_data.get('nb', 0)
                    }
                )

                # 5. Handle Wicket Event
                if state_data.get('last_event') == 'wicket':
                    wicket_details = state_data.get('wicket_details', {})
                    out_batsman_id = wicket_details.get('out_batsman_id')

                    if out_batsman_id:
                        out_batsman_score = BattingScore.objects.filter(inning=inning, player_id=out_batsman_id).first()
                        if out_batsman_score:
                            out_batsman_score.dismissal_type = wicket_details.get('dismissal_type', 'Out')
                            out_batsman_score.bowler_id = state_data['bowler']['id']

                            fielder_id = wicket_details.get('fielder_id')
                            if fielder_id:
                                out_batsman_score.fielder_id = fielder_id

                            out_batsman_score.save()

                            FallOfWicket.objects.update_or_create(
                                inning=inning,
                                wicket_number=inning.total_wickets,
                                defaults={
                                    'player_id': out_batsman_id,
                                    'score_at_fall': inning.total_runs,
                                    'over': inning.overs
                                }
                            )

                if state_data.get('gameOver'):
                    match.is_completed = True
                    match.is_live = False
                    result_string = "Match Completed" # A sensible default
                    
                    # We can only calculate a result if it's the 2nd innings
                    # and we have a target.
                    if state_data['inning']['number'] == 2 and state_data.get('target') is not None:
                        
                        target_score = state_data['target']
                        second_inning_score = state_data['inning']['runs']
                        
                        try:
                            # Get the 1st inning data
                            first_inning = Inning.objects.get(match=match, number=1)
                            first_inning_team = first_inning.batting_team
                            first_inning_score = first_inning.total_runs
                            
                            # Case 1: Target chased (Batting team wins)
                            if second_inning_score >= target_score:
                                wickets_remaining = 10 - state_data['inning']['wickets']
                                result_string = f"{inning.batting_team.tname} won by {wickets_remaining} wickets"
                            
                            # Case 2: Target not chased
                            else:
                                # Case 2a: Tie
                                if second_inning_score == first_inning_score:
                                    result_string = "Match Tied"
                                
                                # Case 2b: Bowling team wins
                                else:
                                    run_margin = first_inning_score - second_inning_score
                                    result_string = f"{first_inning_team.tname} won by {run_margin} runs"
                                    
                        except Inning.DoesNotExist:
                            result_string = "Result could not be calculated" # Error case
                            
                    match.result = result_string
                    match.current_striker = None
                    match.current_non_striker = None
                    match.current_bowler = None
                    match.save() 
                
                elif state_data.get('inning_completed'):
                    match.current_striker = None
                    match.current_non_striker = None
                    match.current_bowler = None
                    match.save() 

                else:
                    match.save()

                return JsonResponse({"status": "success", "message": "Data saved"})

            except Match.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Match not found"}, status=404)
            except Player.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Player not found"}, status=404)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)


    return render(request, 'scorecard_entry.html', {'matches': matches, 'dismissal_choices': BattingScore.DISMISSAL_CHOICES, })

def get_match_state_for_scoring(request, match_id):
    """
    Checks if a match is live and, if so, reconstructs the
    JavaScript 'state' object from the database.
    """
    try:
        match = Match.objects.get(match_id=match_id)
        if not match.is_live or match.is_completed:
            # Match is not live, nothing to load
            return JsonResponse({"is_live": False})

        # --- MATCH IS LIVE, RECONSTRUCT THE STATE ---
        current_inning = Inning.objects.filter(match=match).order_by('-number').first()
        if not current_inning:
            return JsonResponse({"is_live": False})

        # --- Get Player Lists ---
        squad = MatchSquad.objects.filter(match=match, is_playing=True)
        batting_team_id = current_inning.batting_team_id
        bowling_team_id = match.team2_id if match.team1_id == batting_team_id else match.team1_id

        batting_players = list(squad.filter(team_id=batting_team_id).values_list('player__pid', 'player__pname', 'team__tid'))
        bowling_players = list(squad.filter(team_id=bowling_team_id).values_list('player__pid', 'player__pname', 'team__tid'))

        # --- Build the Python 'state' object ---
        state = {
            'maxOvers': match.max_overs,
            'gameOver': match.is_completed,
            'tossWinnerId': match.toss_winner_id,
            'tossDecision': match.toss_decision,
            'target': None,
        }

        # --- Inning ---
        inning_overs_decimal = current_inning.overs
        inning_balls = (inning_overs_decimal.to_integral_value() * 6) + (int(inning_overs_decimal % 1 * 10))
        
        try:
            extras = current_inning.extras
            extras_data = {'wd': extras.wides, 'nb': extras.no_balls, 'b': extras.byes, 'lb': extras.leg_byes}
        except Extras.DoesNotExist:
            extras_data = {'wd': 0, 'nb': 0, 'b': 0, 'lb': 0}

        state['inning'] = {
            'number': current_inning.number,
            'runs': current_inning.total_runs,
            'wickets': current_inning.total_wickets,
            'balls': int(inning_balls),
            'extras': extras_data
        }
        
        if current_inning.number == 2:
            try:
                first_inning = Inning.objects.get(match=match, number=1)
                state['target'] = first_inning.total_runs + 1
            except Inning.DoesNotExist:
                state['target'] = 0 # Fallback

        state['battingTeam'] = {
            'id': current_inning.batting_team.tid,
            'name': current_inning.batting_team.tname
        }

        # --- Batsmen (Striker/Non-Striker) ---
        state['batsmen'] = []
        striker_bs = BattingScore.objects.filter(inning=current_inning, player=match.current_striker).first()
        if striker_bs:
            state['batsmen'].append({
                'id': striker_bs.player_id, 'name': striker_bs.player.pname,
                'runs': striker_bs.runs, 'balls': striker_bs.balls,
                'fours': striker_bs.fours, 'sixes': striker_bs.sixes,
                'onStrike': True
            })
        
        non_striker_bs = BattingScore.objects.filter(inning=current_inning, player=match.current_non_striker).first()
        if non_striker_bs:
            state['batsmen'].append({
                'id': non_striker_bs.player_id, 'name': non_striker_bs.player.pname,
                'runs': non_striker_bs.runs, 'balls': non_striker_bs.balls,
                'fours': non_striker_bs.fours, 'sixes': non_striker_bs.sixes,
                'onStrike': False
            })

        # --- Bowler and BowlingFigures ---
        bowling_figures_db = BowlingScore.objects.filter(inning=current_inning)
        bowling_figures_state = {}
        
        for bs in bowling_figures_db:
            overs_decimal = bs.overs
            balls = (overs_decimal.to_integral_value() * 6) + (int(overs_decimal % 1 * 10))
            bowling_figures_state[bs.player_id] = {
                'id': bs.player_id, 'name': bs.player.pname,
                'balls': int(balls), 'maidens': bs.maidens,
                'runs': bs.runs_conceded, 'wickets': bs.wickets,
                'no_balls': bs.no_balls, 'wides': bs.wides
            }
        
        state['bowlingFigures'] = bowling_figures_state
        if match.current_bowler_id in bowling_figures_state:
            state['bowler'] = bowling_figures_state[match.current_bowler_id]
        else:
            state['bowler'] = None # Should be handled by UI

        # --- Out Batsmen ---
        out_ids = list(BattingScore.objects.filter(inning=current_inning).exclude(dismissal_type='Not Out').values_list('player_id', flat=True))
        state['outBatsmenIds'] = out_ids
        
        # --- ThisOver (Limitation) ---
        state['thisOver'] = [] # Cannot be reconstructed from DB. Will be blank on load.

        return JsonResponse({
            "is_live": True,
            "state": state,
            "batting_players": batting_players,
            "bowling_players": bowling_players
        })
        
    except Match.DoesNotExist:
        return JsonResponse({"error": "Match not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to load state: " + str(e)}, status=500)

def get_live_scorecard_json(request, match_id):
    """
    This API view fetches the full, live scorecard data for a match
    and returns it as JSON for the AJAX polling.
    """
    try:
        # Get the main match object
        match = get_object_or_404(Match, match_id=match_id)

        # Use prefetch_related for an efficient query, just like in your match_detail view
        innings_qs = Inning.objects.filter(match=match).prefetch_related(
            'scores__player',
            'scores__bowler',
            'scores__fielder',
            'bowlingscore_set__player',
            'fallofwicket_set__player',
            'extras'
        ).order_by('number')

        # --- Build the JSON Response ---
        
        data = {
            'match_id': match.match_id,
            'is_live': match.is_live,
            'is_completed': match.is_completed,
            'result': match.result or ("Match in progress" if match.is_live else "Upcoming"),
            'live_players': {
                'striker': None,
                'non_striker': None,
                'bowler': None
            },
            'innings': []
        }

        current_inning = innings_qs.last() 
        
        if current_inning and match.is_live:
            striker_score = current_inning.scores.filter(player=match.current_striker).first()
            non_striker_score = current_inning.scores.filter(player=match.current_non_striker).first()
            bowler_score = current_inning.bowlingscore_set.filter(player=match.current_bowler).first()

            if match.current_striker and striker_score:
                data['live_players']['striker'] = {
                    'name': match.current_striker.pname,
                    'runs': striker_score.runs,
                    'balls': striker_score.balls
                }
            
            if match.current_non_striker and non_striker_score:
                data['live_players']['non_striker'] = {
                    'name': match.current_non_striker.pname,
                    'runs': non_striker_score.runs,
                    'balls': non_striker_score.balls
                }
            
            if match.current_bowler:
                data['live_players']['bowler'] = {
                    'name': match.current_bowler.pname,
                    'overs': f"{bowler_score.overs}" if bowler_score else "0.0",
                    'runs': bowler_score.runs_conceded if bowler_score else 0,
                    'wickets': bowler_score.wickets if bowler_score else 0
                }

        for inning in innings_qs:
            inning_data = {
                'number': inning.number,
                'batting_team_name': inning.batting_team.tname,
                'batting_team_image': inning.batting_team.timage.url if inning.batting_team.timage else None,
                'total_runs': inning.total_runs,
                'total_wickets': inning.total_wickets,
                'overs': f"{inning.overs}", # Convert Decimal to string
                'batting_scores': [],
                'bowling_scores': [],
                'fow': [],
                'extras': {}
            }
            
            # 1. Batting Scores
            for bs in inning.scores.all():
                inning_data['batting_scores'].append({
                    'player_name': bs.player.pname,
                    'player_id': bs.player.pid,
                    'runs': bs.runs,
                    'balls': bs.balls,
                    'fours': bs.fours,
                    'sixes': bs.sixes,
                    'sr': f"{bs.strike_rate}",
                    'dismissal_type': bs.dismissal_type,
                    'bowler_name': bs.bowler.pname if bs.bowler else None,
                    'fielder_name': bs.fielder.pname if bs.fielder else None,
                })

            # 2. Bowling Scores
            for bl in inning.bowlingscore_set.all():
                inning_data['bowling_scores'].append({
                    'player_name': bl.player.pname,
                    'player_id': bl.player.pid,
                    'overs': f"{bl.overs}",
                    'maidens': bl.maidens,
                    'runs_conceded': bl.runs_conceded,
                    'wickets': bl.wickets,
                    'no_balls': bl.no_balls,
                    'wides': bl.wides,
                })
                
            # 3. Fall of Wickets
            for fow in inning.fallofwicket_set.all():
                inning_data['fow'].append({
                    'score_at_fall': fow.score_at_fall,
                    'wicket_number': fow.wicket_number,
                    'player_name': fow.player.pname,
                    'over': f"{fow.over}",
                })

            # 4. Extras
            try:
                extras_obj = inning.extras
                inning_data['extras'] = {
                    'total': extras_obj.total(),
                    'byes': extras_obj.byes,
                    'leg_byes': extras_obj.leg_byes,
                    'wides': extras_obj.wides,
                    'no_balls': extras_obj.no_balls,
                    'penalty_runs': extras_obj.penalty_runs,
                }
            except Extras.DoesNotExist:
                 inning_data['extras'] = {'total': 0, 'byes': 0, 'leg_byes': 0, 'wides': 0, 'no_balls': 0, 'penalty_runs': 0}

            data['innings'].append(inning_data)
            
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# In views.py, add this new function

def get_all_live_scores_json(request):
    """
    Returns a simple JSON object of all live or recently completed matches.
    """
    # Get all matches that are live OR were completed
    live_matches = Match.objects.filter(is_live=True, is_completed=False)
    completed_matches = Match.objects.filter(is_completed=True)
    
    data_to_return = {}

    # Process LIVE matches
    for match in live_matches:
        # Get innings for this match
        all_innings = Inning.objects.filter(match=match).order_by('number')
        
        t1_inn = all_innings.filter(batting_team=match.team1).first()
        t2_inn = all_innings.filter(batting_team=match.team2).first()

        data_to_return[match.match_id] = {
            'is_completed': False,
            'result': 'LIVE',
            't1_id': match.team1_id,
            't1_score': t1_inn.total_runs if t1_inn else 0,
            't1_wickets': t1_inn.total_wickets if t1_inn else 0,
            't1_overs': f"{t1_inn.overs}" if t1_inn else "0.0",
            't2_id': match.team2_id,
            't2_score': t2_inn.total_runs if t2_inn else 0,
            't2_wickets': t2_inn.total_wickets if t2_inn else 0,
            't2_overs': f"{t2_inn.overs}" if t2_inn else "0.0",
        }
        
        # If match is live but no innings yet, it means toss is done
        if not t1_inn and not t2_inn:
             data_to_return[match.match_id]['result'] = 'Toss Done'

    # Process COMPLETED matches
    for match in completed_matches:
        # This will add or overwrite the match data with the final result
        data_to_return[match.match_id] = {
            'is_completed': True,
            'result': match.result,
        }

    return JsonResponse(data_to_return)

def matches_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    match_format = request.GET.get('format')
    status = request.GET.get('status')
    tournament_id = request.GET.get('tournament')

    matches = Match.objects.all()

    today = timezone.now().date()
    if status == 'upcoming':
        matches = matches.filter(date__gte=today)
    elif status == 'past':
        matches = matches.filter(date__lt=today)

    if start_date:
        matches = matches.filter(date__gte=start_date)
    if end_date:
        matches = matches.filter(date__lte=end_date)

    if tournament_id and tournament_id != 'all':
        matches = matches.filter(tournament_id=tournament_id)

    if match_format and match_format != 'all':
        matches = matches.filter(format=match_format)


    matches = matches.order_by('-date')

    tournaments = Tournament.objects.all().order_by('name')

    context = {
        'matches': matches,
        'tournaments': tournaments,
        'selected_start_date': start_date,
        'selected_end_date': end_date,
        'selected_format': match_format,
        'selected_status': status,
        'selected_tournament': int(tournament_id) if tournament_id and tournament_id.isdigit() else None,
        'format_choices': Match.FORMAT_CHOICES,
    }

    return render(request, 'matches.html', context)

def match_detail(request, match_id):
    """
    This view fetches a specific match and all its related data efficiently.
    """
    # Get the main match object or return a 404 error if not found.
    match = get_object_or_404(Match, match_id=match_id)

    # --- Efficient Data Fetching ---
    # Use prefetch_related to get all related data for all innings of this match
    # in a minimal number of database queries. This is much more efficient than
    # filtering in the template.
    innings = Inning.objects.filter(match=match).prefetch_related(
        'scores__player',         # Prefetch batting scores and their related players
        'scores__bowler',         # Prefetch the bowler for each dismissal
        'scores__fielder',        # Prefetch the fielder for each dismissal
        'bowlingscore_set__player', # Prefetch bowling scores and their related players
        'fallofwicket_set__player', # Prefetch fall-of-wickets and the players involved
        'extras'                  # Prefetch the single extras object for each inning
    ).order_by('number')

    # --- Prepare Squad Data ---
    # Fetch all squad members for this match at once.
    squad_list = MatchSquad.objects.filter(match=match).select_related('player', 'team')

    # Organize the squad list into a dictionary where keys are team IDs.
    # This makes it easy to look up a team's squad in the template.
    squads = {
        match.team1.tid: [s for s in squad_list if s.team_id == match.team1.tid],
        match.team2.tid: [s for s in squad_list if s.team_id == match.team2.tid],
    }

    standings = None
    if match.tournament:
        standings = TeamStanding.objects.filter(tournament=match.tournament).select_related('team').order_by('-points', '-net_run_rate')

    # The context dictionary passes all the prepared data to the template.
    context = {
        'match': match,
        'innings': innings,  # This queryset now contains all nested data.
        'squads': squads,
        'standings': standings,
    }

    return render(request, 'match_detail.html', context)


def teams_view(request):
    """
    This view fetches all Team objects from the database and passes them
    to the 'teams.html' template.
    """
    # Retrieve all teams, ordering them by name
    all_teams = Team.objects.all().order_by('team_type', 'tname')

    # Define the context to be passed to the template
    context = {
        'teams': all_teams,
    }

    # Render the request, template, and context
    return render(request, 'teams.html', context)

def players_view(request, tid):
    """
    This view handles displaying players for a specific team.
    It fetches the team based on the provided 'tid' (team ID).
    It also handles an optional search query 'q' to filter players by name.
    """
    # Get the specific team object, or return a 404 error if not found
    team = get_object_or_404(Team, tid=tid)

    # Get the search query from the GET parameters. Default to an empty string.
    query = request.GET.get('q', '')

    # Get all players related to the team
    players_list = team.players.all().order_by('pname')

    # If a search query is provided, filter the players list
    if query:
        players_list = players_list.filter(pname__icontains=query)

    # Define the context
    context = {
        'team': team,
        'players': players_list,
    }

    # Render the template with the context
    return render(request, 'players.html', context)

from collections import defaultdict
import math

# Helper function to convert overs to balls for calculations
# def convert_overs_to_balls(overs_decimal):
#     """Converts a decimal representation of overs (e.g., 4.5) to total balls (e.g., 29)."""
#     overs = int(overs_decimal)
#     balls = round((overs_decimal - overs) * 10)
#     return (overs * 6) + balls

def convert_overs_to_balls(overs):
    """Convert overs (like 4.3) to total balls (27)"""
    if not overs:
        return 0
    whole_overs = int(overs)
    balls = whole_overs * 6
    fractional_part = overs - whole_overs
    if fractional_part > 0:
        balls += int(fractional_part * 10)  # .3 becomes 3 balls
    return balls

def player_detail(request, pid):
    """
    Displays the detailed profile and tournament-wise career statistics for a single player.
    """
    player = get_object_or_404(Player, pid=pid)
    teams = player.teams.all()

    # --- New Logic for Tournament-wise Stats ---

    # A dictionary to hold stats for each tournament, e.g., {tournament_id: stats_dict}
    tournament_stats = defaultdict(lambda: {
        'tournament': None,
        'batting': {
            'matches': set(), 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
            'not_outs': 0, 'highest_score': 0, 'hs_not_out': False, 'fifties': 0, 'hundreds': 0,
        },
        'bowling': {
            'matches': set(), 'innings': 0, 'overs': 0.0, 'runs_conceded': 0, 'wickets': 0,
            'maidens': 0, 'best_wickets': 0, 'best_runs': 1000,
        }
    })

    # 1. Aggregate Batting Stats
    batting_records = BattingScore.objects.filter(player=player).select_related('inning__match__tournament')
    for record in batting_records:
        match = record.inning.match
        if not match.tournament:
            continue

        tourn_id = match.tournament.id
        stats = tournament_stats[tourn_id]
        stats['tournament'] = match.tournament

        # Batting
        b_stats = stats['batting']
        b_stats['matches'].add(match.match_id)
        b_stats['innings'] += 1
        b_stats['runs'] += record.runs
        b_stats['balls'] += record.balls
        b_stats['fours'] += record.fours
        b_stats['sixes'] += record.sixes
        if record.dismissal_type == 'Not Out':
            b_stats['not_outs'] += 1
        if record.runs >= 100:
            b_stats['hundreds'] += 1
        elif record.runs >= 50:
            b_stats['fifties'] += 1
        if record.runs > b_stats['highest_score']:
            b_stats['highest_score'] = record.runs
            b_stats['hs_not_out'] = (record.dismissal_type == 'Not Out')

    # 2. Aggregate Bowling Stats
    bowling_records = BowlingScore.objects.filter(player=player).select_related('inning__match__tournament')
    for record in bowling_records:
        match = record.inning.match
        if not match.tournament:
            continue

        tourn_id = match.tournament.id
        stats = tournament_stats[tourn_id]
        stats['tournament'] = match.tournament

        # Bowling
        bo_stats = stats['bowling']
        bo_stats['matches'].add(match.match_id)
        bo_stats['innings'] += 1
        bo_stats['overs'] += float(record.overs)
        bo_stats['runs_conceded'] += record.runs_conceded
        bo_stats['wickets'] += record.wickets
        bo_stats['maidens'] += record.maidens
        # Update best bowling figures
        if record.wickets > bo_stats['best_wickets'] or \
          (record.wickets == bo_stats['best_wickets'] and record.runs_conceded < bo_stats['best_runs']):
            bo_stats['best_wickets'] = record.wickets
            bo_stats['best_runs'] = record.runs_conceded


    # 3. Post-process to calculate averages, SR, etc. and format the data
    processed_stats = []
    for tourn_id, stats in tournament_stats.items():
        # Batting calcs
        b_stats = stats['batting']
        b_stats['matches'] = len(b_stats['matches'])
        outs = b_stats['innings'] - b_stats['not_outs']
        b_stats['average'] = round(b_stats['runs'] / outs, 2) if outs > 0 else 0.0
        b_stats['strike_rate'] = round((b_stats['runs'] / b_stats['balls']) * 100, 2) if b_stats['balls'] > 0 else 0.0

        # Bowling calcs
        bo_stats = stats['bowling']
        bo_stats['matches'] = len(bo_stats['matches']) # Recalculate based on bowling matches
        bo_stats['average'] = round(bo_stats['runs_conceded'] / bo_stats['wickets'], 2) if bo_stats['wickets'] > 0 else 0.0
        total_balls_bowled = convert_overs_to_balls(bo_stats['overs'])
        bo_stats['strike_rate'] = round(total_balls_bowled / bo_stats['wickets'], 2) if bo_stats['wickets'] > 0 else 0.0
        bo_stats['economy'] = round(bo_stats['runs_conceded'] / (total_balls_bowled / 6), 2) if total_balls_bowled > 0 else 0.0
        if bo_stats['best_wickets'] > 0:
            bo_stats['bbi'] = f"{bo_stats['best_wickets']}/{bo_stats['best_runs']}"
        else:
            bo_stats['bbi'] = '-'

        processed_stats.append(stats)

    # Sort by tournament start date, most recent first
    processed_stats.sort(key=lambda x: x['tournament'].start_date, reverse=True)

    context = {
        'player': player,
        'teams': teams,
        'tournament_stats': processed_stats,
    }
    return render(request, 'player_detail.html', context)



def admin_api(request):
    return render(request, 'admin_api.html')

# def matches(request):
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     match_format = request.GET.get('format')

#     matches = Matches.objects.filter(is_active=True)

#     if start_date:
#         start_date = datetime.strptime(start_date, '%Y-%m-%d')
#         matches = matches.filter(matches2__m_date__gte=start_date)

#     if end_date:
#         end_date = datetime.strptime(end_date, '%Y-%m-%d')
#         matches = matches.filter(matches2__m_date__lte=end_date)

#     if match_format and match_format != 'all':
#         matches = matches.filter(cat=match_format)

#     matches = matches.order_by('matches2__m_date')

#     return render(request, 'matches.html', {
#         'matches': matches,
#         'selected_start_date': start_date,
#         'selected_end_date': end_date,
#         'selected_format': match_format
#     })



# def rankings(request,format=1):
#     test_rankings = Ranking.objects.filter(format=1).select_related('team')
#     odi_rankings = Ranking.objects.filter(format=2).select_related('team')
#     t20_rankings = Ranking.objects.filter(format=3).select_related('team')

#     context = {
#         'test_rankings': test_rankings,
#         'odi_rankings': odi_rankings,
#         't20_rankings': t20_rankings,
#         'selected_format': format,
#     }

#     return render(request, 'rankings.html', context)

from django.db.models import Min

def tickets(request):
    """
    Displays a list of available matches for ticket booking.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Fetch matches that are not completed yet
    # Annotate each match with the minimum price from its available ticket categories
    matches = Match.objects.filter(is_completed=False).annotate(
        min_price=Min('matchticketavailability__category__price')
    ).order_by('date')

    # Apply date filters if they are provided in the request
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            matches = matches.filter(date__gte=start_date_obj)
        except (ValueError, TypeError):
            start_date = None # Reset if format is incorrect

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            matches = matches.filter(date__lte=end_date_obj)
        except (ValueError, TypeError):
            end_date = None # Reset if format is incorrect

    context = {
        'matches': matches,
        'selected_start_date': start_date,
        'selected_end_date': end_date,
    }
    return render(request, 'tickets.html', context)

from django.db import transaction
@login_required # Ensures only logged-in users can access this page
def book_ticket(request, match_id):
    match = get_object_or_404(Match, match_id=match_id)

    # Get all ticket availability info for this match to display
    availabilities = MatchTicketAvailability.objects.filter(match=match).select_related('category').order_by('category__price')

    if request.method == 'POST':
        # Pass match_id to the form to validate the selected category
        form = BookingForm(request.POST, match_id=match.match_id)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            category = form.cleaned_data['category']

            try:
                # Use a transaction to ensure seat availability is updated safely
                with transaction.atomic():
                    # Lock the specific availability row to prevent race conditions
                    availability = MatchTicketAvailability.objects.select_for_update().get(
                        match=match,
                        category=category
                    )

                    if availability.available_seats >= quantity:
                        # --- START OF CHANGES ---

                        # 1. Create the booking record and store it in a variable
                        new_booking = TicketBooking.objects.create(
                            user=request.user,
                            match=match,
                            category=category,
                            quantity=quantity
                            # total_price is auto-calculated by the model's save method
                        )

                        # 2. Create the associated Payment record with 'Pending' status
                        Payment.objects.create(
                            booking=new_booking,
                            status='Pending',
                            payment_method='Razorpay' # Or leave blank if you prefer
                        )

                        # --- END OF CHANGES ---

                        # Decrease the number of available seats
                        availability.available_seats -= quantity
                        availability.save()

                        messages.success(request, f'Successfully booked {quantity} ticket(s) in {category.name}. Please proceed to payment.')
                        return redirect('my_bookings') # Redirect to the bookings page to pay
                    else:
                        messages.error(request, f"Sorry, only {availability.available_seats} tickets are left in the '{category.name}' category.")

            except MatchTicketAvailability.DoesNotExist:
                messages.error(request, "The selected ticket category is invalid for this match.")

    else:
        # For a GET request, initialize the form with the correct categories
        form = BookingForm(match_id=match.match_id)

    context = {
        'form': form,
        'match': match,
        'availabilities': availabilities,
    }
    return render(request, 'book_ticket.html', context)

@login_required
def my_bookings(request):
    """
    Displays a list of all tickets booked by the current user.
    """
    # Retrieve all bookings for the logged-in user.
    # We use select_related to fetch related objects (match, team, category)
    # in a single, more efficient database query.
    bookings = TicketBooking.objects.filter(
        user=request.user
    ).select_related(
        'match', 'match__team1', 'match__team2', 'category'
    ).order_by('-booking_time')

    context = {
        'bookings': bookings
    }
    return render(request, 'my_bookings.html', context)


@login_required
@require_POST # This decorator ensures the view can only be accessed via a POST request for security.
def cancel_booking(request, booking_id):
    """
    Cancels a specific booking and restores the available seats for that ticket category.
    """
    # Retrieve the specific booking, ensuring it belongs to the current user.
    # This prevents one user from being able to cancel another user's booking.
    booking = get_object_or_404(TicketBooking, id=booking_id, user=request.user)

    try:
        # A database transaction ensures that updating the seat count and deleting
        # the booking either both succeed or both fail, preventing data inconsistency.
        with transaction.atomic():
            # Find the corresponding ticket availability to add the seats back.
            # select_for_update() locks the database row to prevent race conditions,
            # which could happen if two users try to cancel at the same time.
            availability = MatchTicketAvailability.objects.select_for_update().get(
                match=booking.match,
                category=booking.category
            )

            # Increase the available seat count by the quantity from the canceled booking.
            availability.available_seats += booking.quantity
            availability.save()

            # After the seats are successfully restored, delete the booking record.
            booking.delete()

            messages.success(request, f"Your booking for '{booking.match.match_name}' has been successfully canceled.")

    except MatchTicketAvailability.DoesNotExist:
        messages.error(request, "Could not process cancellation due to a system error. Please contact support.")
    except Exception as e:
        # Catch any other unexpected errors during the process for robust error handling.
        messages.error(request, f"An unexpected error occurred: {e}")

    # Redirect the user back to their list of bookings.
    return redirect('my_bookings')

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def payment_initiate(request, booking_id):
    """
    Creates a Razorpay order and redirects to the payment page.
    """
    booking = get_object_or_404(TicketBooking, id=booking_id, user=request.user)

    # Ensure the booking hasn't already been paid for
    if hasattr(booking, 'payment') and booking.payment.status == 'Paid':
        messages.warning(request, "This booking has already been paid for.")
        return redirect('my_bookings')

    # Amount should be in paise (e.g., 500.00 becomes 50000)
    amount = int(booking.total_price * 100)

    # Create Razorpay order
    try:
        order_data = {
            "amount": amount,
            "currency": "INR",
            "receipt": f"booking_{booking.id}",
            "notes": {
                "booking_id": str(booking.id),
                "user_id": str(request.user.id),
            }
        }
        order = razorpay_client.order.create(data=order_data)
    except Exception as e:
        messages.error(request, f"Could not initiate payment. Error: {e}")
        return redirect('my_bookings')

    context = {
        'order': order,
        'booking': booking,
        'api_key': settings.RAZORPAY_KEY_ID,
    }

    return render(request, 'payment.html', context)

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def payment_success(request):
    """
    Handles the callback from Razorpay after a successful payment.
    Verifies the signature, updates the booking, and sends a confirmation email.
    """
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify the payment signature
            razorpay_client.utility.verify_payment_signature(params_dict)

            order_details = razorpay_client.order.fetch(order_id)
            booking_id = order_details['notes']['booking_id']

            # Update the payment status in our database
            payment = get_object_or_404(Payment, booking__id=booking_id)
            payment.status = 'Paid'
            payment.transaction_id = payment_id
            payment.paid_at = timezone.now()
            payment.save()

            # --- EMAIL SENDING LOGIC ---
            booking = payment.booking
            # Consistently use the user who owns the booking
            user_who_booked = booking.user
            recipient_email = user_who_booked.email

            subject = f"Your Ticket Booking is Confirmed: {booking.match.match_name}"
            # Use the correct user object for the greeting
            message = f"""
            Hi {user_who_booked.first_name or user_who_booked.username},

            Your payment has been successfully processed and your booking is confirmed!

            Here are your booking details:
            - Match: {booking.match.match_name}
            - Teams: {booking.match.team1.tname} vs {booking.match.team2.tname}
            - Venue: {booking.match.venue}
            - Date: {booking.match.date.strftime('%d %B, %Y')}
            - Category: {booking.category.name}
            - Quantity: {booking.quantity}
            - Total Price: ₹{booking.total_price}
            - Booking ID: {booking.id}
            - Transaction ID: {payment.transaction_id}

            You can view your ticket in the "My Bookings" section on our website.

            Thank you for booking with us!

            Regards,
            CricketZone
            """
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )
                messages.success(request, "Payment successful! A confirmation email has been sent.")
            except Exception as e:
                logger.error(f"EMAIL SENDING FAILED: An exception of type {type(e).__name__} occurred. Arguments:\n{e.args}")
                messages.warning(request, "Your payment was successful, but we couldn't send a confirmation email.")

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed. Please contact support.")
        except Exception as e:
            messages.error(request, f"An error occurred during payment confirmation: {e}")

        return redirect('my_bookings')

    messages.error(request, "Invalid request method.")
    return redirect('my_bookings')


@login_required
def view_ticket(request, booking_id):
    """
    Displays a printable ticket page for a confirmed booking.
    """
    booking = get_object_or_404(
        TicketBooking,
        id=booking_id,
        user=request.user,  # Ensures the ticket belongs to the logged-in user
    )

    # Security check: Only allow viewing if the ticket is paid
    if not hasattr(booking, 'payment') or booking.payment.status != 'Paid':
        messages.error(request, "This ticket has not been paid for or does not exist.")
        return redirect('my_bookings')

    return render(request, 'view_ticket.html', {'booking': booking})

def download_ticket_pdf(request, booking_id):
    booking = get_object_or_404(TicketBooking, id=booking_id)
    qr_data_url = request.build_absolute_uri()
    template = get_template('ticket_pdf.html')

    # --- ADD THESE TWO LINES ---
    base_url = f"{request.scheme}://{request.get_host()}"
    context = {
        'booking': booking,
        'qr_data_url': qr_data_url,
        'base_url': base_url, # Pass the base URL to the template
    }

    # The rest of the view remains the same
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_{booking.id}.pdf"'
        return response

    return HttpResponse("Error Rendering PDF", status=400)

# def add_to_cart(request, ticket_id):
#     ticket = get_object_or_404(Ticket, id=ticket_id)

#     if request.method == 'POST':
#         form = TicketBookingForm(request.POST)
#         if form.is_valid():
#             # Check if the ticket is already in the cart for the user and selected section
#             existing_cart_item = Cart.objects.filter(
#                 user=request.user,
#                 ticket=ticket,
#                 section=form.cleaned_data['section']
#             ).first()

#             if existing_cart_item:
#                 # If it exists, show a message that it's already in the cart
#                 messages.error(request, 'Ticket already exists in your cart.')
#             else:
#                 # Create a new cart item
#                 cart_item = form.save(commit=False)
#                 cart_item.user = request.user
#                 cart_item.ticket = ticket
#                 cart_item.save()
#                 messages.success(request, 'Ticket successfully added to cart.')

#     else:
#         form = TicketBookingForm()

#     return render(request, 'book_ticket.html', {'ticket': ticket, 'form': form})

# def order(request):
#     cart = Cart.objects.filter(user=request.user)

#     for item in cart:
#         item.total_price = float(item.quantity) * float(item.ticket.ticket_price)

#     context = {'cart': cart}
#     return render(request, 'order.html', context)

# def remove_from_cart(request, item_id):
#     cart_item = get_object_or_404(Cart, id=item_id, user=request.user)

#     if request.method == 'POST':
#         cart_item.delete()
#         return redirect('order')  # Redirect back to the order page after removal

#     return redirect('order')

# def payment_page(request):
#     # Logic for payment processing goes here
#     return render(request, 'payment.html')


# def contact(request):
#     return render(request,'contact.html')

# def about(request):
#     return render(request,'about.html')

def user_signup(request):
    if request.method=='GET':
        return render(request,'signup.html')
    else:
        context={}

        n=request.POST['uname']
        em=request.POST['uemail']
        p=request.POST['upass']
        cp=request.POST['ucpass']

        if n=='' or em=='' or p=='' or cp=='':
            context['errmsg']='Field can not be blank'
            return render(request,'signup.html',context)
        elif len(p)<=8:
            context['errmsg']='password must be atleast 8 character'
            return render(request,'signup.html',context)
        elif p!=cp:
            context['errmsg']='password and confirm password must be same'
            return render(request,'signup.html',context)
        else:
            try:
                u=User.objects.create(username=n,email=em)
                u.set_password(p )
                u.save()
                context['success']='User Created Successfully'
                return render(request,'signup.html',context)
            except Exception:
                context['errmsg']="User already Exist, Please Login!"
                return render(request,'signup.html',context)

def user_login(request):
    if request.method=='GET':
        return render(request,'login.html')
    else:
        n=request.POST['uname']
        p=request.POST['upass']

        u=authenticate(username=n,password=p)
        if u is not None:
            login(request,u)
            return redirect('/home')
        else:
            context={}
            context['errmsg']='Invalid Username and Password'
            return render(request,'login.html',context)

def user_logout(request):
    logout(request)
    return redirect('/home')


def about_us(request):
    # This will look for a template at 'cricket_app/about_us.html'
    return render(request, 'about_us.html')

@login_required
def user_profile(request):
    # Fetch bookings for the currently logged-in user
    try:
        # Use your model 'TicketBooking' and field 'booking_time'
        user_bookings = TicketBooking.objects.filter(user=request.user).order_by('-booking_time')
    except:
        user_bookings = None 

    context = {
        'user_bookings': user_bookings
    }
    return render(request, 'user_profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Only initialize the UserUpdateForm
        u_form = UserUpdateForm(request.POST, instance=request.user)
        
        if u_form.is_valid():
            u_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('user_profile') # Redirect back to the profile page

    else:
        # On GET, populate form with existing data
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
        # 'p_form' is removed
    }

    return render(request, 'edit_profile.html', context)


