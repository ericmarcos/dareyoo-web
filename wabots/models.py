#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, importlib, inspect, time, collections, aiml, os
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.db.models.query import QuerySet
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from polymorphic import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet
from jsonfield import JSONField
from celery.execute import send_task
from celery import chain, signature
from whatsappclient import WhatsappClient
from .utils import BotMessage
from .tasks import get_chain_send_msg, get_chain_send_many


WHATSAPP   = 1
LINE       = 2
TELEGRAM   = 3
PROVIDER_CHOICES = ((WHATSAPP, "whatsapp"),
                    (LINE, "line"),
                    (TELEGRAM, "telegram"))


class ProviderQuerySet(QuerySet):

    def provider(self, provider=None):
        return self.filter(provider=provider)

    def whatsapp(self):
        return self.provider(WHATSAPP)

    def line(self):
        return self.provider(LINE)
    
    def telegram(self):
        return self.provider(TELEGRAM)


class MetisUserQuerySet(ProviderQuerySet):
    pass


class MetisUserManager(UserManager):
    use_for_related_fields = True

    def get_queryset(self):
        return MetisUserQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return MetisUserQuerySet(self.model, using=self._db)

    def get_or_create_by_jid(self, user_jid):
        return self.get_or_create(username=user_jid, whatsapp=user_jid)


#class MetisUser(AbstractUser):
#    objects = MetisUserManager()
#
#    whatsapp = models.CharField(max_length=255, blank=True, null=True, default="")
#    line = models.CharField(max_length=255, blank=True, null=True, default="")
#    telegram = models.CharField(max_length=255, blank=True, null=True, default="")


class ConversationQuerySet(ProviderQuerySet):
    pass

 
class ConversationManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return ConversationQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return ConversationQuerySet(self.model, using=self._db)


class Conversation(models.Model):
    objects = ConversationManager()

    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations', blank=True, null=True)
    jid = models.CharField(max_length=255, blank=True, null=True, default="")
    provider = models.PositiveSmallIntegerField(blank=True, null=True, choices=PROVIDER_CHOICES, default=WHATSAPP)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    last_interaction = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    messages_log = models.TextField(blank=True, null=True, default="")
    autoresponse = models.BooleanField(blank=True, default=True)

    def is_group(self):
        return self.users.count() > 1

    def get_user(self):
        return self.users.first()

    def new_message(self, user, msg, delay_response=True, respond=None):
        '''
        respond = {None: responds depending on autoresponse attribute,
                    True: always responds, ignoring autoresponse,
                    False: never responds, ignoring autoresponse}
        '''
        now = timezone.now()
        if user:
            self.users.add(user)
            log = u"[%s] USER %s: %s\n" % (now, user.id, msg.decode('utf_8'))
        else:
            log = u"[%s] USER UNKNOWN: %s\n" % (now, msg.decode('utf_8'))
        if getattr(settings, "WA_LOGS", True):
            self.messages_log += log
        self.last_interaction = now
        self.save()

        if respond or (respond is None and self.autoresponse):
            if delay_response and getattr(settings, "WA_RESPONSE_CELERY", True):
                send_task('get_response', [self.id, now, user.id if user else None, msg])
            else:
                self.get_response(now, user, msg, False)

    def get_response(self, time, user, msg, delay_response=True):
        resp = None
        for bot in self.bots.active():
            resp = bot.input(time, user, msg)
            if isinstance(resp, collections.Iterable):
                send_msgs = []
                for r in resp:
                    if r.isSend() and delay_response and getattr(settings, "WA_RESPONSE_CELERY", True):
                        send_msgs.append(r)
                    else:
                        self.execBotMsg(r, delay_response=delay_response)
                get_chain_send_many(self.id, send_msgs).apply_async()
                return
            elif not resp.isNotFound():
                self.execBotMsg(resp, delay_response=delay_response)
                return

    def execBotMsg(self, msg, delay_response=True):
        if msg.isText() or msg.isHtml() or msg.isLink():
            if delay_response and getattr(settings, "WA_RESPONSE_CELERY", True):
                get_chain_send_msg(self.id, msg.client.id, msg.msg_body).apply_async()
            else:
                self.send(msg.client, msg.msg_body)
        elif msg.isMedia():
            if delay_response and getattr(settings, "WA_RESPONSE_CELERY", True):
                get_chain_send_msg(self.id, msg.client.id, None, msg.msg_body).apply_async()
            else:
                self.sendImage(msg.client, msg.msg_body)
        elif msg.isPush():
            self.pushBot(BotsManager.getBot(msg.msg_body),msg.client.id)
        elif msg.isPop():
            self.popBot()
        elif msg.isNoop() or msg.isNotFound():
            pass

    def send(self, client, msg):
        if getattr(settings, "WA_LOGS", True):
            log = u"[%s] BOT %s: %s\n" % (timezone.now(), client.id, msg.decode('utf_8'))
            self.messages_log += log
            self.save()
        client.send(self.provider, self.jid, msg)

    def sendImage(self, client, path):
        if getattr(settings, "WA_LOGS", True):
            log = u"[%s] BOT %s: Sent image %s\n" % (timezone.now(), client.id, path)
            self.messages_log += log
            self.save()
        client.sendPic(self.provider, self.jid, path)

    def pushBot(self, BotModel, client_id, priority=None):
        '''priority = None means that it will push this bot
        automatically on top of the stack (min priority)'''
        assert inspect.isclass(BotModel), "BotModel must be a class"
        b = BotModel(default_client=client_id)
        b.conversation = self
        if not isinstance(priority, int) and self.bots.count() > 0:
            p = self.bots.aggregate(models.Min('priority'))['priority__min']
            b.priority = int(p) - 1
        b.save()

    def popBot(self):
        b = self.bots.first()
        assert b, "The bot stack is empty"
        b.delete()


