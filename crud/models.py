# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Member(models.Model):
    firstname = models.CharField(max_length=40, blank=False)
    lastname = models.CharField(max_length=40, blank=False)
    mobile_number = models.CharField(max_length=10, blank=True)
    description = models.TextField(max_length=255, blank=False)
    location = models.TextField(max_length=255, blank=False)
    date = models.DateField('%m/%d/%Y')
    created_at = models.DateTimeField('%m/%d/%Y %H:%M:%S')
    updated_at = models.DateTimeField('%m/%d/%Y %H:%M:%S')


class Simulation(models.Model):
    user_id = models.CharField(max_length=255,default=False)
    basket_icon_click = models.IntegerField(default=False)
    basket_add_list = models.IntegerField(default=False)
    basket_add_detail = models.IntegerField(default=False)
    sort_by = models.IntegerField(default=False)
    image_picker = models.IntegerField(default=False)
    account_page_click = models.IntegerField(default=False)
    promo_banner_click = models.IntegerField(default=False)
    detail_wishlist_add = models.IntegerField(default=False)
    list_size_dropdown = models.IntegerField(default=False)
    closed_minibasket_click = models.IntegerField(default=False)
    checked_delivery_detail = models.IntegerField(default=False)
    checked_returns_detail = models.IntegerField(default=False)
    sign_in = models.IntegerField(default=False)
    saw_checkout = models.IntegerField(default=False)
    saw_sizecharts = models.IntegerField(default=False)
    saw_delivery = models.IntegerField(default=False)
    saw_account_upgrade = models.IntegerField(default=False)
    saw_homepage = models.IntegerField(default=False)
    device_computer = models.IntegerField(default=False)
    device_tablet = models.IntegerField(default=False)
    returning_user = models.IntegerField(default=False)
    loc_uk = models.IntegerField(default=False)
    propensity = models.FloatField(default=False) 
    score = models.FloatField(default=False)
    created_at = models.DateTimeField('%m/%d/%Y %H:%M:%S')
    updated_at = models.DateTimeField('%m/%d/%Y %H:%M:%S')
    