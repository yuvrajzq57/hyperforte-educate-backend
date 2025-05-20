from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Uses a single 'name' field instead of first_name/last_name.


    """

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='authent_user_set',  # Custom related_name
        related_query_name='user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='authent_user_set',  # Custom related_name
        related_query_name='user',
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    
    # Make the first_name and last_name fields optional since we're using 'name'
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.email})"