class BotsManager:
    _bots = {}

    @classmethod
    def getBotId(__cls__, BotModel):
        if BotModel.Meta and getattr(BotModel.Meta, 'bot_name', False):
            return BotModel.Meta.bot_name
        return BotModel.__name__

    @classmethod
    def registerBot(__cls__, BotModel):
        if not __cls__.isRegistered(BotModel):
            __cls__._bots[__cls__.getBotId(BotModel)] = BotModel
            return True
        return False

    @classmethod
    def isRegistered(__cls__, BotModel):
        return __cls__.getBotId(BotModel) in __cls__._bots.keys()

    @classmethod
    def getBotChoices(__cls__):
        choices = [(id,unicode(b())) for id,b in __cls__._bots.items()]
        return choices

    @classmethod
    def getBot(__cls__, id):
        return __cls__._bots.get(id)


class BotInstanceQuerySet(PolymorphicQuerySet):

    def category(self, category=None):
        return self.filter(category=category)

    def active(self):
        return self.filter(silent=False)

    def silent(self):
        return self.filter(silent=True)

class BotInstanceManager(PolymorphicManager):
    queryset_class = BotInstanceQuerySet

    def active(self):
        return self.get_queryset().active()


class BaseBotInstance(PolymorphicModel):
    objects = BotInstanceManager()
    extra_clients = 0

    conversation = models.ForeignKey(Conversation, related_name='bots', blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True, choices=BotsManager.getBotChoices(), default=None)
    silent = models.BooleanField(blank=True, default=False)
    priority = models.SmallIntegerField(default=0)
    clients = models.CharField(max_length=255, blank=True, null=True, default="")

    class Meta:
        ordering = ['priority']

    def __unicode__(self):
        return self.__class__.__name__

    def __init__(self, *args, **kwargs):
        default_client = kwargs.pop('default_client', None)
        super(BaseBotInstance, self).__init__(*args, **kwargs)
        if default_client:
            default_id = default_client if isinstance(default_client, basestring) else default_client.id
            clients = ClientsManager.requestClients(self.extra_clients, exclude=[default_id])
            self.clients = ",".join([default_id] + [c.id for c in clients])
        self.category = BotsManager.getBotId(self.__class__)

    def input(self, time, user, msg):
        raise Exception("You must override input method")

    def getClients(self):
        ids = self.clients.split(",")
        return [ClientsManager.getClient(id) for id in ids]

    def getDefaultClient(self):
        ids = self.clients.split(",")
        return ClientsManager.getClient(ids[0])


class PingPongBot(BaseBotInstance):

    def input(self, time, user, msg):
        client = self.getDefaultClient()
        return BotMessage.textMsg(client, msg)


#http://timonweb.com/imagefield-overwrite-file-if-file-with-the-same-name-exists
from django.core.files.storage import FileSystemStorage
class OverwriteStorage(FileSystemStorage):
 
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


