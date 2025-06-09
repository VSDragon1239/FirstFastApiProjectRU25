from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile


# Автоматически создавать Profile при регистрации
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    При создании нового пользователя автоматически заводим для него Profile.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    При каждом сохранении User сохраняем и профиль (если меняли его данные через форму).
    """
    instance.profile.save()
