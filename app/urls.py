from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.BookIndexView.as_view(), name='index'),
    path('Detail/<int:pk>', views.BookDetailView.as_view(), name='detail'),
    path('Check/', views.CheckView.as_view(), name='check'),
    path('Mypage/', views.MypageView.as_view(), name='mypage'),
    path('Inquiry/', views.InquiryView.as_view(), name='inquiry'),
]
