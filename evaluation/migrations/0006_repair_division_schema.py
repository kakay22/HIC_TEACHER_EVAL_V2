
from django.db import migrations


def repair_division_schema(apps, schema_editor):
    connection = schema_editor.connection

    if connection.vendor != "sqlite":
        raise RuntimeError(
            "This repair migration is intended for the "
            "SQLite database. Review it before using another database."
        )

    cursor = connection.cursor()

    tables_and_columns = {
        "evaluation_teacher": "education_level",
        "evaluation_teacherevaluation": "education_level",
        "evaluation_evaluationperiod": "education_level",
    }

    # Add only the columns that are actually missing.
    # Existing records receive the default value COLLEGE.
    for table, column in tables_and_columns.items():
        columns = {
            item.name
            for item in connection.introspection.get_table_description(
                cursor, table
            )
        }

        if column not in columns:
            quoted_table = schema_editor.quote_name(table)
            quoted_column = schema_editor.quote_name(column)

            schema_editor.execute(
                f"ALTER TABLE {quoted_table} "
                f"ADD COLUMN {quoted_column} "
                "varchar(20) NOT NULL DEFAULT 'COLLEGE'"
            )

    # Remove the old constraints that do not account for divisions.
    old_indexes = [
        "evaluation_teacherevaluation_teacher_id_student_id_subject_id_course_id_semester_academic_year_5f94daec_uniq",
        "unique_evaluation_academic_period",
        "only_one_open_evaluation_period",
    ]

    for index_name in old_indexes:
        schema_editor.execute(
            f"DROP INDEX IF EXISTS {schema_editor.quote_name(index_name)}"
        )

    # Add indexes for filtering by division.
    division_indexes = [
        (
            "eval_teacher_level_idx",
            "evaluation_teacher",
        ),
        (
            "eval_teval_level_idx",
            "evaluation_teacherevaluation",
        ),
        (
            "eval_period_level_idx",
            "evaluation_evaluationperiod",
        ),
    ]

    for index_name, table in division_indexes:
        schema_editor.execute(
            f"CREATE INDEX IF NOT EXISTS "
            f"{schema_editor.quote_name(index_name)} "
            f"ON {schema_editor.quote_name(table)} "
            "(education_level)"
        )

    # An evaluation is unique within its division.
    schema_editor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        eval_teval_division_uniq
        ON evaluation_teacherevaluation (
            teacher_id,
            student_id,
            subject_id,
            course_id,
            semester,
            academic_year,
            education_level
        )
        """
    )

    # A division cannot have duplicate periods for the same
    # academic year and semester.
    schema_editor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        unique_division_academic_period
        ON evaluation_evaluationperiod (
            education_level,
            academic_year,
            semester
        )
        """
    )

    # Each division can have at most one open evaluation period.
    schema_editor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        only_one_open_period_per_division
        ON evaluation_evaluationperiod (education_level)
        WHERE is_open = 1
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ("evaluation", "0005_evaluationperiod_and_more"),
    ]

    operations = [
        migrations.RunPython(
            repair_division_schema,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
