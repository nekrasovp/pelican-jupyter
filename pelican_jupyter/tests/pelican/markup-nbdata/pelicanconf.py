SITEURL = ""
SITENAME = "pelican-jupyter-test"
PATH = "content"
LOAD_CONTENT_CACHE = False
TIMEZONE = "UTC"
DEFAULT_LANG = "en"
THEME = "notmyidea"
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
ARTICLE_URL = "articles/{slug}.html"
ARTICLE_SAVE_AS = "articles/{slug}.html"

# Plugin config
MARKUP = ("ipynb",)
PLUGINS = ["pelican.plugins.ipynb_reader"]

IGNORE_FILES = [".ipynb_checkpoints"]
