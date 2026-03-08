from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('therapy', '0009_session_session_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='therapistprofile',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='therapistprofile',
            name='block_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('reviewed', 'Reviewed'), ('resolved', 'Resolved')],
                    default='pending',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='complaint',
                    to='therapy.session',
                )),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='complaints_filed',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('therapist', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='complaints_received',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
