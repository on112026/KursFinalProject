from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_sale_productsale'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]