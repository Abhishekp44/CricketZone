from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateField()
    # Images will be uploaded to a 'news_images/' folder inside 'media/'
    image = models.ImageField(upload_to='news_images/')

    def __str__(self):
        return self.title

    class Meta:
        # This will make the newest articles appear first
        ordering = ['-date']

class Team(models.Model):
    # Define the choices for the team type
    class TeamType(models.TextChoices):
        INTERNATIONAL = 'INT', 'International'
        IPL = 'IPL', 'Indian Premier League'
        DOMESTIC = 'DOM', 'Domestic'
        OTHER = 'OTH', 'Other'

    tid = models.AutoField(primary_key=True)
    tname = models.CharField(max_length=70)
    timage = models.ImageField(upload_to='team_images/', null=True, blank=True)

    # New field for team category
    team_type = models.CharField(
        max_length=3,
        choices=TeamType.choices,
        default=TeamType.INTERNATIONAL
    )

    def __str__(self):
        return self.tname


class Player(models.Model):
    ROLE_CHOICES = [
        ('Wicket Keeper', 'Wicket Keeper'),
        ('Batsman', 'Batsman'),
        ('Bowler', 'Bowler'),
        ('All-Rounder', 'All-Rounder'),
    ]

    ARM_CHOICES = [
        ('left arm', 'Left Arm'),
        ('right arm', 'Right Arm'),
    ]

    BOWLING_STYLE_CHOICES = [
        ('fast', 'Fast'),
        ('spin', 'Spin'),
    ]

    pid = models.AutoField(primary_key=True)  # serial
    pname = models.CharField(max_length=70)
    prole = models.CharField(max_length=20, choices=ROLE_CHOICES)
    parm = models.CharField(max_length=10, choices=ARM_CHOICES)
    pbowl_style = models.CharField(max_length=10, choices=BOWLING_STYLE_CHOICES, blank=True)
    pjr_no = models.IntegerField()  # New field added
    pimage = models.ImageField(upload_to='player_images/', null=True, blank=True)
    teams = models.ManyToManyField(Team, related_name='players', null=True, blank=True)
    current_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_players'
    )

    def __str__(self):
        return f"{self.pname} ({self.pjr_no})"


def get_default_stats_dict():
    return {
        "matches": 0, "innings_batted": 0, "not_outs": 0, "total_runs": 0,
        "balls_faced": 0, "highest_score": 0, "highest_score_is_not_out": False,
        "fifties": 0, "hundreds": 0, "fours": 0, "sixes": 0,
        "innings_bowled": 0, "balls_bowled": 0, "runs_conceded": 0,
        "total_wickets": 0, "maidens": 0, "best_figures": "",
        "five_wicket_hauls": 0, "catches": 0, "stumpings": 0, "run_outs": 0,
    }

class PlayerStats(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='stats')

    # Storing stats for each format in a JSONField
    test_stats = models.JSONField(default=get_default_stats_dict)
    odi_stats = models.JSONField(default=get_default_stats_dict)
    t20_stats = models.JSONField(default=get_default_stats_dict)

    # --- Calculated Career Properties (Totals across all formats) ---

    @property
    def career_total_runs(self):
        return (self.test_stats.get('total_runs', 0) +
                self.odi_stats.get('total_runs', 0) +
                self.t20_stats.get('total_runs', 0))

    @property
    def career_total_wickets(self):
        return (self.test_stats.get('total_wickets', 0) +
                self.odi_stats.get('total_wickets', 0) +
                self.t20_stats.get('total_wickets', 0))

    @property
    def career_batting_average(self):
        total_runs = self.career_total_runs
        total_innings = (self.test_stats.get('innings_batted', 0) +
                         self.odi_stats.get('innings_batted', 0) +
                         self.t20_stats.get('innings_batted', 0))
        total_not_outs = (self.test_stats.get('not_outs', 0) +
                          self.odi_stats.get('not_outs', 0) +
                          self.t20_stats.get('not_outs', 0))

        outs = total_innings - total_not_outs
        if outs > 0:
            return round(total_runs / outs, 2)
        return 0.0

    # You can create similar properties for career strike rate, economy, etc.
    # You can also create properties for format-specific stats for convenience.

    @property
    def t20_strike_rate(self):
        runs = self.t20_stats.get('total_runs', 0)
        balls = self.t20_stats.get('balls_faced', 0)
        if balls > 0:
            return round((runs / balls) * 100, 2)
        return 0.0

    def __str__(self):
        return f"Career Stats for {self.player.pname}"

    class Meta:
        verbose_name = "Player Career Stat"
        verbose_name_plural = "Player Career Stats"



