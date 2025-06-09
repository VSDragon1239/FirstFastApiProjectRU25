from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Чтобы не использовать ФИО...
    """
    nickname = models.CharField(max_length=64, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=64, blank=True)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.user.nickname


class FandomCategory(models.Model):
    """
    Категории произведений, или по другому фэндомов
    """
    name = models.CharField(max_length=31)

    def __str__(self):
        return self.name


class Fandom(models.Model):
    """
    Фэндом, или по другому...
    Тут идёт связь с их категориями и название
    """
    category = models.ForeignKey(FandomCategory, on_delete=models.CASCADE, related_name="fandoms")
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class TagCategory(models.Model):
    """
    Категории тегов (типа жанры, предупреждения, праздники...)
    """
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Метки, типа - Вымышленные существа, вымышленные праздники, попаданчество...
    """
    category = models.ForeignKey(TagCategory, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=64)
    description = models.TextField()

    def __str__(self):
        return self.name


class Direction(models.Model):
    """
    Направление произведения, например Джен (отношение персонажей между собой)
    """
    name = models.CharField(max_length=64)
    description = models.TextField()

    def __str__(self):
        return self.name


class Work(models.Model):
    """
    Самое центральное, что тут есть - произведение
    Связано с тегами и фэндомом многие ко многим через таблицы WorkTag и WorkFandom
    Также есть направленность, название, и количество оценок
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="works")
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, related_name="works")
    name = models.CharField(max_length=64)
    rating_count = models.PositiveIntegerField(default=0)

    # M2M через промежуточные таблицы
    tags = models.ManyToManyField(Tag, through="WorkTag", related_name="works")
    fandoms = models.ManyToManyField(Fandom, through="WorkFandom", related_name="works")

    def __str__(self):
        return self.name


class WorkTag(models.Model):
    """
    Промежуточная таблица для связи многие ко многим произведения и меток (тегов).
    """
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("work", "tag")


class WorkFandom(models.Model):
    """
    Промежуточная таблица для связи многие ко многим произведения и фэндомов.
    """
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    fandom = models.ForeignKey(Fandom, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("work", "fandom")


class Chapter(models.Model):
    """
    Глава - некоторая часть произведения, с большим содержанием текста, который находится в файле - "путь к файлу + название"
    """
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=64)
    file = models.FileField(upload_to="chapters/")

    def __str__(self):
        return f"{self.work.name}: {self.title}"


class Review(models.Model):
    """
    Отзывы, хранятся в файлах, привязаны к пользователям и главам.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE, primary_key=True, related_name="review")
    file = models.FileField(upload_to="reviews/")

    def __str__(self):
        return f"Review for {self.chapter}"
