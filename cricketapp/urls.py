from django.urls import path
from cricketapp import views
from django.conf import settings
from django.conf.urls.static import static
from .views import PlayerCreateAPIView, TeamCreateAPIView, MatchCreateAPIView,MatchSquadCreateAPIView,InningCreateAPIView,BattingScoreCreateAPIView,BowlingScoreCreateAPIView
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('home', views.home, name='home'),
    path('about/', views.about_us, name='about_us'),
    path('news/<int:article_id>/', views.news_detail, name='news_detail'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('', views.home),
    path('scorecard_entry', views.scorecard_entry, name='scorecard_entry'),
    path('match_squad', views.match_squad, name='match_squad'),
    path('players/create/', PlayerCreateAPIView.as_view(), name='player-create'),
    path('teams/create/', TeamCreateAPIView.as_view(), name='team-create'),
    path('match/create/', MatchCreateAPIView.as_view(), name='match-create'),
    path('matchsquad/create/', MatchSquadCreateAPIView.as_view(), name='matchsquad-create'),
    path('inning/create/', InningCreateAPIView.as_view(), name='inning-create'),
    path('batting/create/', BattingScoreCreateAPIView.as_view(), name='BattingScore-create'),
    path('bowling/create/', BowlingScoreCreateAPIView.as_view(), name='BowlingScore-create'),
    path('matches/',views.matches_view, name='matches'),
    path('match_detail/<int:match_id>',views.match_detail, name='match_detail'),
    path('api/live-scorecard/<int:match_id>/', views.get_live_scorecard_json, name='get_live_scorecard_json'),
    path('api/live-scores-list/', views.get_all_live_scores_json, name='get_all_live_scores_json'),
    path('teams/', views.teams_view, name='teams_view'),
    path('teams/<int:tid>/', views.players_view, name='players_view'),
    path('players/<int:pid>/', views.player_detail, name='player_detail'),
    path('admin_api/', views.admin_api, name='admin_api'),
    path('tickets/', views.tickets, name='tickets'),
    # path('rankings',views.rankings),
    # path('contact',views.contact),
    # path('about',views.about),
    path('login',views.user_login,name="login"),
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name="password_reset.html"), 
         name="password_reset"),
         
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), 
         name="password_reset_done"),
         
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), 
         name="password_reset_confirm"),
         
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), 
         name="password_reset_complete"),
    path('logout',views.user_logout,name='logout'),
    path('signup',views.user_signup,name='signup'),
    path('book-ticket/<int:match_id>/', views.book_ticket, name='book_ticket'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('payment/initiate/<int:booking_id>/', views.payment_initiate, name='payment_initiate'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('view-ticket/<int:booking_id>/', views.view_ticket, name='view_ticket'),
    path('ticket/download/<int:booking_id>/', views.download_ticket_pdf, name='download_ticket_pdf'),
    # path('ticket/<int:ticket_id>/add/', views.add_to_cart, name='add_to_cart'),
    # path('order/', views.order, name='order'),
    # path('payment/', views.payment_page, name='payment_page'),
    # path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

]

urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)