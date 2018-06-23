======================
Session Video Uploader
======================

Upload session videos to YouTube.

To use:

* Clone the project.

* Add ``.env`` in project containing::

    VIDEO_ROOT='path/to/directory/containing/video/files'
    OAUTH2_CLIENT_SECRET='path/to/oauth-client-secret.json'
    
    # First day of conference
    YEAR='2018'
    MONTH=6
    DAY=1
    # Get talks list api
    URL='https://tw.pycon.org/2018/ccip/'

* ``pipenv sync``

* ``pipenv run upload``
