"""Flask CLI commands: flask init-db, seed-db, check-model, reprocess."""

import click
from flask import current_app
from flask.cli import with_appcontext

from app.extensions import db
from app.inference.registry import get_detector
from app.models import Inspection, InspectionStatus
from app.seed import seed_damage_types
from app.tasks.inspection_job import process_inspection
from app.utils.identifiers import parse_uuid_or_404


def register_cli(app) -> None:
    for command in (init_db, seed_db, check_model, reprocess):
        app.cli.add_command(command)


@click.command("init-db")
@click.option("--seed/--no-seed", default=True, help="Also write the damage_types rows.")
@with_appcontext
def init_db(seed: bool):
    """Create any missing tables, then seed the lookup data.

    This is the whole schema story for this project: the models are the single
    source of truth and there is no migration history to keep in step with them.
    Existing tables are left untouched, so it is safe to re-run.
    """
    db.create_all()
    click.echo("Schema created (existing tables left as they are).")

    if seed:
        click.echo(f"Seeded {seed_damage_types(current_app)} damage types.")


@click.command("seed-db")
@with_appcontext
def seed_db():
    """Insert or update the six damage_types rows."""
    click.echo(f"Seeded {seed_damage_types(current_app)} damage types.")


@click.command("check-model")
@with_appcontext
def check_model():
    """Load the configured model and print what it can detect.

    Quickest way to confirm MODEL_PATH and MODEL_BACKEND are right before
    submitting a real inspection.
    """
    detector = get_detector(current_app.config)
    click.echo(f"Backend      : {detector.backend_name}")
    click.echo(f"Model path   : {detector.model_path or '(none)'}")
    click.echo(f"Input size   : {detector.input_size}")
    click.echo(f"Confidence   : {detector.confidence_threshold}")

    names = getattr(detector, "class_names", None)
    if names:
        click.echo("Classes      :")
        for index, label in sorted(names.items()):
            click.echo(f"  {index}: {label}")


@click.command("reprocess")
@click.argument("inspection_id")
@with_appcontext
def reprocess(inspection_id: str):
    """Re-run the model over an existing inspection (e.g. after a model update)."""
    inspection = db.session.get(Inspection, parse_uuid_or_404(inspection_id, "Inspection"))
    if inspection is None:
        raise click.ClickException(f"No inspection with id {inspection_id}")

    # Clear the previous findings so the re-run does not stack on top of them.
    for detection in list(inspection.detections):
        db.session.delete(detection)
    inspection.status = InspectionStatus.QUEUED
    db.session.commit()

    process_inspection(inspection_id)
    click.echo(f"Reprocessed {inspection_id}: status={inspection.status}")
