======================
Session Video Uploader
======================

Upload session videos to YouTube.

To use:

1. Clone the project.
2. Add ``.env`` in project containing…
    * ``VIDEO_ROOT`` points to the directory containing video files.
    * ``OAUTH2_CLIENT_SECRET`` points to the OAuth client secret JSON file.
3. ``pipenv sync``
4. ``pipenv run upload``
