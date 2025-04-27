from django.db import models

class Profile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    profile_photo = models.URLField(default="https://i.imgur.com/pG5Zwli.jpg")

    class Meta:
        db_table = 'profile'  # <-- Yeh line batati hai Django ko ki table ka naam 'profile' hi use kare

    def __str__(self):
        return self.name