class AliceBot(BaseBotInstance):
    startup_aiml = "./alice-brains/std-startup.xml"
    startup_commands = "load aiml b"

    brain_file = models.FileField(upload_to='alice/brains', null=True, blank=True, storage=OverwriteStorage())
    session = JSONField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(AliceBot, self).__init__(*args, **kwargs)
        self._aiml = aiml.Kernel()
        if self.brain_file:
            self._aiml.bootstrap(brainFile=self.brain_file.path)
        else:
            self._aiml.bootstrap(learnFiles=self.startup_aiml, commands=self.startup_commands)
        if self.session:
            for pred,value in self.session.items():
                self._aiml.setPredicate(pred, value, str(self.id))

    def save(self, *args, **kwargs):
        create_files = kwargs.pop("create_files", True)
        super(AliceBot, self).save(*args, **kwargs)
        if create_files:
            self.brain_file.save("AliceBot_%s.brn" % self.id, ContentFile(''), save=False)
            self._aiml.saveBrain(self.brain_file.path)
            self.session = self._aiml.getSessionData(str(self.id))
            self.save(create_files=False)


    def input(self, time, user, msg):
        client = self.getDefaultClient()
        resp = self._aiml.respond(msg, str(self.id))
        self.save()
        if resp == "STARTTRIVIA":
            r = [BotMessage.pushMsg(client, "TriviaBot"),
                BotMessage.textMsg(client, "Loading trivia bot!")]
            return r
        return BotMessage.textMsg(client, resp)


#TODO: move this to __init__?
for rbot in [getattr(importlib.import_module(mod), cls)
    for (mod, cls) in (sbot.rsplit(".", 1)
        for sbot in getattr(settings, "WA_BOTS", ["wabots.PingPongBot"]))]:
    BotsManager.registerBot(rbot)

def getDefaultBot():
    try:
        mod, cls in getattr(settings, "WA_DEFAULT_BOT", "wabots.PingPongBot").rsplit(".", 1)
        return getattr(importlib.import_module(mod), cls)
    except:
        return None


class ClientsManager:
    '''TODO: Maybe this should be a DB Model?'''
    _clients = {}

    @classmethod
    def requestClients(__cls__, n=1, exclude=None):
        exclude = exclude or []
        return [c for c in __cls__._clients.values() if c.id not in exclude][0:n]

    @classmethod
    def registerClient(__cls__, client):
        if client.whatsapp:
            __cls__._clients[client.id] = client

    @classmethod
    def getClient(__cls__, id):
        return __cls__._clients.get(id)

    @classmethod
    def init(__cls__,):
        for client in __cls__._clients.values():
            client.login()

    

class Client:
    id = None
    whatsapp = None
    line = None
    telegram = None

    def __init__(self, id=None, *args, **kwargs):
        self.id = id

    def addWhatsappProvider(self, user, nick, pwd):
        self.addProvider(WhatsappClient(user, nick, pwd, 'info'))

    def addProvider(self, client):
        if isinstance(client, WhatsappClient):
            self.whatsapp = client
            if not self.id:
                self.id = client.username
            self.whatsapp.addListener("message_received", self._onWhatsappMessageReceived)
            self.whatsapp.addListener("group_messageReceived", self._onWhatsappGroupMessageReceived)
        else:
            raise Exception("This provider is not supported yet")

    def _onWhatsappMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadcast):
        message_received.send(sender=self.__class__, client=self, conversation_jid=jid, user_jid=jid, msg=messageContent)

    def _onWhatsappGroupMessageReceived(self, messageId, jid, author, messageContent, timestamp, wantsReceipt, pushName):
        message_received.send(sender=self.__class__, client=self, conversation_jid=jid, user_jid=author, msg=messageContent)

    def startTyping(self, jid):
        if self.whatsapp:
            self.whatsapp.startTyping(jid)

    def stopTyping(self, jid):
        if self.whatsapp:
            self.whatsapp.stopTyping(jid)

    def send(self, provider, jid, msg):
        if provider == WHATSAPP:
            self.whatsapp.send(jid, msg)

    def sendPic(self, provider, jid, path):
        if provider == WHATSAPP:
            self.whatsapp.sendPic(jid, path)

    def login(self):
        if self.whatsapp:
            self.whatsapp.login()


c = Client()
c.addWhatsappProvider(settings.WA_USERNAME, settings.WA_NICKNAME, settings.WA_PASSWORD)
ClientsManager.registerClient(c)
if getattr(settings, "WA_INIT_CLIENTS", True):
    ClientsManager.init()


def process_message(client_id, conversation_jid, user_jid, msg):
    c, c_created = Conversation.objects.get_or_create(jid=conversation_jid)
    u, u_created = get_user_model().objects.get_or_create_by_jid(user_jid)
    if c_created:
        c.pushBot(getDefaultBot(), client_id)
    c.new_message(u, msg, delay_response=getattr(settings, "WA_RESPONSE_CELERY", True))

#Avoinding circular dependency
#see: http://stackoverflow.com/questions/7115097/the-right-place-to-keep-my-signals-py-files-in-django
from .signals import message_received