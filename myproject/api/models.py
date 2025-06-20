from django.db import models
from django.urls import reverse

from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    """
    Роль пользователя: например 'admin', 'author', 'moderator' и т.п.
    """
    name = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    """
    roles = models.ManyToManyField(Role, related_name="users", blank=True, help_text="Роли, присвоенные пользователю")


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()

    def __str__(self):
        return self.name


class Category(models.Model):
    title = models.CharField(verbose_name='Название категории', max_length=100)
    slug = models.SlugField(verbose_name='Slug', unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(verbose_name='Название товара', max_length=100)
    slug = models.SlugField(verbose_name='Slug', unique=True)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', on_delete=models.CASCADE)
    price = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2)
    description = models.TextField(verbose_name='Описание', max_length=300)
    image = models.ImageField(verbose_name='Изображение', upload_to='images/')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'id': self.id, 'slug': self.slug})


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class WishlistProduct(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()


class Order(models.Model):
    STATUS = {
        'new': 'Новый',
        'paid': 'Оплачен',
        'delivered': 'Доставлен'
    }
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS)
    total = models.PositiveIntegerField()

    def get_total(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    count = models.PositiveIntegerField()

    def get_cost(self):
        return self.product.price * self.count
