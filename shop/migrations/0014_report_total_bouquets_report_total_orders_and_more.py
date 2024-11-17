# Generated by Django 5.1.3 on 2024-11-15 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_reportparameter_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='total_bouquets',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество букетов'),
        ),
        migrations.AddField(
            model_name='report',
            name='total_orders',
            field=models.PositiveIntegerField(default=0, verbose_name='Общее количество заказов'),
        ),
        migrations.AddField(
            model_name='report',
            name='total_revenue',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Общая выручка'),
        ),
        migrations.AlterField(
            model_name='report',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='reports/', verbose_name='Файл отчета'),
        ),
    ]
