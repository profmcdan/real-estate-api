from django.db import models
from django.conf import settings
from django.urls import reverse


class Agent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=30)
    whatsapp_number = models.CharField(max_length=30)
    picture = models.CharField(max_length=255, null=True, blank=True)


class Apartment(models.Model):
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name='apartments')
    address = models.TextField()


class ApartmentPicture(models.Model):
    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name='apartments')
    image = models.ImageField(upload_to='apartments/')
