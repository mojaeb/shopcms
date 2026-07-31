"""Widen color_code to store multiple hex values per option."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0005_attribute_button_style_value_icon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productattributevalue",
            name="color_code",
            field=models.CharField(
                blank=True,
                help_text="یک یا چند رنگ با ویرگول؛ مثال: #111111,#c0c0c0",
                max_length=120,
                verbose_name="کد رنگ",
            ),
        ),
    ]
