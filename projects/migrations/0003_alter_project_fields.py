from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_project_participants_alter_project_description_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="participants",
            field=models.ManyToManyField(
                blank=True,
                related_name="participated_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("closed", "Closed"),
                ],
                default="open",
                max_length=6,
            ),
        ),
    ]