#----------------------------------- Ranking -----------------------------------------------------
class Tournament(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=100)
    is_tour = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class TournamentTeam(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('tournament', 'team')

    def __str__(self):
        return f"{self.team.tname} - {self.tournament.name}"

class TeamStanding(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    matches_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)
    no_results = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    net_run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('tournament', 'team')
        ordering = ['-points', '-net_run_rate']

    def __str__(self):
        return f"{self.team.tname} - {self.points} pts"



#----------------------------------- Scorecard -------------------------------------------------

class Match(models.Model):
    FORMAT_CHOICES = [
        ('t20', 'T20'),
        ('odi', 'ODI'),
        ('test', 'Test'),
    ]
    match_id = models.AutoField(primary_key=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)
    match_name = models.CharField(max_length=150, null=True, blank=True)
    format = models.CharField(max_length=4, choices=FORMAT_CHOICES, null=True, blank=True)
    date = models.DateField()
    venue = models.CharField(max_length=100)
    team1 = models.ForeignKey(Team, related_name='team1_matches', on_delete=models.CASCADE)
    team2 = models.ForeignKey(Team, related_name='team2_matches', on_delete=models.CASCADE)
    toss_winner = models.ForeignKey(Team, related_name='toss_winner', on_delete=models.SET_NULL, null=True,blank=True)
    toss_decision = models.CharField(max_length=10, choices=[('bat', 'Bat'), ('bowl', 'Bowl')], null=True,blank=True)
    result = models.CharField(max_length=100, null=True,blank=True)
    is_active = models.BooleanField(default=False)
    is_live = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    current_striker = models.ForeignKey(
        Player, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='striker_matches'
    )
    current_non_striker = models.ForeignKey(
        Player, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='non_striker_matches'
    )
    current_bowler = models.ForeignKey(
        Player, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='bowler_matches'
    )

    def __str__(self):
        format_display = self.get_format_display() if self.format else "Match"
        return f"{self.team1} vs {self.team2} - {format_display} ({self.date})"

class Inning(models.Model):
    inning_id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    batting_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    number = models.IntegerField()  # 1 or 2
    total_runs = models.IntegerField(default=0)
    total_wickets = models.IntegerField(default=0)
    overs = models.DecimalField(max_digits=4, decimal_places=1)  # e.g., 19.5

    def __str__(self):
        return f"{self.batting_team} - Inning {self.number}"

class BattingScore(models.Model):
    DISMISSAL_CHOICES = [
        ('Not Out', 'Not Out'),
        ('Bowled', 'Bowled'),
        ('Caught', 'Caught'),
        ('LBW', 'LBW'),
        ('Run Out', 'Run Out'),
        ('Stumped', 'Stumped'),
        ('Hit Wicket', 'Hit Wicket'),
        ('Retired Hurt', 'Retired Hurt'),
        ('Obstructing the Field', 'Obstructing the Field'),
        ('Timed Out', 'Timed Out'),
    ]

    inning = models.ForeignKey(Inning, on_delete=models.CASCADE, related_name='scores')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    runs = models.IntegerField()
    balls = models.IntegerField()
    fours = models.IntegerField()
    sixes = models.IntegerField()
    dismissal_type = models.CharField(max_length=30, choices=DISMISSAL_CHOICES)
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='bowled_batsmen')
    fielder = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='caught_batsmen')

    def __str__(self):
        return f"{self.player.pname} - {self.runs} runs"

    @property
    def strike_rate(self):
        if self.balls > 0:
            return round((self.runs / self.balls) * 100, 2)
        return 0.0


class BowlingScore(models.Model):
    inning = models.ForeignKey(Inning, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    overs = models.DecimalField(max_digits=4, decimal_places=1)
    maidens = models.IntegerField()
    runs_conceded = models.IntegerField()
    wickets = models.IntegerField()
    no_balls = models.IntegerField()
    wides = models.IntegerField()

    def __str__(self):
        return f"{self.player.pname} - {self.wickets} wickets"


class FallOfWicket(models.Model):
    inning = models.ForeignKey(Inning, on_delete=models.CASCADE)
    wicket_number = models.IntegerField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score_at_fall = models.IntegerField()
    over = models.DecimalField(max_digits=4, decimal_places=1)

    def __str__(self):
        return f"Wicket {self.wicket_number} - {self.player.pname}"

class Extras(models.Model):
    inning = models.OneToOneField(Inning, on_delete=models.CASCADE)
    byes = models.IntegerField(default=0)
    leg_byes = models.IntegerField(default=0)
    wides = models.IntegerField(default=0)
    no_balls = models.IntegerField(default=0)
    penalty_runs = models.IntegerField(default=0)

    def total(self):
        return self.byes + self.leg_byes + self.wides + self.no_balls + self.penalty_runs

class MatchSquad(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    is_playing = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.player.pname} - {self.team.tname} ({'Playing' if self.is_playing else 'Substitute'})"


#--------------------- TICKET BOOKING SYSTEM ---------------------------------------------------------------
class TicketCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., VIP, General, Box
    price = models.DecimalField(max_digits=8, decimal_places=2)
    total_seats = models.IntegerField()

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class MatchTicketAvailability(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    available_seats = models.IntegerField()

    class Meta:
        unique_together = ('match', 'category')

    def __str__(self):
        return f"{self.match} - {self.category.name} ({self.available_seats} left)"


class TicketBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.match} - {self.category.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Auto calculate total price
        self.total_price = self.category.price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    booking = models.OneToOneField(TicketBooking, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Failed', 'Failed')])
    payment_method = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

