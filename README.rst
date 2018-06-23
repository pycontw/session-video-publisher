======================
Session Video Uploader
======================

Upload session videos to YouTube.

To use:

* Clone the project.

* Add ``.env`` in project containing::

    # Point to the directory containing video files.
    # Video files should be named by the session title. They don't need to be
    # exactly identical, the script will use fuzzy match to find them.
    VIDEO_ROOT='path/to/directory/containing/video/files'

    # YouTube OAuth2 secret files, downloaded from Google Console.
    OAUTH2_CLIENT_SECRET='path/to/oauth-client-secret.json'

    # First day of the conference.
    YEAR='2018'
    MONTH='6'
    DAY='1'

    # Get talks list API.
    URL='https://tw.pycon.org/2018/ccip/'

* ``pipenv sync``

* ``pipenv run upload``
