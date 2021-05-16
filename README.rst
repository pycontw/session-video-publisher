======================
Session Video Uploader
======================

Support features:
- Upload session videos to YouTube.
- Generate PyCon YouTube channel video data.

To use:

* Clone the project.

* Add ``.env`` in project containing::

    # ===== Following are for upload =====
    # Point to the directory containing video files.
    # Video files should be named by the session title. They don't need to be
    # exactly identical, the script will use fuzzy match to find them.
    VIDEO_ROOT='path/to/directory/containing/video/files'

    # YouTube OAuth2 secret files, downloaded from Google Console.
    OAUTH2_CLIENT_SECRET='path/to/oauth-client-secret.json'

    # Get talks list API.
    URL='https://tw.pycon.org/2018/ccip/'


    # ===== Following are for generate =====

    # YouTube data v3 API key
    YOUTUBE_API_KEY='AIzaSyAWro8W3P02k9ouJS-1i7znK3tGW7TejsM'

    # YouTube channel information
    # You can provide CHANNEL_ID & PLAYLIST_TITLE
    # or provide PLAYLIST_ID information is enough
    CHANNEL_ID='UCHLnNgRnfGYDzPCCH8qGbQw'
    PLAYLIST_TITLE='PyCon Taiwan 2020'

    #PLAYLIST_ID='PLqtzN042QpfeN9YsLKI7RW78v1maUUYNw'


    # ===== Following are for both actions =====

    # First day of the conference.
    YEAR='2020'
    MONTH='9'
    DAY='5'

* ``pipenv sync``

* ``pipenv run upload`` for uploading session videos

* ``pipenv run generate`` for generating video data


Troubleshooting
***************

The overall flow looks like the following:

* No 2FA may be a must.

* If your uploading device is the 1st time to upload, or your last uploading is too long ago, you may need a SMS validation for your device because of security concern.

* The corresponding credential json may need to update (by the channel owner of youtube/gmail account)

* This app needs approval by the channel owner's youtube/gmail account (via web browser by clicking the authorization link).

* In 2020 we are aware that Google Security Team will review your uploaded videos via your customized application. The uploaded videos is "private(locked)" by default and not allowed to set as "public" manually until the approval of Google Security Team.
