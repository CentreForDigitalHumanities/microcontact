"""Exercise demo data with real signals, media files, API uploads and admin."""

import io
import os
import subprocess
from importlib import import_module

import pytest
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from .demo_data import PLACE_PREFIX, SOURCE_PREFIX
from .management.commands import seed_demo_data
from .models import AgeCategory, Country, Dialect, Language, Place, Recording


def seed(**options):
    output = io.StringIO()
    call_command('seed_demo_data', stdout=output, **options)
    return output.getvalue()


@pytest.fixture
def seeded(app_data):
    seed()


def media_snapshot(directory):
    return {os.path.join(root, name): os.stat(os.path.join(root, name)).st_mtime_ns
            for root, _, names in os.walk(directory) for name in names}


def upload_payload(place, country=None):
    sample = Recording.objects.get(recording_original_datasource__contains='luca-toronto')
    with sample.recording.storage.open(sample.recording.name, 'rb') as audio:
        upload = SimpleUploadedFile('new-contribution.mp3', audio.read(), 'audio/mpeg')
    return {
        'name': 'Test contributor', 'email': 'contributor@example.invalid', 'phone': '',
        'dialect': sample.dialect_id, 'languages': list(sample.languages.values_list('pk', flat=True)),
        'age': sample.age_id, 'sex': Recording.FEMALE, 'education': Recording.UNIVERSITY_EDU,
        'generation': Recording.SECOND_GEN, 'recording': upload,
        'place.placeID': place.placeID, 'place.name': place.name,
        'place.country': country or place.country.code,
        'place.latitude': place.latitude, 'place.longitude': place.longitude,
    }


def test_seed_uses_migrated_references_and_valid_profiles(app_data):
    reference_counts = [model.objects.count() for model in (Country, Dialect, Language, AgeCategory)]
    assert '15 created, 0 kept' in seed()
    assert reference_counts == [model.objects.count() for model in (Country, Dialect, Language, AgeCategory)]
    assert Recording.objects.count() == 15
    assert Recording.objects.filter(public=True).count() == 12
    assert Place.objects.count() == 8
    assert set(Recording.objects.values_list('place__country__code', flat=True)) == {'AR', 'BR', 'CA', 'IT', 'US'}
    assert Recording.objects.values('dialect').distinct().count() == 9
    assert set(Recording.objects.filter(public=False).values_list('status', flat=True)) == {'a', 'b', 'c'}
    for recording in Recording.objects.all():
        recording.full_clean()
        assert recording.email.endswith('@example.invalid')
        assert recording.recording_original_datasource.startswith(SOURCE_PREFIX)
        assert recording.recording.storage.exists(recording.recording.name)
        assert recording.get_web_recording().name.endswith('.mp3')
        assert recording.get_web_recording().size > 0
        assert recording.languages.exists()
    wav = Recording.objects.filter(recording__endswith='.wav').first()
    assert wav.recording_web
    mp3 = Recording.objects.get(recording__endswith='.mp3')
    assert not mp3.recording_web
    assert mp3.get_web_recording() == mp3.recording
    # Decode both paths used by browser playback, without mocking ffmpeg.
    for recording in (wav, mp3):
        subprocess.check_call(['ffmpeg', '-v', 'error', '-i', recording.get_web_recording().path,
                               '-f', 'null', '-'])


def test_public_api_and_media(seeded, client, settings):
    # Django builds static media routes at URL import time. Point them at this
    # test's media directory and enable the same DEBUG-only serving as runserver.
    settings.DEBUG = True
    app_patterns = import_module(settings.ROOT_URLCONF).urlpatterns

    class MediaURLs:
        urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + app_patterns

    settings.ROOT_URLCONF = MediaURLs
    public_ids = set(Recording.objects.filter(public=True).values_list('pk', flat=True))
    recordings = client.get('/api/recordings/').json()
    assert {row['id'] for row in recordings} == public_ids
    for row in recordings:
        assert not {'name', 'email', 'phone', 'relation_to_speaker', 'generation'} & set(row)
        response = client.get(row['recording_web'])
        assert response.status_code == 200
        assert b''.join(response.streaming_content)
        response.close()
    places = client.get('/api/places/').json()
    assert {r['id'] for place in places for r in place['recordings']} == public_ids
    assert sum(bool(place['recordings']) for place in places) == 7
    assert next(p for p in places if p['name'] == 'Caxias do Sul')['recordings'] == []
    for private in Recording.objects.filter(public=False):
        assert client.get('/api/recordings/{}/'.format(private.pk)).status_code == 404
    # OPEN + public is deliberately visible; REVIEWED + private stays hidden.
    assert Recording.objects.get(public=True, status=Recording.OPEN).pk in public_ids


def test_rerun_preserves_edits_ids_and_files(seeded, settings):
    recording = Recording.objects.first()
    Recording.objects.filter(pk=recording.pk).update(public=False, name='Edited demo')
    ids = list(Recording.objects.values_list('pk', flat=True))
    before = media_snapshot(settings.MEDIA_ROOT)
    assert '0 created, 15 kept' in seed()
    assert list(Recording.objects.values_list('pk', flat=True)) == ids
    assert media_snapshot(settings.MEDIA_ROOT) == before
    recording.refresh_from_db()
    assert recording.name == 'Edited demo'
    assert not recording.public
    assert Place.objects.count() == 8


