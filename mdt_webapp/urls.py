from django.urls import path
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.create_landing, name='index'),
    path('index/', views.create_landing, name='index'),
    path('emissions/', views.show_emissions, name='emissions'),
    path('flow/', views.show_flow, name='flow'),
    path('inspector/<int:segID>/<str:modifiers>',views.create_inspector, name='inspect'),
    path('download/<str:zip_output>/<str:modifiers>', views.download_network, name='download'),
    path('create/', views.create_objs, name='create'),
    path('accounts/login/', views.login_error, name='create'),
]