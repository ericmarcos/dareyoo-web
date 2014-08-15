#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) <2014> Eric Marcos <ericmarcos.p@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this 
software and associated documentation files (the "Software"), to deal in the Software 
without restriction, including without limitation the rights to use, copy, modify, 
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to the following 
conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR 
A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

__author__ = "Eric Marcos"
__version__ = "0.1"
__email__ = "ericmarcos.p@gmail.com"
__license__ = "MIT"

import sys, os, hashlib, base64, StringIO
from Yowsup.Common.utilities import Utilities
from Yowsup.Common.debugger import Debugger
from Yowsup.connectionmanager import YowsupConnectionManager
from Yowsup.Registration.v2.existsrequest import WAExistsRequest as WAExistsRequestV2
from Yowsup.Registration.v2.coderequest import WACodeRequest as WACodeRequestV2
from Yowsup.Registration.v2.regrequest import WARegRequest as WARegRequestV2
from Yowsup.Media.downloader import MediaDownloader
from Yowsup.Media.uploader import MediaUploader
from PIL import Image
import requests
import tempfile


class WhatsappClient:
    LOG_LEVELS = {
        'none': 0,
        'error': 1,
        'info': 2,
        'debug': 3
    }

    _mediaUploads = {}

    def __init__(self, user='', nick='', pwd='', logLevel='info'):
        self.username = user
        self.nickname = nick
        self.password = pwd

        self._connectionManager = YowsupConnectionManager()

        self._signalsInterface = self._connectionManager.getSignalsInterface()
        self._methodsInterface = self._connectionManager.getMethodsInterface()
        self._connectionManager.setAutoPong(True)

        self.addListener("auth_success", self._onAuthSuccess)
        self.addListener("auth_fail", self._onAuthFailed)

        self.addListener("receipt_messageSent", self._onMessageSent)
        self.addListener("receipt_messageDelivered", self._onMessageDelivered)

        self.addListener("message_received", self._onMessageReceived)
        self.addListener("group_messageReceived", self._onGroupMessageReceived)
        self.addListener("image_received", self._onImageReceived)

        self.addListener("profile_setPictureSuccess", self._onProfilePicSuccess)
        self.addListener("profile_setPictureError", self._onProfilePicError)
        self.addListener("message_error", self._onError)

        self.addListener("media_uploadRequestSuccess", self._onMediaUploadRequestSuccess)
        self.addListener("media_uploadRequestFailed", self._onMediaUploadRequestFailed)
        self.addListener("media_uploadRequestDuplicate", self._onMediaUploadRequestDuplicate)

        self._log_level = logLevel if logLevel in self.LOG_LEVELS.keys() else 'info'
        Debugger.enabled = self.LOG_LEVELS.get(logLevel) >= self.LOG_LEVELS.get('debug')

    def addListener(self, event, callback):
        self._signalsInterface.registerListener(event, callback)

    def _log(self, level, msg):
        if self.LOG_LEVELS.get(level) <= self.LOG_LEVELS.get(self._log_level):
            print(msg)

    def _dissectPhoneNumber(self, phoneNumber):
        try:
            for row in COUNTRY_CODES.split("\n"):
                line = row.split(",")
                if len(line) == 3:
                    country, cc, mcc = line
                else:
                    country,cc = line
                    mcc = "000"
                try:
                    if phoneNumber.index(cc) == 0:
                        return (cc, phoneNumber[len(cc):])
                except ValueError:
                    continue     
        except:
            pass
        return False

    def requestCode(self, method='sms', username=''):
        cc, phone = self._dissectPhoneNumber(username or self.username)
        identity = Utilities.processIdentity('')
        wc = WACodeRequestV2(cc, phone, identity, method if method in ('sms', 'voice') else 'sms')
        result = wc.send()
        self._log('info', self._requestResultToString(result))

    def requestPassword(self, code, username=''):
        cc, phone = self._dissectPhoneNumber(username or self.username)
        code = "".join(code.split('-'))
        identity = Utilities.processIdentity('')
        wr = WARegRequestV2(cc, phone, code, identity)
        result = wr.send()
        self._log('info', self._requestResultToString(result))

    def _requestResultToString(self, result):
        unistr = str if sys.version_info >= (3, 0) else unicode
        out = []
        for k, v in result.items():
            if v is None:
                continue
            out.append("%s: %s" %(k, v.encode("utf-8") if type(v) is unistr else v))
            
        return "\n".join(out)

    def login(self, username=None, password=None, nickname=''):
        self.username = username or self.username
        self.password = password or self.password
        self.nickname = nickname or self.nickname
        self._real_password = base64.b64decode(bytes(self.password.encode('utf-8')))
        self._log('info', "[client | logging_in]: %s (%s)" % (self.nickname, self.username))
        self._methodsInterface.call("auth_login", (self.username, self._real_password))

    def setProfilePic(self, picPath):
        self._log('info', "[client | setting_profile_pic]: %s" % (jid, picPath))
        self._methodsInterface.call("profile_setPicture", (picPath,))

    def startTyping(self, jid):
        self._log('info', "[client | typing_start | jid:%s]" % jid)
        self._methodsInterface.call("typing_send", (jid,))

    def stopTyping(self, jid):
        self._log('info', "[client | typing_stop | jid:%s]" % jid)
        self._methodsInterface.call("typing_paused", (jid,))

    def send(self, jid, message):
        if not jid.endswith('@s.whatsapp.net') and not jid.endswith('@g.us'):
            jid += '@s.whatsapp.net'
        self._log('info', "[client | sending_msg | jid:%s]: %s" % (jid, message.decode('utf_8')))
        self._methodsInterface.call("message_send", (jid, message))

    def sendPic(self, jid, path):
        if not jid.endswith('@s.whatsapp.net') and not jid.endswith('@g.us'):
            jid += '@s.whatsapp.net'

        file_temp = False
        if not os.path.isfile(path):
            r = requests.get(path, stream=True)
            if r.status_code == 200:
                file_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                for chunk in r.iter_content():
                    file_temp.write(chunk)
                file_temp.close()
                path = file_temp.name

        statinfo = os.stat(path)
        name = os.path.basename(path)
        mtype = "image"
        size = os.path.getsize(path)
        sha1 = hashlib.sha256()
        fp = open(path, 'rb')
        try:
            sha1.update(fp.read())
            hsh = base64.b64encode(sha1.digest())
            self._log('info', "[client | sending_media_upload_request | jid:%s]" % jid)
            self._methodsInterface.call("media_requestUpload", (hsh, mtype, size))
        finally:
            fp.close()
        self._mediaUploads[hsh] = { 'hash': hsh,
                                    'jid': jid,
                                    'path': path,
                                    'name': name,
                                    'url':'',
                                    'del_file': file_temp.name if file_temp else None,
                                    'gotMediaReceipt': True,
                                    'mediaDone': False}

    def _onMediaUploadRequestSuccess(self, hsh, url, resumeFrom):
        self._log('info', "[whatsapp | media_upload_request_ok | hash:%s | url:%s | resume:%s]" % (hsh, url, resumeFrom))
        mu = self._mediaUploads.get(hsh)
        if mu:
            mu['url'] = url
            mu['gotMediaReceipt'] = True
            self._uploadImage(mu)

    def _onMediaUploadRequestFailed(self, hsh):
        self._log('info', "[whatsapp | media_upload_request_error | hash:%s]" % hsh)
        if self._mediaUploads[hsh].get('del_file'):
            os.remove(self._mediaUploads[hsh].get('del_file'))
        del self._mediaUploads[hsh]

    def _onMediaUploadRequestDuplicate(self, hsh, url):
        self._log('info', "[whatsapp | media_upload_request_duplicate | hash:%s | url:%s]" % (hsh, url))
        mu = self._mediaUploads.get(hsh)
        if mu:
            mu['url'] = url
            mu['gotMediaReceipt'] = True
            self._uploadImage(mu)

    def _doSendImage(self, mu):
        uploader = MediaUploader(mu.get('jid'),
                                 self.username,
                                 lambda url: self._onUploadSuccess(mu, url),
                                 lambda: self._onUploadError(mu),
                                 lambda progress: self._onUploadProgressUpdated(mu, progress))
        uploader.upload(mu.get('path'), mu.get('url'))

    def _onUploadSuccess(self, mu, url):
        self._log('info', "[whatsapp | media_upload_success | hash:%s | url:%s]" % (mu.get('hash'), url))
        mu['url'] = url
        self._doSendImage(mu)

    def _onUploadError(self, mu):
        self._log('info', "[whatsapp | media_upload_error | hash:%s]" % mu.get('hash'))
        if self._mediaUploads[mu.get('hash')].get('del_file'):
            os.remove(self._mediaUploads[mu.get('hash')].get('del_file'))
        del self._mediaUploads[mu.get('hash')]

    def _onUploadProgressUpdated(self, mu, progress):
        pass

    def _doSendImage(self, mu):
        size = str(os.stat(mu.get('path')).st_size)
        
        im = Image.open(mu.get('path'))
        im.thumbnail((64, 64), Image.ANTIALIAS)
        #im = im.crop((0,0,63,63))
        buf = StringIO.StringIO()
        im.save(buf, format= 'JPEG')
        raw = base64.b64encode(buf.getvalue())
        buf.close()
        self._methodsInterface.call("message_imageSend", (mu.get('jid'), mu.get('url'), mu.get('name'), size, raw))
        if self._mediaUploads[mu.get('hash')].get('del_file'):
            os.remove(self._mediaUploads[mu.get('hash')].get('del_file'))
        del self._mediaUploads[mu.get('hash')]

    def _onAuthSuccess(self, username):
        self._log('info', "[whatsapp | auth_ok | %s]" % username)
        self._methodsInterface.call("ready")
        self._methodsInterface.call("presence_sendAvailableForChat", (self.nickname,))

    def _onAuthFailed(self, username, err):
        self._log('error', "[whatsapp | auth_error | error:%s" % err)

    def _onMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadcast):
        self._log('info', "[whatsapp | received | jid:%s]: %s" % (jid, messageContent.decode('utf_8')))
        
        if wantsReceipt:
            self._methodsInterface.call("message_ack", (jid, messageId))

    def _onGroupMessageReceived(self, messageId, jid, author, messageContent, timestamp, wantsReceipt, pushName):
        self._log('info', "[whatsapp | received_group | jid:%s | author:%s]: %s" % (jid, author, messageContent.decode('utf_8')))
        
        if wantsReceipt:
            self._methodsInterface.call("message_ack", (jid, messageId))

    def _onImageReceived(self, messageId, jid, preview, url, size, wantsReceipt, isBroadcast):
        self._log('info', "[whatsapp | image_received | jid:%s]: %s" % (jid, preview))
        
        if wantsReceipt:
            self._methodsInterface.call("message_ack", (jid, messageId))

    def _onMessageSent(self, jid, messageId):
        self._log('info', "[whatsapp | sent_ok | jid:%s]" % jid)

    def _onMessageDelivered(self, jid, messageId):
        self._log('info', "[whatsapp | delivered_ok | jid:%s]" % jid)
        self._methodsInterface.call("delivered_ack", (jid, messageId))

    def _onProfilePicSuccess(self):
        self._log('info', "[whatsapp | profile_pic_ok]")

    def _onProfilePicError(self, errorCode):
        self._log('error', "[whatsapp | profile_pic_error | error_code:%s]" % errorCode)

    def _onError(self, messageId, jid, errorCode):
        self._log('error', "[whatsapp | message_error | error_code:%s | jid:%s | message_id:%s]" % (errorCode, jid, messageId))


