from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notif_type', models.CharField(
                    choices=[
                        ('session_booked', '📅 Session Booked'),
                        ('session_approved', '✅ Session Approved'),
                        ('session_cancelled', '❌ Session Cancelled'),
                        ('session_completed', '🏁 Session Completed'),
                        ('session_reminder', '⏰ Session Reminder'),
                        ('payment_received', '💰 Payment Received'),
                        ('payment_done', '💳 Payment Done'),
                        ('new_message', '💬 New Message'),
                        ('new_prescription', '📋 New Prescription'),
                        ('review_received', '⭐ Review Received'),
                        ('profile_approved', '🎉 Profile Approved'),
                        ('profile_pending', '🕐 Profile Pending Review'),
                        ('session_join_unlocked', '🔓 Session Unlocked'),
                        ('general', 'ℹ️ General'),
                    ],
                    default='general',
                    max_length=30
                )),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('link', models.CharField(blank=True, max_length=300, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to='auth.user'
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
