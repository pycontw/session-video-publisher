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


Troubleshooting
***************

The overall flow looks like the following:

* No 2FA may be a must.

* If your uploading device is the 1st time to upload, or your last uploading is too long ago, you may need a SMS validation for your device because of security concern.

* The corresponding credential json may need to update (by the channel owner of youtube/gmail account)

* This app needs approval by the channel owner's youtube/gmail account (via web browser by clicking the authorization link).

* In 2020 we are aware that Google Security Team will review your uploaded videos via your customized application. The uploaded videos is "private(locked)" by default and not allowed to set as "public" manually until the approval of Google Security Team.