COUNTRY_CODES = '''Afghanistan,93,412
Albania,355,276
Algeria,213,603
Andorra,376,213
Angola,244,631
Anguilla,1,365
Antarctica (Australian bases),6721,232
Antigua and Barbuda,1,344
Argentina,54,722
Armenia,374,283
Aruba,297,363
Ascension,247,658
Australia,61,505
Austria,43,232
Azerbaijan,994,400
Bahamas,1,364
Bahrain,973,426
Bangladesh,880,470
Barbados,1,342
Belarus,375,257
Belgium,32,206
Belize,501,702
Benin,229,616
Bermuda,1,350
Bhutan,975,402
Bolivia,591,736
Bosnia and Herzegovina,387,218
Botswana,267,652
Brazil,55,724
British Indian Ocean Territory,246,348
British Virgin Islands,1,348
Brunei,673,528
Bulgaria,359,284
Burkina Faso,226,613
Burundi,257,642
Cambodia,855,456
Cameroon,237,624
Canada,1,302
Cape Verde,238,625
Cayman Islands,1,346
Central African Republic,236,623
Chad,235,622
Chile,56,730
China,86,460|461
Colombia,57,732
Comoros,269,654
Democratic Republic of the Congo,243,630
Republic of the Congo,242,629
Cook Islands,682,548
Costa Rica,506,658
Cote d'Ivoire,712
Croatia,385,219
Cuba,53,368
Cyprus,357,280
Czech Republic,420,230
Denmark,45,238
Djibouti,253,638
Dominica,1,366
Dominican Republic,1,370
East Timor,670,514
Ecuador,593,740
Egypt,20,602
El Salvador,503,706
Equatorial Guinea,240,627
Eritrea,291,657
Estonia,372,248
Ethiopia,251,636
Falkland Islands,500,750
Faroe Islands,298,288
Fiji,679,542
Finland,358,244
France,33,208
French Guiana,594,742
French Polynesia,689,547
Gabon,241,628
Gambia,220,607
Gaza Strip,970,0
Georgia,995,282
Germany,49,262
Ghana,233,620
Gibraltar,350,266
Greece,30,202
Greenland,299,290
Grenada,1,352
Guadeloupe,590,340
Guam,1,535
Guatemala,502,704
Guinea,224,611
Guinea-Bissau,245,632
Guyana,592,738
Haiti,509,372
Honduras,504,708
Hong Kong,852,454
Hungary,36,216
Iceland,354,274
India,91,404|405|406
Indonesia,62,510
Iraq,964,418
Iran,98,432
Ireland (Eire),353,272
Israel,972,425
Italy,39,222
Jamaica,1,338
Japan,81,440|441
Jordan,962,416
Kazakhstan,7,401
Kenya,254,639
Kiribati,686,545
Kuwait,965,419
Kyrgyzstan,996,437
Laos,856,457
Latvia,371,247
Lebanon,961,415
Lesotho,266,651
Liberia,231,618
Libya,218,606
Liechtenstein,423,295
Lithuania,370,246
Luxembourg,352,270
Macau,853,455
Republic of Macedonia,389,294
Madagascar,261,646
Malawi,265,650
Malaysia,60,502
Maldives,960,472
Mali,223,610
Malta,356,278
Marshall Islands,692,551
Martinique,596,340
Mauritania,222,609
Mauritius,230,617
Mayotte,262,654
Mexico,52,334
Federated States of Micronesia,691,550
Moldova,373,259
Monaco,377,212
Mongolia,976,428
Montenegro,382,297
Montserrat,1,354
Moroo,212,604
Mozambique,258,643
Myanmar,95,414
Namibia,264,649
Nauru,674,536
Netherlands,31,204
Netherlands Antilles,599,362
Nepal,977,429
New Caledonia,687,546
New Zealand,64,530
Nicaragua,505,710
Niger,227,614
Nigeria,234,621
Niue,683,555
Norfolk Island,6723,505
North Korea,850,467
Northern Ireland 44,28,272
Northern Mariana Islands,1,534
Norway,47,242
Oman,968,422
Pakistan,92,410
Palau,680,552
Palestine,970,425
Panama,507,714
Papua New Guinea,675,537
Paraguay,595,744
Peru,51,716
Philippines,63,515
Poland,48,260
Portugal,351,268
Qatar,974,427
Reunion,262,647
Romania,40,226
Russia,7,250
Rwanda,250,635
Saint-Barthelemy,590,340
Saint Helena,290,658
Saint Kitts and Nevis,1,356
Saint Lucia,1,358
Saint Martin (French side),590,340
Saint Pierre and Miquelon,508,308
Saint Vincent and the Grenadines,1,360
Samoa,685,549
Sao Tome and Principe,239,626
Saudi Arabia,966,420
Senegal,221,608
Serbia,381,220
Seychelles,248,633
Sierra Leone,232,619
Singapore,65,525
Slovakia,421,231
Slovenia,386,293
Solomon Islands,677,540
Somalia,252,637
South Africa,27,655
South Korea,82,450
South Sudan,211,659
Spain,34,214
Sri Lanka,94,413
Sudan,249,634
Suriname,597,746
Swaziland,268,653
Sweden,46,240
Switzerland,41,228
Syria,963,417
Taiwan,886,466
Tajikistan,992,436
Tanzania,255,640
Thailand,66,520
Togo,228,615
Tokelau,690,690
Tonga,676,539
Trinidad and Tobago,1,374
Tunisia,216,605
Turkey,90,286
Turkmenistan,993,438
Turks and Caicos Islands,1,376
Tuvalu,688,553
Uganda,256,641
Ukraine,380,255
United Arab Emirates,971,424|430|431
United Kingdom,44,234|235
United States of America,1,310|311|312|313|314|315|316
Uruguay,598,748
Uzbekistan,998,434
Vanuatu,678,541
Venezuela,58,734
Vietnam,84,452
U.S. Virgin Islands,1,332
Wallis and Futuna,681,543
West Bank,970,0
Yemen,967,421
Zambia,260,645
Zimbabwe,263,648'''
