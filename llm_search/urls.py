# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 18:38:21 2022

@author: jscru
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
]
