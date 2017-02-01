import praw
import binascii
import logging
import time
import re
import os

logger = None

# TODO: Pass in credentials for security
username = "BinaryAsciiBot"
password = "<redacted>"

pattern = re.compile('^[0-1]+$')

NUM_SECONDS_IN_DAY = 60 * 60 * 24  # 86400

seen_comments = []
replied_comments = []


def setup_logging():
    """Set up logging and file handler."""
    global logger

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if os.path.exists("logs/binary_bot.txt"):
        os.remove("logs/binary_bot.txt")

    handler = logging.FileHandler("logs/binary_bot.txt")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)-15s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.info("Binary bot started at %s" % time.strftime("%d/%m/%Y %H:%M:%S"))


def reddit_login():
    """Log into Reddit using the desired bot credentials."""
    r = praw.Reddit(user_agent="PRAW:BinaryBot:0.1 (by /u/<redacted>)")
    logger.info("Logging in with credentials %s // %s" % (username, password))
    r.login(username, password)
    return r


def find_binary(text):
    """Return any found binary strings in the body of the comment."""
    if "1" not in text and "0" not in text:
        # Speed optimization, regex can be slow
        return None

    binary_words = []
    for w in text.split():
        match = pattern.match(w)
        if match and len(match.string) >= 8 and not (len(match.string) % 8):
            # Potentially binary
            binary_words.append(match.string)

    if not binary_words:
        return None

    return "".join(binary_words)


def generate_response(ascii_str):
    """Generate a text response to reply to the comment."""
    msg = "Hello! It looks like you're trying to write something in binary.\n\n"
    msg += "Your translated message:\n%s\n\n" % ascii_str
    msg += "Am I wrong? Send a PM please."


def send_reply(comment, binary):
    """Send an automated reply with the translation."""
    try:
        binary_int = int("0b" + binary, 2)
        ascii_str = binascii.unhexlify('%x' % binary_int)
    except:
        logger.warning("Suspected binary but failed to translate: %s" % binary)
        return

    if comment.id not in replied_comments:
        replied_comments.append(comment.id)
        response = generate_response(ascii_str)
        try:
            logger.warning("Found binary! %s" % comment.permalink)
            logger.warning("Post contained: %s" % binary)
            logger.warning("Translated text: %s" % ascii_str)
            logger.warning("Response: %s" % response)
            comment.reply(response)
        except:
            logger.exception("Failed to send reply!")


def parse_comment(comment):
    """Parse individual comment."""
    # Sometimes API fails to return a comment author
    if comment.author and comment.author.name:
        if comment.author.name.lower() == username.lower():
            # Don't find ourself
            return

    if comment.id not in seen_comments:
        seen_comments.append(comment.id)
        binary = find_binary(comment.body)
        if binary:
            send_reply(comment, binary)


def parse_submission(submission):
    """Parse the individual submission from the front page."""
    logger.info("Parsing '%s'" % submission.title)
    submission.refresh()

    logger.info("Expanding 'More Comments'")
    submission.replace_more_comments(limit=None, threshold=0)

    all_comments = submission.comments
    all_comments_flattened = praw.helpers.flatten_tree(submission.comments)

    logger.info("Parsing %s comments" % len(all_comments_flattened))
    for comment in all_comments_flattened:
        parse_comment(comment)
    logger.info("--------------------------------------")


def run_bot():
    """Main execution loop."""
    setup_logging()
    r = reddit_login()
    clear_seen_list_time = time.time() + NUM_SECONDS_IN_DAY

    # Run until killed
    while 1:
        try:
            if time.time() > clear_seen_list_time:
                # Helps the bot run "forever" by clearing out state periodically
                seen_comments = []
                clear_seen_list_time = time.time() + NUM_SECONDS_IN_DAY

            front_page = r.get_front_page()
            for submission in front_page:
                try:
                    parse_submission(submission)
                except KeyboardInterrupt:
                    logger.warning("Forcing a quit.")
                    return
                except:
                    logger.exception("Exception hit! Going to keep trying..")

            logger.info("Checked %s comments." % len(seen_comments))
        except:
            logger.exception("Outer loop failed.")


if __name__ == "__main__":
    run_bot()
