from rest_framework import serializers
from .models import Player, Team, Match, MatchSquad,Inning,BattingScore,BowlingScore

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'
        read_only_fields = ['pid']  # optional: if you want to make 'pid' read-only

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'
        read_only_fields = ['tid']  # optional

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

class InningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inning
        fields = '__all__'


class MatchSquadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchSquad
        fields = ['match', 'team', 'player', 'is_playing']

class BulkMatchSquadSerializer(serializers.ListSerializer):
    child = MatchSquadSerializer()

    def create(self, validated_data):
        squads = [MatchSquad(**item) for item in validated_data]
        return MatchSquad.objects.bulk_create(squads)

class BattingScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = BattingScore
        fields = '__all__'

class BowlingScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = BowlingScore
        fields = '__all__'