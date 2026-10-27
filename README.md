Microcontact
============
**Microcontact. Language Variation and Change from the Italian heritage perspective** is an ERC-funded research project that aims to understand language change from a syntactic microvariational perspective, by observing core syntactic aspects of Romance languages in contact. More information can be found [here](https://microcontact.sites.uu.nl/project/).

Configuration
-------------
There are default settings in `microcontact.settings`. It is recommended that you take some time to review these settings and override them where necessary, especially for production use. See the "Database" section below for comments on the `DATABASES` setting in particular.

For local development use, create a Python module in the project root that starts with `from microcontact.settings import *` and then selectively override settings. Your file will be automatically ignored by git if you call it `config.py`.

For production use, copy `microcontact/settings.py` to a separate file. Put this file elsewhere in the filesystem under restrictive access rights, then modify its contents. There are many settings that need to be overridden because of security considerations; please see the comments.

In either case, set the environment variable `DJANGO_SETTINGS_MODULE` to the module name of your customized settings in order to use it. Depending on location of your settings module, you may also need to set `PYTHONPATH`. For documentation, see the [Django documentation on settings][1].

Google Maps API key
-------------------
You need to obtain an API key for Google Maps in order for the frontend application to work. Save the key (with nothing else) in a file named `.gmapikey` in the project root directory. This file is ignored by Git.

Dependencies
------------

Make sure that the following packages are installed using `sudo apt-get install`:

* libldap2-dev (needed for pyldap)
* libsasl2-dev (needed for pyldap)
* libmagic-dev (needed for [python-magic][22])
* python3-dev (needed for Anaconda3)

For the Python dependencies, create a Python 3 virtualenv and activate it. `pip install pip-tools` and then run `pip-sync`.
For the JavaScript dependencies, install NPM, Bower and Grunt, then run `npm install` and `bower install`. For deployment, you can run `bower install` with the `--production` flag in order to skip development-only packages.

For audio conversion, get ffmpeg. See instructions for Windows, OS X and Ubuntu [here][21].

For file type detection we use the [python-magic][22] package, which depends on `libmagic` being installed on your system.

Database
--------
The default configuration in `microcontact.settings` assumes a SQLite database. SQLite and PostgreSQL are also the only database backends supported by the `requirements.txt`. If you choose a different backend, you will need to install additional libraries. For most backends, including PostgreSQL, you will also need to create a dedicated database and a dedicated user with all privileges on that database. For local development, the database user should also be able to create new databases in order to enable testing. See the [Django settings reference][2] for instructions on setting `DATABASES`.

In order to bootstrap your local database before first running the application, run `python manage.py migrate`. Run this command again after defining new migrations. In order to define a new migration (after modifying the database schema), run `python manage.py makemigrations` and edit the generated file. See the [Django documentation on migrations][14] for details.

Local development
-----------------
Make sure that your virtual environment is activated, then run `grunt`. This will do many things:

  - Compile the CoffeeScript, Sass and Mustache sources to browser-ready static assets (these are hidden in `/.tmp` under the project root).
  - Run all unit tests once (this relies on you having installed `pytest`).
  - Run the Django-based development server on `localhost:8000/`.
  - Watch all sources for changes, automatically recompiling static assets, re-running unit tests and reloading any open browser tabs where applicable.
  - Recompile and rerun the functional tests when changed. Note that the functional tests are not automatically rerun when you change source files. Functional tests are further discussed below.

All subprocesses log to the same single terminal that you run `grunt` from, so the output will be a mess at first. After that, however, you will be grateful for the combined output, as any server hiccups, test failures and compilation errors will automatically come to your attention from a single window. This process keeps running until you kill it with `ctrl-c`.

At your option, you may also run any of the tasks above separately. The required commands are listed below with pointers to further documentation. Refer to the `Gruntfile.coffee` for the definitions and configuration of the Grunt-based tasks.

  - `grunt handlebars` to precompile all Mustache templates except for the `index.mustache` to a single `templates.js` ([grunt-contrib-handlebars][13]).
  - `grunt coffee` to compile all CoffeeScript sources to JavaScript ([grunt-contrib-coffee][3]). `grunt coffee:compile` to limit compilation to the client side scripts or `grunt coffee:functional` to limit compilation to the functional tests.
  - `grunt newer:coffee`, `grunt newer:coffee:compile` or `grunt newer:coffee:functional` to do the same but only with changed sources ([grunt-newer][15]).
  - `grunt clean:develop compile-handlebars:develop` to generate the `index.html` ([grunt-compile-handlebars][4]). The `clean` step is necessary because `compile-handlebars` appends to output files instead of replacing them.
  - `grunt sass postcss` to compile the stylesheets from Sass to CSS ([grunt-sass][18], [grunt-postcss][19]).
  - `grunt symlink` to ensure that the `/bower_components` are accessible from within the `/.tmp` ([grunt-contrib-symlink][6]).
  - `grunt compile` to do all of the above.
  - `grunt server` or `python manage.py runserver` to run just the development server ([django-admin][12]). Keeps running.
  - `grunt watch` to automatically recompile, retest and reload when files change ([grunt-contrib-watch][10]). This includes the functional tests as described above. Note that if you start the development server before the watch task, livereload will not work until you manually refresh your browser tab. Keeps running.
  - `grunt casperjs` to run all functional tests. This assumes that you already compiled the CoffeeScript sources. ([grunt-casperjs][16], [CasperJS][17])
  - `grunt newer:casperjs` to run only the functional tests that you edited and recompiled.

In order to remove generated files but not the `node_modules` or the `bower_components`, run `grunt clean:all` ([grunt-contrib-clean][11]).

If you want to verify the optimized assets (see below) during development, you can override the `STATICFILES_DIRS` setting in your `config.py` as follows:

    STATICFILES_DIRS = (
        os.path.join(BASE_DIR, 'dist'),
    )

this will cause the Django application to take the `index.html` and other static assets from `/dist` instead of `/.tmp`. The development server will pick up the change while running, so you don't need to restart it. Note that livereload does not work when you serve from `/dist`.

Deployment
----------
An optimized version of the static assets can be obtained by running `grunt dist`. The optimized files are put in the `/dist` project subdirectory. In this case, most of the external libraries are fetched from CDNs in their minified forms.

You are advised to run the Django-based backend as a WSGI application from your favourite HTTP server. See [Deploying Django][20].

Serve the static assets under `/static/`.

Containers
----------
A containerized setup for Podman/Docker is available. See [docs/containerization.md](docs/containerization.md) for details.

Browser tests
-------------
Four Playwright tests in `e2e/` cover map navigation, recording discovery and
playback, public/private marker visibility, and country/city selection. They
run against an existing app with live Google Maps and seeded demo data, using
their own Node dependencies. See [setup and commands](docs/demo-data.md#browser-map-tests).

Directory reference
-------------------

    project root                 (whatever you called it)
    ├── .editorconfig            notation conventions, in-VCS
    ├── .functional-tests        functional tests compiled to JS, out-of-VCS
    ├── .gitignore
    ├── .tmp/                    generated static assets for dev., out-of-VCS
    ├── Gruntfile.coffee         task configuration, in-VCS
    ├── README.md                this file, in-VCS
    ├── bower.json               listing of JS deps, in-VCS
    ├── bower_components/        JS deps during development, out-of-VCS
    ├── client                   static asset sources, in-VCS
    │   ├── script
    │   │   ├── *.coffee
    │   │   └── *_test.coffee    unit tests belonging to *.coffee
    │   ├── style/
    │   └── template/
    ├── config.py                presumed to be written by you, out-of-VCS
    ├── dist/                    generated static assets for depl., out-of-VCS
    ├── functional-tests         functional test sources in Coffee, in-VCS
    ├── manage.py                backend manager, in-VCS
    ├── media/                   file uploads, out-of-VCS
    ├── microcontact             the Django project package, in-VCS
    │   ├── *.py
    │   └── *_test.py            unit tests belonging to *.py
    ├── node_modules/            Node and Grunt dependencies, out-of-VCS
    ├── package.json             listing of Node/Grunt deps, in-VCS
    ├── recordings               the Django API application package, in-VCS
    │   ├── *.py
    │   └── *_test.py            unit tests belonging to *.py
    ├── requirements.in          top-level Python package requirements, in-VCS
    └── requirements.txt         generated pinned requirements, in-VCS


(c) 2016 Julian Gonggrijp
(c) 2017 Digital Humanities Lab, Utrecht University


[1]: https://docs.djangoproject.com/en/1.8/topics/settings/
[2]: https://docs.djangoproject.com/en/1.8/ref/settings/#databases
[3]: https://www.npmjs.com/package/grunt-contrib-coffee
[4]: https://www.npmjs.com/package/grunt-compile-handlebars
[6]: https://www.npmjs.com/package/grunt-contrib-symlink
[7]: https://www.npmjs.com/package/grunt-contrib-connect
[8]: https://www.npmjs.com/package/http-proxy
[9]: https://www.npmjs.com/package/grunt-concurrent
[10]: https://www.npmjs.com/package/grunt-contrib-watch
[11]: https://www.npmjs.com/package/grunt-contrib-clean
[12]: https://docs.djangoproject.com/en/1.8/ref/django-admin/
[13]: https://www.npmjs.com/package/grunt-contrib-handlebars
[14]: https://docs.djangoproject.com/en/1.8/topics/migrations/
[15]: https://www.npmjs.com/package/grunt-newer
[16]: https://www.npmjs.com/package/grunt-casperjs
[17]: http://docs.casperjs.org/
[18]: https://www.npmjs.com/package/grunt-sass
[19]: https://www.npmjs.com/package/grunt-postcss
[20]: https://docs.djangoproject.com/en/1.8/howto/deployment/
[21]: https://github.com/adaptlearning/adapt_authoring/wiki/installing-ffmpeg
[22]: https://github.com/ahupp/python-magic