def test_reset_preserves_real_upload_and_reuses_places(seeded, settings):
    place = Place.objects.get(placeID=PLACE_PREFIX + 'toronto')
    response = APIClient().post('/api/recordings/', upload_payload(place), format='multipart')
    assert response.status_code == 201, response.data
    real = Recording.objects.get(pk=response.data['id'])
    old_demo_paths = set(media_snapshot(settings.MEDIA_ROOT)) - {real.recording.path}
    assert '15 created, 0 kept' in seed(reset=True)
    real.refresh_from_db()
    assert real.recording.storage.exists(real.recording.name)
    assert real.place_id == place.pk
    assert Recording.objects.count() == 16
    assert Place.objects.count() == 8
    assert not any(os.path.exists(path) for path in old_demo_paths)


def test_upload_review_publish_and_withdraw(seeded, client):
    place = Place.objects.get(placeID=PLACE_PREFIX + 'toronto')
    payload = upload_payload(place)
    payload['public'] = True  # the public upload API must ignore this
    response = APIClient().post('/api/recordings/', payload, format='multipart')
    assert response.status_code == 201, response.data
    recording = Recording.objects.get(pk=response.data['id'])
    assert recording.status == Recording.OPEN and not recording.public
    assert recording.place_id == place.pk
    assert Place.objects.count() == 8
    detail_url = '/api/recordings/{}/'.format(recording.pk)
    assert client.get(detail_url).status_code == 404

    admin = get_user_model().objects.create_superuser('reviewer', 'reviewer@example.invalid', 'test-password')
    client.force_login(admin)
    change_url = '/admin/recordings/recording/{}/change/'.format(recording.pk)
    assert client.get(change_url).status_code == 200
    form = {
        'status': Recording.REVIEWED, 'public': 'on', 'name': recording.name,
        'email': recording.email, 'phone': '', 'dialect': recording.dialect_id, 'place': place.pk,
        'age': recording.age_id, 'sex': recording.sex, 'education': recording.education,
        'generation': recording.generation,
        'languages': list(recording.languages.values_list('pk', flat=True)), '_save': 'Save',
    }
    response = client.post(change_url, form)
    assert response.status_code == 302
    recording.refresh_from_db()
    assert recording.status == Recording.REVIEWED and recording.public
    client.logout()
    assert client.get(detail_url).status_code == 200
    nested = client.get('/api/places/{}/'.format(place.pk)).json()['recordings']
    assert recording.pk in {row['id'] for row in nested}

    client.force_login(admin)
    form.pop('public')
    assert client.post(change_url, form).status_code == 302
    client.logout()
    assert client.get(detail_url).status_code == 404


def test_upload_new_italian_place_forces_first_generation(seeded):
    place = Place(placeID='test-new-italian-place', name='Test town', latitude=45, longitude=9)
    response = APIClient().post('/api/recordings/', upload_payload(place, country='IT'), format='multipart')
    assert response.status_code == 201, response.data
    recording = Recording.objects.get(pk=response.data['id'])
    assert recording.generation == Recording.FIRST_GEN
    assert recording.place.country.code == 'IT'
    assert Place.objects.count() == 9


def test_upload_requires_contact_details(seeded):
    place = Place.objects.get(placeID=PLACE_PREFIX + 'toronto')
    payload = upload_payload(place)
    payload.pop('email')
    response = APIClient().post('/api/recordings/', payload, format='multipart')
    assert response.status_code == 400
    assert 'non_field_errors' in response.data
    assert Recording.objects.count() == 15


def test_missing_reference_data_fails_before_writes(app_data):
    Dialect.objects.all().delete()
    with pytest.raises(CommandError, match='reference data'):
        seed()
    assert not Recording.objects.exists()
    assert not Place.objects.exists()


def test_missing_ffmpeg_cannot_reset_existing_demo(seeded, settings, monkeypatch):
    before = media_snapshot(settings.MEDIA_ROOT)
    ids = list(Recording.objects.values_list('pk', flat=True))
    monkeypatch.setattr(seed_demo_data.shutil, 'which', lambda name: None)
    with pytest.raises(CommandError, match='ffmpeg is required'):
        seed(reset=True)
    assert list(Recording.objects.values_list('pk', flat=True)) == ids
    assert media_snapshot(settings.MEDIA_ROOT) == before


def test_conversion_failure_rolls_back_record_and_cleans_files(app_data, settings, monkeypatch):
    from . import signals

    def fail_conversion(path):
        with open(os.path.splitext(path)[0] + '.mp3', 'wb') as partial:
            partial.write(b'incomplete')
        raise RuntimeError('Conversion failed')

    monkeypatch.setattr(signals, 'convert_to_mp3', fail_conversion)
    with pytest.raises(CommandError, match='Could not seed'):
        seed()
    assert not Recording.objects.exists()
    assert not media_snapshot(settings.MEDIA_ROOT)
