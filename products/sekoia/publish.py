import shutil
from uuid import uuid4
from meshroom.model import Integration
from meshroom.decorators import publish


@publish(role="consumer", topic="events")
def publish_intake_format(integration: Integration):
    """
    Publish an intake format as a PR to Sekoia.io's https://github.com/SEKOIA-IO/intake-formats opensource repo

    We proceed by cloning the intake-formats repo to a tmp_path, copying the intake format files to it and pushing to a branch
    """
    from meshroom.git import Git
    from meshroom.model import get_project_dir
    from meshroom.template import generate_files_from_template

    name = integration.target_product
    module_name = name

    intake_formats_path = get_project_dir() / "mirrors" / integration.product / "intake-formats"
    path = integration.path.parent / "dist" / "formats" / name
    tmp_path = path / f"tmp-{uuid4()}"
    Git(intake_formats_path).pull("https://github.com/SEKOIA-IO/intake-formats.git")

    if Git(path).push(True, ".", f"Update {name} intake format"):
        print(f"Intake format {name} successfully pushed to git repo")
    else:
        print(f"Intake format {name} is up-to-date in git repo")

    # Clone intake-formats' main branch to tmp_path pointing to our project's remote
    Git(tmp_path).pull(intake_formats_path)
    Git(tmp_path).create_branch(f"intake-format-{name}")
    Git(tmp_path).remove_remote("origin")
    Git(tmp_path).add_remote("origin", Git(path).get_remote())

    # Scaffold a dummy module from templates/intake_format_module
    generate_files_from_template(
        integration.get_product().path / "templates/intake_format_module",
        tmp_path / module_name,
        {
            "{{UUID}}": integration.intake_format_uuid,
            "{{NAME}}": name,
        },
    )

    # Copy intake-format files
    for d in ("_meta", "ingest"):
        if (path / d).exists():
            shutil.copytree(path / d, tmp_path / module_name / name / d)

    # Push the changes to the remote branch
    print(Git(tmp_path).get_updated_files())
    Git(tmp_path).push(True, ".", f"Publish {name} intake format", remote="origin")

    # TODO : Print link to create PR from {branch} to intake-formats' main branch
    print("Open a browser to\nhttps://TODO.com\nTo create a PR to SEKOIA-IO/intake-formats")

    # Clean up tmp_path
    shutil.rmtree(tmp_path)

    # Pull intakes also involve an automation connector, let's publish a PR for it too
    if integration.mode == "pull":
        publish_automation_connector(integration)


def publish_automation_connector(integration: Integration):
    """Publish an automation connector as a PR to Sekoia.io's https://github.com/SEKOIA-IO/automation-library"""
    from meshroom.git import Git
    from meshroom.model import get_project_dir

    name = integration.target_product

    automation_library_path = get_project_dir() / "mirrors" / integration.product / "intake-formats"
    path = integration.path.parent / "dist" / "formats" / name
    dst_path = path / name
    Git(automation_library_path).pull("https://github.com/SEKOIA-IO/automation-library.git")

    path = integration.path.parent / "dist" / "formats" / name
    if Git(path).push(True, ".", f"Update {name} automation module"):
        print(f"Automation module {name} successfully pushed to git repo")
    else:
        print(f"Automation module {name} is up-to-date in git repo")

    # Create a local branch to merge our changes into intake-format's git history
    old_branch = Git(path).get_branch()
    branch = uuid4().hex[:4] + "-" + integration.target_product

    # Get rid of intake-format specific files
    shutil.rmtree(path / "_meta")
    shutil.rmtree(path / "_ingest")

    # Move files to their destination module's directory
    dst_path.mkdir(parents=True, exist_ok=True)
    for item in path.iterdir():
        if item.name != dst_path.name and item.name != ".git":
            shutil.move(item, dst_path / item.name)

    # Copy automation-library's main branch to a new local branch
    Git(automation_library_path).copy_branch(Git(automation_library_path).get_branch(), path, branch)
    Git(path).branch(branch)
    Git(path).push(True, ".", f"Publish {name} connector")

    # TODO : Print link to create PR from {branch} to automation-library' main branch
    print("Open a browser to\nhttps://TODO.com\nTo create a PR to SEKOIA-IO/automation-library")

    # Switch back to the original branch
    Git(path).branch(old_branch)
