# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 18:38:21 2022

@author: jscru
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('history/<int:day_offset>/rank<int:no_to_display>/', views.update, name='update'),
    path('adding/<str:word_type>/', views.add_word, name='add_word'),
    path('removing/<str:word_type>/', views.remove, name='remove'),
    # path('history/<int:day_offset>/rank<int:no_to_display>/', views.go_back, name='go_back'),
    # path('history/<int:day_offset>/rank<int:no_to_display>/', views.go_forward, name='go_forward'),
]