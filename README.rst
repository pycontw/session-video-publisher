======================
Session Video Uploader
======================

Upload session videos to YouTube.

To use:

* Clone the project.

* Add ``.env`` in project containing::

    VIDEO_ROOT='path/to/directory/containing/video/files'
    OAUTH2_CLIENT_SECRET='path/to/oauth-client-secret.json'

* ``pipenv sync``

* ``pipenv run upload``
