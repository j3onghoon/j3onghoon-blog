import mimetypes
import logging

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone


BYTE_SCALE = 1024

BYTE = "B"
KILOBYTE = "KB"
MEGABYTE = "MB"
GIGABYTE = "GB"
TERABYTE = "TB"

SIZE_UNITS = (BYTE, KILOBYTE, MEGABYTE, GIGABYTE, TERABYTE)
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"]
VIDEO_EXTENSIONS = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf']
AUDIO_EXTENSIONS = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']


class FileType(models.TextChoices):
    IMAGE = "image", _("이미지")
    VIDEO = "video", _("동영상")
    DOCUMENT = "document", _("문서")
    AUDIO = "audio", _("오디오")
    OTHER = "other", _("기타")


EXTENSION_TO_FILE_TYPE = {ext: FileType.IMAGE for ext in IMAGE_EXTENSIONS}
EXTENSION_TO_FILE_TYPE.update({ext: FileType.VIDEO for ext in VIDEO_EXTENSIONS})
EXTENSION_TO_FILE_TYPE.update({ext: FileType.DOCUMENT for ext in DOCUMENT_EXTENSIONS})
EXTENSION_TO_FILE_TYPE.update({ext: FileType.AUDIO for ext in AUDIO_EXTENSIONS})


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


class Attachment(BaseModel):
    file = models.FileField(_("파일"), max_length=255)
    name = models.CharField(_("파일명"), max_length=255, blank=True)
    file_type = models.CharField(_("파일 유형"), max_length=20, choices=FileType.choices, default=FileType.OTHER)
    mime_type = models.CharField(_("MIME 유형"), max_length=100, blank=True)
    size = models.PositiveIntegerField(_("파일 크기(바이트)"), default=0)
    description = models.TextField(_("설명"), blank=True)
    order = models.PositiveIntegerField(_("정렬 순서"), default=0)

    content_type = models.ForeignKey("ContentType", on_delete=models.CASCADE, verbose_name=_("콘텐츠 타입"))
    object_id = models.PositiveIntegerField(_("객체 ID"))
    content_object = GenericForeignKey("content_type", "object_id")

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordereing = ["content_type", "object_id", "order"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["file_type"])
        ]

    def __str__(self):
        if self.name:
            return self.name
        elif self.file and (filename := getattr(self.file, "name", "")):
            return filename.split("/")[-1]
        return ""

    @property
    def extension(self):
        if not self.file:
            return ""
        return self.file.name.split(".")[-1].lower() if "." in self.file.name else ""

    @property
    def formatted_size(self):
        size = self.size
        for unit in SIZE_UNITS:
            if size < BYTE_SCALE or unit == TERABYTE:
                return f"{size:.2f} {unit}" if unit != BYTE else f"{size} {unit}"
            size /= BYTE_SCALE

    def save(self, *args, **kwargs):
        if not self.file:
            return super().save(*args, **kwargs)

        if not self.name:
            self.name = self.file.name.split("/")[-1]

        if (file_size := getattr(self.file, "size", 0)) > 0:
            self.size = file_size

        if not self.file_type:
            self.file_type = EXTENSION_TO_FILE_TYPE.get(self.extension, FileType.OTHER)

        if not self.mime_type:
            self.mime_type = mimetypes.guess_type(self.file.name)[0]

        super().save(*args, **kwargs)

    def hard_delete(self, using=None, keep_parents=False):
        storage = self.file.storage
        if storage and self.file:
            try:
                storage.delete(self.file.name)
            except Exception as e:
                file_path = self.file.name if self.file else "알 수 없음"
                error_msg = f"파일 삭제 실패 (ID: {self.pk}, 파일: {file_path}: {str(e)}"
                logging.error(error_msg)
                raise Exception(f"첨부 파일 삭제 실패: {str(e)}")

        return super().hard_delete(using=using, keep_parents=keep_parents)


class AttachmentMixin(models.Model):
    attachments = GenericRelation("Attachment")

    class Meta:
        abstract = True

    def add_attachment(self, file, **kwargs):
        return Attachment.objects.create(
            file=file,
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            **kwargs,
        )

    def get_attachments_by_type(self, file_type=None):
        attachments = self.attachments.all()

        if file_type:
            return attachments.filter(file_type=file_type)

        return attachments

    @property
    def images(self):
        return self.get_attachments_by_type(FileType.IMAGE)

    @property
    def videos(self):
        return self.get_attachments_by_type(FileType.VIDEO)

    @property
    def documents(self):
        return self.get_attachments_by_type(FileType.DOCUMENT)

    @property
    def audios(self):
        return self.get_attachments_by_type(FileType.AUDIO)



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValidationError(_("이메일 주소는 필수입니다."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValidationError(_('superuser는 is_staff=True 이어야 합니다.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError(_('superuser는 is_superuser=True 이어야 합니다.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(
        _("사용자명"),
        max_length=150,
        blank=True,
        null=True
    )
    email = models.EmailField(
        _("이메일"),
        unique=True,
    )
    phone = models.CharField(_("휴대폰"), max_length=20, blank=True)
    birth_datetime = models.DateTimeField(_("생년월일시"), null=True, blank=True)


