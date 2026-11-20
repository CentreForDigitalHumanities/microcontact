"""Fictional profiles for the project's 2018-era research workflow.

The source labels and place IDs are reserved for seed_demo_data. Names and
contact details are invented; coordinates describe real cities. Audio is
generated separately and contains tones, not dialect speech.
"""

SOURCE_PREFIX = 'Microcontact demo v1: '
PLACE_PREFIX = 'microcontact-demo-v1-'

# slug, display name, country code, latitude, longitude
PLACES = (
    ('buenos-aires', 'Buenos Aires', 'AR', -34.6037, -58.3816),
    ('sao-paulo', 'São Paulo', 'BR', -23.5505, -46.6333),
    ('toronto', 'Toronto', 'CA', 43.6532, -79.3832),
    ('montreal', 'Montréal', 'CA', 45.5017, -73.5673),
    ('new-york', 'New York', 'US', 40.7128, -74.0060),
    ('naples', 'Napoli', 'IT', 40.8518, 14.2681),
    ('siena', 'Siena', 'IT', 43.3188, 11.3308),
    ('caxias-do-sul', 'Caxias do Sul', 'BR', -29.1678, -51.1794),
)

# Use the Italian reference names installed by the data migrations, not PKs.
# Field values use Recording's existing choice codes. Omitted values default
# to reviewed/public, self-uploaded, and WAV audio in the command.
PROFILES = (
    dict(
        slug='rosa-buenos-aires', name='Rosa Esposito', place='buenos-aires',
        dialect='Napoletano (Campano)', languages=('italiano', 'spagnolo'),
        age=(66, 70), sex='b', education='e', generation='a',
        origin='Caserta, CE', migrated=1956,
    ),
    dict(
        slug='marco-buenos-aires', name='Marco Ferrero', place='buenos-aires',
        dialect='Piemontese', languages=('spagnolo',),
        age=(46, 50), sex='a', education='u', generation='b',
    ),
    dict(
        slug='lucia-buenos-aires', name='Lucia Greco', place='buenos-aires',
        dialect='Salentino', languages=('italiano', 'spagnolo'),
        age=(61, 65), sex='b', education='m', generation='a',
        origin='Nardò, LE', migrated=1962,
    ),
    dict(
        slug='antonio-sao-paulo', name='Antonio Bortolotto', place='sao-paulo',
        dialect='Veneto', languages=('italiano', 'portoghese'),
        age=(71, 75), sex='a', education='e', generation='a',
        origin='Bassano del Grappa, VI', migrated=1958,
        relation_to_speaker='Grandson',
    ),
    dict(
        slug='elena-sao-paulo', name='Elena Romano', place='sao-paulo',
        dialect='Palermitano (Siciliano)', languages=('portoghese', 'italiano'),
        age=(56, 60), sex='b', education='h', generation='b',
    ),
    dict(
        slug='anna-toronto', name='Anna Di Carlo', place='toronto',
        dialect='Abruzzese/Teatino', languages=('italiano', 'inglese'),
        age=(66, 70), sex='b', education='m', generation='a',
        origin='Chieti, CH', migrated=1964,
    ),
    dict(
        slug='luca-toronto', name='Luca Russo', place='toronto',
        dialect='Napoletano (Campano)', languages=('inglese', 'italiano'),
        age=(31, 35), sex='a', education='u', generation='b',
        extension='mp3',
    ),
    dict(
        slug='paolo-montreal', name='Paolo Costa', place='montreal',
        dialect='Palermitano (Siciliano)',
        languages=('italiano', 'francese', 'inglese'),
        age=(61, 65), sex='a', education='h', generation='a',
        origin='Monreale, PA', migrated=1972,
    ),
    dict(
        slug='sofia-new-york', name='Sofia Conti', place='new-york',
        dialect='Fiorentino', languages=('italiano', 'inglese'),
        age=(56, 60), sex='b', education='u', generation='a',
        origin='Fiesole, FI', migrated=1988,
    ),
    dict(
        slug='alex-new-york', name='Alex Moretti', place='new-york',
        dialect='altro', languages=('inglese', 'altro'),
        age=(26, 30), sex='c', education='u', generation='b', status='c',
    ),
    dict(
        slug='giuseppe-naples', name='Giuseppe De Luca', place='naples',
        dialect='Napoletano (Campano)', languages=('italiano',),
        age=(76, 80), sex='a', education='e', generation='a',
        origin='Napoli, NA', relation_to_speaker='Daughter',
    ),
    dict(
        slug='maria-siena', name='Maria Neri', place='siena',
        dialect='Senese (Toscano)', languages=('italiano',),
        age=(51, 55), sex='b', education='h', generation='a',
        origin='Siena, SI',
    ),
    dict(
        slug='pending-toronto', name='Giulia Zanetti', place='toronto',
        dialect='Veneto', languages=('inglese',),
        age=(18, 25), sex='b', education='h', generation='b',
        status='c', public=False,
    ),
    dict(
        slug='private-buenos-aires', name='Carlo Gallo', place='buenos-aires',
        dialect='Piemontese', languages=('italiano', 'spagnolo'),
        age=(81, 85), sex='a', education='e', generation='a',
        origin='Alba, CN', migrated=1950, public=False,
    ),
    dict(
        slug='censored-caxias', name='Teresa Sartori', place='caxias-do-sul',
        dialect='Veneto', languages=('portoghese',),
        age=(41, 45), sex='b', education='m', generation='b',
        status='a', public=False,
    ),
)


def source_label(profile):
    return SOURCE_PREFIX + profile['slug'] + ' (synthetic audio)'
