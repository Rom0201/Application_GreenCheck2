from django.db import models

# Create your models here.

class User(models.Model):
    firstname = models.CharField("nom", max_length=50)
    lastname = models.CharField("prénom", max_length=50)
    email = models.CharField("email", max_length=100, unique=True)
    password = models.CharField("mot de passe", max_length=255)
    ROLE_CHOICE = [
        ("user", "Utilisateur"),
        ("admin", "Administrateur"),
    ]
    
    role = models.CharField("role", max_length=30, choices=ROLE_CHOICE, default="user")
    
    def __str__(self):
        return self.firstname