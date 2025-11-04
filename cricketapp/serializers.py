from rest_framework import serializers
from .models import *

class BulkUpdateListSerializer(serializers.ListSerializer):
    """
    Overrides the default ListSerializer.update() method to perform
    a bulk update using Django's bulk_update() method.
    
    This assumes the incoming data contains an 'id' for matching.
    """
    def update(self, instances, validated_data):
        # 1. Map incoming data to existing instances by 'id'
        instance_mapping = {instance.id: instance for instance in instances}
        
        # 2. Prepare data for bulk_update
        data_to_update = []
        fields_to_update = set() # Store all fields that are being updated
        
        for item_data in validated_data:
            instance_id = item_data.get('id')
            instance = instance_mapping.get(instance_id)

            if instance:
                # 3. Update the instance's attributes in-memory
                for attr, value in item_data.items():
                    if attr != 'id': # Don't try to update the 'id'
                        setattr(instance, attr, value)
                        fields_to_update.add(attr)
                
                data_to_update.append(instance)
            
        if not data_to_update:
            return instances # Nothing to update

        # 4. Perform the bulk_update in a single database query!
        try:
            # We use the child's Meta.model to get the correct model class
            self.child.Meta.model.objects.bulk_update(
                data_to_update, 
                list(fields_to_update)
            )
        except Exception as e:
            # Handle potential database errors
            raise serializers.ValidationError(f"Bulk update failed: {e}")

        return data_to_update

class PlayerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = Player
        fields = '__all__'
        read_only_fields = ['pid']
        list_serializer_class = BulkUpdateListSerializer # ADDED

class TeamSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED

    class Meta:
        model = Team
        fields = '__all__'
        read_only_fields = ['tid']
        list_serializer_class = BulkUpdateListSerializer # ADDED

class MatchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED

    class Meta:
        model = Match
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED

class InningSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = Inning
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED

class MatchSquadSerializer(serializers.ModelSerializer):
    # **NOTE:** Bulk update for MatchSquad is special.
    # It likely has a composite key (match, team, player) and not a simple 'id'.
    # The generic 'BulkUpdateListSerializer' won't work here without modification.
    # We will skip adding bulk update for this one for now.
    class Meta:
        model = MatchSquad
        fields = ['match', 'team', 'player', 'is_playing']

# This is your existing bulk *create* serializer, which is perfect.
class BulkMatchSquadSerializer(serializers.ListSerializer):
    child = MatchSquadSerializer()

    def create(self, validated_data):
        squads = [MatchSquad(**item) for item in validated_data]
        return MatchSquad.objects.bulk_create(squads)

class BattingScoreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = BattingScore
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED

class BowlingScoreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = BowlingScore
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED

class FallOfWicketSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = FallOfWicket
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED


class ExtrasSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # ADDED
    
    class Meta:
        model = Extras
        fields = '__all__'
        list_serializer_class = BulkUpdateListSerializer # ADDED