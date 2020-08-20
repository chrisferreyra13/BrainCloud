# Generated by Django 3.0.7 on 2020-08-11 21:22

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import filemanager.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryUploadChunked',
            fields=[
                ('upload_id', models.CharField(max_length=22, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(22)])),
                ('file_id', models.CharField(max_length=22, validators=[django.core.validators.MinLengthValidator(22)])),
                ('upload_dir', models.CharField(default=models.CharField(max_length=22, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(22)]), max_length=512)),
                ('last_chunk', models.IntegerField(default=0)),
                ('offset', models.IntegerField(default=0)),
                ('total_size', models.IntegerField(default=0)),
                ('upload_name', models.CharField(default='', max_length=512)),
                ('upload_complete', models.BooleanField(default=False)),
                ('last_upload_time', models.DateTimeField(auto_now=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TemporaryUpload',
            fields=[
                ('upload_id', models.CharField(max_length=22, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(22)])),
                ('file_id', models.CharField(max_length=22, validators=[django.core.validators.MinLengthValidator(22)])),
                ('file', models.FileField(storage=filemanager.models.FileManagerUploadSystemStorage(), upload_to=filemanager.models.get_upload_path)),
                ('upload_name', models.CharField(max_length=512)),
                ('uploaded', models.DateTimeField(auto_now_add=True)),
                ('upload_type', models.CharField(choices=[('F', 'Uploaded file data'), ('U', 'Remote file URL')], max_length=1)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StoredUpload',
            fields=[
                ('upload_id', models.CharField(max_length=22, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(22)])),
                ('file', models.FileField(max_length=2048, storage=filemanager.models.FileManagerLocalStoredStorage(), upload_to='')),
                ('uploaded', models.DateTimeField()),
                ('stored', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
