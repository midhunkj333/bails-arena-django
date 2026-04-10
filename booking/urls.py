from django.urls import path
from . import views 
from .views import login_view,logout_view, index, get_slots, booking_page, report, report_view, download_report

urlpatterns = [
    path('', index),

    # API
    path('api/slots/', get_slots),   # 👈 FIXED
    path('api/report/', report),

    # UI
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
 path('api/customers/', views.customers),
path('api/book/', views.book_slot),
    path('reports/', report_view),  
    path('download-report/', download_report),
    path('book/', booking_page),
]