#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BotMessage(object):
    TYPE_TEXT = "text"
    TYPE_HTML = "html"
    TYPE_LINK = "link"
    TYPE_MEDIA = "media"
    TYPE_NOOP = "noop"
    TYPE_NOTFOUND = "notfound"
    TYPE_PUSH = "push"
    TYPE_POP = "pop"

    msg_type = None
    msg_body = None
    client = None
    options = {}

    def __init__(self, *args, **kwargs):
        self.msg_type = kwargs.get('msg_type')
        body = kwargs.get('msg_body')
        self.msg_body = BotMessage.decode_emojis(body).encode('utf_8') if body else ""
        self.client = kwargs.get('client')
        self.options = kwargs.get('options', {})

    @staticmethod
    def decode_emojis(msg=""):
        return msg.decode('utf_8').format(**EMOJIS)

    @staticmethod
    def textMsg(client, body=""):
        return BotMessage(msg_type=BotMessage.TYPE_TEXT, msg_body=body, client=client)

    @staticmethod
    def htmlMsg(client, html_body=""):
        return BotMessage(msg_type=BotMessage.TYPE_HTML, msg_body=html_body, client=client)

    @staticmethod
    def linkMsg(client, link=""):
        return BotMessage(msg_type=BotMessage.TYPE_LINK, msg_body=link, client=client)

    @staticmethod
    def mediaMsg(client, url=""):
        return BotMessage(msg_type=BotMessage.TYPE_MEDIA, msg_body=url, client=client)

    @staticmethod
    def noopMsg():
        return BotMessage(msg_type=BotMessage.TYPE_NOOP)

    @staticmethod
    def notFoundMsg():
        return BotMessage(msg_type=BotMessage.TYPE_NOTFOUND)

    @staticmethod
    def pushMsg(client, bot_id="", options=None):
        return BotMessage(msg_type=BotMessage.TYPE_PUSH, msg_body=bot_id, client=client, options=options or {})

    @staticmethod
    def popMsg():
        return BotMessage(msg_type=BotMessage.TYPE_POP)

    def isText(self):
        return self.msg_type == self.TYPE_TEXT

    def isHtml(self):
        return self.msg_type == self.TYPE_HTML

    def isLink(self):
        return self.msg_type == self.TYPE_LINK

    def isMedia(self):
        return self.msg_type == self.TYPE_MEDIA

    def isNoop(self):
        return self.msg_type == self.TYPE_NOOP

    def isNotFound(self):
        return self.msg_type == self.TYPE_NOTFOUND

    def isPush(self):
        return self.msg_type == self.TYPE_PUSH

    def isPop(self):
        return self.msg_type == self.TYPE_POP

    def isSend(self):
        return self.isText() or self.isHtml() or self.isLink() or self.isMedia()



EMOJIS = {
    "KISS_HEART": u"",
    "KISS_BLUSH": u"",
    "KISS": u"😗", 
    "KISS_CLOSED_EYES": u"😙",
    "TONGUE_WINK": U"",
    "TONGUE_CLOSED_EYES": U"",
    "TONGUE": U"😛",
    "LAUGH_HARD": U"",
    "LAUGH": U"",
    "LAUGH_SOFT": U"😀",
    "SMILE_BLUSH": U"",
    "BLUSH": U"",
    "WINK": U"",
    "HEART_EYES": U"",
    "SURPRISE_BLUSH": U"",
    "GRIMACING": U"",
    "SAD": U"",
    "RELIEVED": U"",
    "UNAMUSED": U"",
    "VERY_SAD": U"",
    "PERSEVERING": U"",
    "SAD_CRYING": U"",
    "LAUGH_CRYING": U"",
    "CRYING": U"",
    "SLEEPY": U"",
    "DISAPOINTED_SWEAT_DROP": U"",
    "VERY_DISAPOINTED_SWEAT_DROP": U"",
    "LAUGH_SWEAT_DROP": U"😅",
    "SAD_SWEAT_DROP": U"",
    "WEARY": U"😩"
}
#😫😤😆😋😎😴😵😟😦😧😈😮😬😐😕😯😶😇😑😺😸😻😽😼🙀😿😹😾👹👺🙈🙉🙊💫💥💧👅👪👬👭🙋👰🙎🙍👞👚🎽👖👝👛👓💕💖💞💌👤👥💬💭

