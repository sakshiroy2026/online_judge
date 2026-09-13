from django.db import migrations, models


def backfill_is_solved(apps, schema_editor):
    """Existing rows predate the is_solved flag. A row is a genuine solve only if
    the user has a 100% submission for that question; anything else was a favorite."""
    UserSolvedQuestion = apps.get_model("dashboard", "UserSolvedQuestion")
    CodeSubmission = apps.get_model("compile", "CodeSubmission")

    for row in UserSolvedQuestion.objects.all():
        solved = CodeSubmission.objects.filter(
            user_id=row.user_id, question_id=row.question_id, score=100
        ).exists()
        if solved:
            row.is_solved = True
            row.save(update_fields=["is_solved"])


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_usersolvedquestion_delete_userquestionstatus"),
        ("compile", "0002_codesubmission_question_codesubmission_score_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersolvedquestion",
            name="is_solved",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_is_solved, migrations.RunPython.noop),
    ]