"""Create repeatable demo data through the normal recording save signals."""

import io
import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recordings.demo_data import PLACES, PROFILES, PLACE_PREFIX, source_label
from recordings.models import AgeCategory, Country, Dialect, Language, Place, Recording


def make_audio():
    """Generate two seconds of quiet tones and preflight the MP3 encoder."""
    if not shutil.which('ffmpeg'):
        raise CommandError('ffmpeg is required to seed playable demo recordings.')
    buffer = io.BytesIO()
    rate = 16000
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b''.join(
            struct.pack('<h', int(2500 * math.sin(
                2 * math.pi * (440 if frame < rate else 660) * frame / rate
            ))) for frame in range(2 * rate)
        ))
    wav = buffer.getvalue()
    with tempfile.TemporaryDirectory(prefix='microcontact-demo-') as directory:
        wav_path = os.path.join(directory, 'demo.wav')
        mp3_path = os.path.join(directory, 'demo.mp3')
        with open(wav_path, 'wb') as audio:
            audio.write(wav)
        try:
            subprocess.run(
                ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', wav_path,
                 '-acodec', 'mp3', '-ac', '1', '-ab', '128k', mp3_path],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise CommandError('Cannot generate demo MP3 audio: {}'.format(error))
        with open(mp3_path, 'rb') as audio:
            return {'wav': wav, 'mp3': audio.read()}


class Command(BaseCommand):
    help = 'Seed fictional speakers, map locations and synthetic audio for local testing.'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete and recreate only the tagged demo recordings and their audio.',
        )

    def handle(self, *args, **options):
        # Resolve everything before writing or resetting anything. Migrations
        # own the reference lists; seeding must not duplicate or overwrite them.
        try:
            countries = {row[2]: Country.objects.get(code=row[2]) for row in PLACES}
            dialects = {p['dialect']: Dialect.objects.get(it=p['dialect']) for p in PROFILES}
            languages = {name: Language.objects.get(it=name)
                         for p in PROFILES for name in p['languages']}
            ages = {p['age']: AgeCategory.objects.get(least=p['age'][0], greatest=p['age'][1])
                    for p in PROFILES}
        except (ObjectDoesNotExist, MultipleObjectsReturned) as error:
            raise CommandError(
                'Expected reference data is missing or ambiguous. Run migrate and '
                'check countries, dialects, languages and ages. {}'.format(error)
            )

        existing = Recording.objects.filter(
            recording_original_datasource__in=[source_label(p) for p in PROFILES],
        )
        labels = set(existing.values_list('recording_original_datasource', flat=True))
        pending = [p for p in PROFILES if options['reset'] or source_label(p) not in labels]
        # Test ffmpeg before a reset removes any existing files.
        audio = make_audio() if pending else {}
        if options['reset']:
            existing.delete()  # post_delete removes originals and converted MP3s

        places = {}
        for slug, name, code, latitude, longitude in PLACES:
            places[slug], _ = Place.objects.get_or_create(
                placeID=PLACE_PREFIX + slug,
                defaults=dict(name=name, country=countries[code],
                              latitude=latitude, longitude=longitude),
            )

        for profile in pending:
            fields = dict(profile)
            slug = fields.pop('slug')
            extension = fields.pop('extension', 'wav')
            fields['place'] = places[fields['place']]
            fields['dialect'] = dialects[fields['dialect']]
            fields['age'] = ages[fields['age']]
            spoken = [languages[name] for name in fields.pop('languages')]
            fields['name'] = 'Demo: ' + fields['name']
            fields['email'] = slug + '@example.invalid'
            fields.setdefault('status', Recording.REVIEWED)
            fields.setdefault('public', True)
            fields['recording_original_datasource'] = source_label(profile)
            fields['recording'] = ContentFile(audio[extension], name='demo/{}.{}'.format(slug, extension))
            recording = Recording(**fields)
            try:
                # Keep each completed profile on failure so a rerun can resume.
                # Files need explicit cleanup because DB rollback cannot do it.
                with transaction.atomic():
                    recording.full_clean()
                    recording.save()
                    recording.languages.set(spoken)
            except Exception as error:
                if recording.recording._committed:
                    storage = recording.recording.storage
                    storage.delete(recording.recording.name)
                    if extension == 'wav':
                        storage.delete(os.path.splitext(recording.recording.name)[0] + '.mp3')
                raise CommandError('Could not seed {}: {}'.format(slug, error))

        self.stdout.write(self.style.SUCCESS(
            'Demo data: {} created, {} kept; {} demo recordings total.'.format(
                len(pending), len(PROFILES) - len(pending), len(PROFILES),
            )
        ))
        self.stdout.write(
            'Open /#contributions for public recordings and /admin/recordings/recording/ '
            'for moderation. Audio contains synthetic tones, not speech.'
        )
