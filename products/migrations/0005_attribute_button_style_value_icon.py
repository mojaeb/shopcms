"""Add button_style on attributes and icon on attribute values."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_add_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="productattribute",
            name="button_style",
            field=models.CharField(
                blank=True,
                choices=[
                    ("icon", "فقط آیکون"),
                    ("text", "فقط متن"),
                    ("icon_text", "آیکون + متن"),
                ],
                default="",
                max_length=20,
                verbose_name="سبک دکمه",
            ),
        ),
        migrations.AddField(
            model_name="productattributevalue",
            name="icon",
            field=models.URLField(blank=True, verbose_name="آیکون"),
        ),
        migrations.AlterField(
            model_name="productattribute",
            name="display_type",
            field=models.CharField(
                choices=[
                    ("list", "لیست"),
                    ("select", "انتخاب"),
                    ("color", "رنگ"),
                    ("button", "دکمه"),
                ],
                default="select",
                max_length=20,
                verbose_name="نوع نمایش",
            ),
        ),
    ]
