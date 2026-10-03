from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0002_shortcode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="banner",
            name="image",
            field=models.CharField(blank=True, max_length=500, verbose_name="تصویر"),
        ),
    ]
