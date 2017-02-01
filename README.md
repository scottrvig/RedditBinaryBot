# RedditBinaryBot
Automated bot for translating binary in Reddit comments.

This Python script scratches the surface of the Reddit API and provides a "Bot" that scans through Reddit posts on the front page.  If the bot finds a comment containing a binary string (e.g. "01101001 00100000 01100001 01101101 00100000 01100001 00100000 01100010 01101111 01110100"), it will reply with a comment including the translation from binary to ASCII.

The bot is very primitive, but could easily be extended and made more flexible.

Run instructions:

$ pip install praw
$ pip install binascii
$ python binary_boy.py
