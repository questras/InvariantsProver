# Generated by Django 3.1.7 on 2021-05-02 08:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prover', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sectionstatusdata',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_set', to='prover.sectionstatus'),
        ),
        migrations.CreateModel(
            name='FileProvingResult',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='prover.entity')),
                ('data', models.TextField()),
                ('related_file', models.ForeignKey(help_text='File, to which result relates.', on_delete=django.db.models.deletion.CASCADE, to='prover.file')),
            ],
            bases=('prover.entity',),
        ),
    ]
