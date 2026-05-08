from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cluster_key', models.CharField(max_length=64)),
                ('decision', models.CharField(choices=[('CONFIRMED', 'Confirmed'), ('REJECTED', 'Rejected')], max_length=20)),
                ('canonical_merchant_override', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_overrides', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'subscription_overrides',
                'unique_together': {('user', 'cluster_key')},
            },
        ),
        migrations.AddIndex(
            model_name='subscriptionoverride',
            index=models.Index(fields=['user', 'cluster_key'], name='subscriptio_user_id_4a1b9c_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptionoverride',
            index=models.Index(fields=['user', 'decision'], name='subscriptio_user_id_4e52d6_idx'),
        ),
    ]

