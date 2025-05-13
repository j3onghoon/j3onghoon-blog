from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone


class TimeStampedModel(models.Model):
    created = models.DateTimeField(_("생성 일시"), default=timezone.now, editable=False)
    updated = models.DateTimeField(_("수정 일시"), auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def delete(self):
        return self.update(is_active=False, deleted=timezone.now)

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(is_active=True, deleted=None)


class ActiveManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()

    def inactive(self):
        return self.model.all_objects.get_queryset().inactive()

    def delete(self):
        return self.get_queryset().delete()

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def inactive(self):
        return self.get_queryset().inactive()

    def restore(self):
        return self.get_queryset().restore()

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(_("활성 상태"), default=True)
    deleted = models.DateTimeField(_("삭제 일시"), null=True, blank=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.deleted = timezone.now()
        self.save(using=using, update_fields=['is_active', 'deleted'])

    def restore(self):
        self.is_active = True
        self.deleted = None
        self.save(update_fields=["is_active", "deleted"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, SoftDeleteModel):
    class Meta:
        abstract = True
