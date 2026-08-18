from app.core.celery_app import app


def test_worker_registers_application_tasks():
    app.loader.import_default_modules()

    expected_tasks = {
        'app.tasks.achievement.check_achievements_after_approval',
        'app.tasks.cleanup.gc_orphan_files',
        'app.tasks.content_extract.extract_material_content_to_es',
        'app.tasks.counter_sync.sync_download_counters',
        'app.tasks.index_sync.sync_material_to_es',
        'app.tasks.link_check.check_dead_links',
        'app.tasks.material_tasks.generate_thumbnail',
        'app.tasks.material_tasks.pre_screen_content',
        'app.tasks.material_tasks.virus_scan',
    }

    assert expected_tasks <= set(app.tasks)
