# forms.py
# from django import forms
# from .models import Cart

# class TicketBookingForm(forms.ModelForm):
#     class Meta:
#         model = Cart
#         fields = ['quantity', 'section']
#         widgets = {
#             'quantity': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': 'form-control'}),
#             'section': forms.Select(attrs={
#                 'class': 'form-control',
#                 'style': 'background-color: #222831; width: 100%; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px; font-size: 16px; color: #495057;',
#                  'onfocus':"this.style.borderColor='#ee1e46';"
#             }),
#         }

# app_name/forms.py

from django import forms
from .models import TicketBooking, TicketCategory, MatchTicketAvailability

class BookingForm(forms.ModelForm):
    """
    A form for booking tickets, with a dynamic choice of categories
    based on the selected match.
    """
    # The category field will be a dropdown populated by the view
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.none(), # Initially empty
        label="Select Category",
        empty_label="--- Select a Ticket Category ---",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TicketBooking
        fields = ['category', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1, # Default to 1 ticket
            })
        }

    def __init__(self, *args, **kwargs):
        # Get the match_id passed from the view to filter categories
        match_id = kwargs.pop('match_id', None)
        super().__init__(*args, **kwargs)

        if match_id:
            # Get the IDs of categories that have available seats for this match
            available_category_ids = MatchTicketAvailability.objects.filter(
                match_id=match_id,
                available_seats__gt=0 # Only show categories with seats
            ).values_list('category_id', flat=True)

            # Set the queryset for the category dropdown
            self.fields['category'].queryset = TicketCategory.objects.filter(
                id__in=available_category_ids
            ).order_by('price')
