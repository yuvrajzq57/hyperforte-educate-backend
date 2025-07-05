from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Uses a single 'name' field instead of first_name/last_name.
    """
    # Authentication fields
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)  # Required for admin
    
    # Make the first_name and last_name fields optional since we're using 'name'
    first_name = None
    last_name = None
    
    # Profile fields
    avatar = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the user's profile picture"
    )
    
    # Groups and permissions with custom related names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='authent_user_set',
        related_query_name='user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='authent_user_set',
        related_query_name='user',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    class Meta:
        ordering = ['name', 'email']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def get_full_name(self):
        """Return the name field as full name."""
        return self.name
    
    def get_short_name(self):
        """Return the name field as short name."""
        return self.name