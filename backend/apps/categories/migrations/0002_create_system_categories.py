from django.db import migrations

SYSTEM_CATEGORIES = [
    ('Alimentari', '#10B981', 'shopping-cart'),
    ('Trasporti', '#3B82F6', 'car'),
    ('Ristoranti', '#F59E0B', 'utensils'),
    ('Intrattenimento', '#8B5CF6', 'film'),
    ('Salute', '#EF4444', 'heart'),
    ('Shopping', '#EC4899', 'shopping-bag'),
    ('Abbonamenti', '#6366F1', 'repeat'),
    ('Investimenti', '#F97316', 'trending-up'),
    ('Stipendio', '#14B8A6', 'briefcase'),
    ('Trasferimenti', '#06B6D4', 'arrow-right-left'),
    ('Prelievi ATM', '#78716C', 'wallet'),
    ('Cambio Valuta', '#A3E635', 'currency'),
    ('Altro', '#6B7280', 'more-horizontal'),
]


def create_system_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    for name, color, icon in SYSTEM_CATEGORIES:
        Category.objects.create(
            name=name,
            color=color,
            icon=icon,
            is_system=True,
            user=None,
        )


def remove_system_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    Category.objects.filter(is_system=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_system_categories, remove_system_categories),
    ]
