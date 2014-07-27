from JumpScale import j

from HTML2Text import *

class HTMLFactory(object):

    def __init__(self):
        pass
        
    def html2text(self, html):
        """
        """
        html=unicode(html, errors='ignore')
        encoding = "utf-8"
        html = html.decode(encoding)
        h = HTML2Text()

        # # handle options
        # if options.ul_style_dash: h.ul_item_mark = '-'
        # if options.em_style_asterisk:
        #     h.emphasis_mark = '*'
        #     h.strong_mark = '__'

        h.body_width = 0 
        # h.list_indent = options.list_indent
        # h.ignore_emphasis = options.ignore_emphasis
        # h.ignore_links = options.ignore_links
        # h.ignore_images = options.ignore_images
        # h.google_doc = options.google_doc
        # h.hide_strikethrough = options.hide_strikethrough
        # h.escape_snob = options.escape_snob

        text=h.handle(html)
        text.encode('utf-8')

        return text
        

