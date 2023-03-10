# Generated by Django 4.1.7 on 2023-03-09 17:21

from django.db import migrations
from django.core.exceptions import ObjectDoesNotExist

INITIAL_TAGS = [
    {'name': 'Завтрак', 'color': '#F39C12', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#ff0000', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#00BFFF', 'slug': 'dinner'},
]


def add_tags(apps, schema_editor):
    tag_model = apps.get_model('recipes', 'Tag')
    for tag in INITIAL_TAGS:
        new_tag = tag_model(**tag)
        new_tag.save()


def remove_tags(apps, schema_editor):
    tag_model = apps.get_model('recipes', 'Tag')
    for tag in INITIAL_TAGS:
        try:
            tag_model.objects.get(**tag).delete()
        except ObjectDoesNotExist:
            print(f"Tag {tag.get('name')} doesn't exists. Skipped.")


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_load_ingredients'),
    ]

    operations = [
        migrations.RunPython(add_tags, remove_tags)
    ]
