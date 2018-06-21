======================
Session Video Uploader
======================

Upload session videos to YouTube.

To use:

1. Clone the project.
2. Add ``.env`` in project containing path to your service account certificate.
   This is a JSON file downloaded from Google Console. BEWARE: NOT THE OAUTH
   AUTH FILE!
3. ``pipenv sync``
4. ``pipenv run python -m vidpub``
