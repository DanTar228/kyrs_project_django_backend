from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

# -------------- soft delete --------------


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])


class SoftDeleteUserModel(AbstractBaseUser):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])


# -------------- model Users --------------


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(
            username=self.model.normalize_username(username=username), **extra_fields
        )  # Create user -+
        user.set_password(password)  # Hash the password
        user.save(using=self._db)  # Save to database
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class User(SoftDeleteUserModel):
    username = models.CharField(unique=True, max_length=16)
    password = models.CharField(max_length=128)
    email = models.EmailField()
    registration_day = models.DateField(default=timezone.now)

    USERNAME_FIELD = "username"
    objects = CustomUserManager()


class Post(SoftDeleteModel):
    title = models.CharField(max_length=32)
    description = models.TextField(max_length=256)
    payment = models.IntegerField()
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    is_open = models.BooleanField(default=True)


class GlobalAdmin(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)


class ResourcesData(SoftDeleteModel):
    resource_url = models.URLField()


class ResourcesRelation(SoftDeleteModel):
    post = models.ForeignKey(Post, on_delete=models.PROTECT)
    resource = models.ForeignKey(ResourcesData, on_delete=models.PROTECT)
