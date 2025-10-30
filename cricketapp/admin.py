from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# By changing the base class from admin.ModelAdmin to ImportExportModelAdmin,
# we add import/export functionality without changing any other logic.

@admin.register(PlayerStats)
class PlayerStatsAdmin(ImportExportModelAdmin):
    """
    Admin configuration for the PlayerStats model.
    """

    # --- List View Configuration ---
    list_display = (
        'player',
        'career_total_runs',
        'career_batting_average',
        'career_total_wickets',
        't20_strike_rate'
    )

    search_fields = ('player__pname',)

    # --- Detail/Edit View Configuration ---
    readonly_fields = (
        'career_total_runs',
        'career_total_wickets',
        'career_batting_average',
        't20_strike_rate',
    )

    fieldsets = (
        ('Player Information', {
            'fields': ('player',)
        }),
        ('Calculated Career Stats (Read-Only)', {
            'classes': ('collapse',),
            'fields': (
                'career_total_runs',
                'career_batting_average',
                'career_total_wickets',
                't20_strike_rate',
            )
        }),
        ('Test Cricket Stats', {
            'classes': ('collapse',),
            'fields': ('test_stats',),
            'description': 'Edit the JSON data for Test match statistics below.'
        }),
        ('One Day International (ODI) Stats', {
            'classes': ('collapse',),
            'fields': ('odi_stats',),
            'description': 'Edit the JSON data for ODI statistics below.'
        }),
        ('T20 Cricket Stats', {
            'classes': ('collapse',),
            'fields': ('t20_stats',),
            'description': 'Edit the JSON data for T20 statistics below.'
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('player')

@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    list_display = ('pid', 'pname', 'prole', 'parm', 'pjr_no', 'display_teams')
    list_filter = ('prole', 'parm', 'pbowl_style', 'teams__tname')
    search_fields = ('pname', 'pjr_no')

    @admin.display(description='Teams')
    def display_teams(self, obj):
        return ", ".join([team.tname for team in obj.teams.all()])

@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    list_display = ('tid', 'tname')

# Inlines remain the same
class BattingScoreInline(admin.TabularInline):
    model = BattingScore
    extra = 11

class BowlingScoreInline(admin.TabularInline):
    model = BowlingScore
    extra = 6

class FallOfWicketInline(admin.TabularInline):
    model = FallOfWicket
    extra = 5

class ExtrasInline(admin.StackedInline):
    model = Extras
    max_num = 1

class InningInline(admin.StackedInline):
    model = Inning
    extra = 2
    show_change_link = True

@admin.register(Match)
class MatchAdmin(ImportExportModelAdmin):
    list_display = ('match_id', 'date', 'venue', 'team1', 'team2', 'toss_winner', 'toss_decision', 'result', 'is_active')
    list_filter = ('date', 'venue', 'toss_decision')
    search_fields = ('venue', 'team1__tname', 'team2__tname')
    inlines = [InningInline]

@admin.register(MatchSquad)
class MatchSquadAdmin(ImportExportModelAdmin):
    list_display = ('player_name', 'team_name', 'match_display', 'is_playing')
    list_filter = ('team', 'match', 'is_playing')
    search_fields = ('player__pname', 'team__tname', 'match__team1__tname', 'match__team2__tname')

    def player_name(self, obj):
        return obj.player.pname
    player_name.short_description = 'Player'

    def team_name(self, obj):
        return obj.team.tname
    team_name.short_description = 'Team'

    def match_display(self, obj):
        return f"{obj.match.team1.tname} vs {obj.match.team2.tname} on {obj.match.date}"
    match_display.short_description = 'Match'

@admin.register(Inning)
class InningAdmin(ImportExportModelAdmin):
    list_display = ('inning_id', 'match', 'batting_team', 'number', 'total_runs', 'total_wickets', 'overs')
    list_filter = ('number', 'batting_team')
    inlines=[BattingScoreInline,BowlingScoreInline,FallOfWicketInline,ExtrasInline]

@admin.register(BattingScore)
class BattingScoreAdmin(ImportExportModelAdmin):
    list_display = ('inning', 'player', 'runs', 'balls', 'fours', 'sixes', 'dismissal_type', 'bowler', 'fielder')
    list_filter = ('dismissal_type','inning__batting_team','inning__match')
    search_fields = ('player__pname', 'inning__inning_id', 'inning__batting_team__tname')

@admin.register(BowlingScore)
class BowlingScoreAdmin(ImportExportModelAdmin):
    list_display = ('inning', 'player', 'overs', 'maidens', 'runs_conceded', 'wickets', 'no_balls', 'wides')
    search_fields = ('player__pname', 'inning__inning_id', 'inning__batting_team__tname')

@admin.register(FallOfWicket)
class FallOfWicketAdmin(ImportExportModelAdmin):
    list_display = ('inning', 'wicket_number', 'player', 'score_at_fall', 'over')
    list_filter = ('wicket_number',)

@admin.register(Extras)
class ExtrasAdmin(ImportExportModelAdmin):
    list_display = ('inning', 'byes', 'leg_byes', 'wides', 'no_balls', 'penalty_runs')

@admin.register(TicketCategory)
class TicketCategoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'price', 'total_seats')

@admin.register(MatchTicketAvailability)
class MatchTicketAvailabilityAdmin(ImportExportModelAdmin):
    list_display = ('match', 'category', 'available_seats')
    list_filter = ('category',)

@admin.register(TicketBooking)
class TicketBookingAdmin(ImportExportModelAdmin):
    list_display = ('user', 'match', 'category', 'quantity', 'total_price', 'booking_time')
    list_filter = ('match', 'category')
    search_fields = ('user__username',)

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    list_display = ('booking', 'status', 'payment_method', 'transaction_id', 'paid_at')
    list_filter = ('status', 'payment_method')

@admin.register(Tournament)
class TournamentAdmin(ImportExportModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'location')
    search_fields = ('name', 'location')
    list_filter = ('start_date', 'end_date')

@admin.register(TournamentTeam)
class TournamentTeamAdmin(ImportExportModelAdmin):
    list_display = ('tournament', 'team')
    search_fields = ('tournament__name', 'team__tname')
    list_filter = ('tournament',)

@admin.register(TeamStanding)
class TeamStandingAdmin(ImportExportModelAdmin):
    list_display = ('tournament', 'team', 'matches_played', 'wins', 'losses', 'ties', 'no_results', 'points', 'net_run_rate')
    list_filter = ('tournament',)
    search_fields = ('team__tname', 'tournament__name')
    ordering = ('-points', '-net_run_rate')


@admin.register(NewsArticle)
class NewsArticleAdmin(ImportExportModelAdmin):
    list_display = ('title', 'date')
    list_filter = ('date',)
    search_fields = ('title', 'content')
    ordering = ('-date',)

