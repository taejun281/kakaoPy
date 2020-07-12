import asyncio
import packet
from bson import BSON as bson
import time
import json
import os
import httpApi
import hashlib
import requests

class Chat:
    def __init__(self, writer, packet):
        self.writer = writer

        self.rawBody = packet.toJsonBody()

        self.chatId = self.rawBody["chatLog"]["chatId"]

        self.logId = self.rawBody["chatLog"]["logId"]

        self.type = self.rawBody["chatLog"]["type"]

        self.message = self.rawBody["chatLog"]["message"]

        self.msgId = self.rawBody["chatLog"]["msgId"]

        self.authorId = self.rawBody["chatLog"]["authorId"]
       
        try:
            if "attachment" in self.rawBody["chatLog"]:
                self.attachment = json.loads(self.rawBody["chatLog"]["attachment"])
            else:
                self.attachment = {}
        except:
            pass
        
        if "li" in self.rawBody:
            self.li = self.rawBody["li"]
        else:
            self.li = 0

        self.nickName = self.rawBody["authorNickname"]

        ########## NOT WORKING ##########
        """
    async def __uploadPicture(self, path, w, h):
        f = open(path, "rb")
        filedata = f.read()
        f.close()

        filehash = hashlib.sha1(filedata).hexdigest()

        shipRecv = (await self.writer.sendPacket(packet.Packet(0, 0, "SHIP", 0, bson.encode({
            "c": self.chatId,
            "s": len(filedata),
            "t": 2,  # Photo
            "cs": filehash,
            "e": "jpg",
        })))).toJsonBody()

        host = shipRecv["vh"]
        port = shipRecv["p"]

        key = shipRecv["k"]

        cm = cryptoManager.CryptoManager()

        sock = socket.socket()
        sock.connect((host, port))

        sock.send(cm.getHandshakePacket())
        sock.send(packet.Packet(0, 0, "POST", 0, bson.encode({
            "u": self.authorId,
            "k": key,
            "t": 2,  # Photo
            "s": len(filedata),
            "c": self.chatId,
            "mid": self.msgId,
            "w": w,
            "h": h,
            "ns": False,
            "av": "8.9.1",
            "os": "android",
            "nt": 0,
            "mm": "",
            "ex": "{}",
        })).toEncryptedLocoPacket(cm))

        dataPacket = io.BytesIO()

        iv = os.urandom(16)
        enc = cm.aesEncrypt(filedata, iv)
        
        dataPacket.write(struct.pack("<I", len(enc)+len(iv)))
        dataPacket.write(iv)
        dataPacket.write(enc)

        sock.send(dataPacket.getvalue())
        
        d=sock.recv(1024)

        dataRecv = packet.Packet()
        dataRecv.readEncryptedLocoPacket(d, cm)

        body=dataRecv.toJsonBody()

        if body["status"] != 0:
            raise Exception("Image Upload Error: {}".format(body))

        return (key, filehash, len(filedata))
	"""

    async def reply(self, msg, type=0):
        return await self.sendText(msg, json.dumps({
            "attach_only": False,
            "attach_type": type,
            "mentions": [],
            "src_linkId": self.li,
            "src_logId": self.logId,
            "src_mentions": [],
            "src_message": self.message,
            "src_type": self.type,
            "src_userId": self.authorId
        }), 26)

    async def sendText(self, msg, extra="{}", t=1):
        return await self.writer.sendPacket(packet.Packet(0, 0, "WRITE", 0, bson.encode({
            "chatId": self.chatId,
            "extra": extra,
            "type": t,
            "msgId": int(time.time()/10),
            "msg": str(msg),
            "noSeen": False,
        })))

    async def delete(self):
        await self.writer.sendPacket(packet.Packet(0, 0, "DELETEMSG", 0, bson.encode({
            "chatId": self.chatId,
            "logId": self.logId
        })))

    async def hide(self, lid=0):
        if self.li:
            if lid == 0:
                lid=self.logId

            await self.writer.sendPacket(packet.Packet(0, 0, "REWRITE", 0, bson.encode({
                "c": self.chatId,
                "li": lid,
                "logId": self.logId,
                "t": 1
            })))

    async def sendPhoto(self, data, w, h):
        key = httpApi.uploadPhoto(data, self.authorId)

        u=key.replace('/talkm', "")

        url = "https://dn-m.talk.kakao.com/{}".format(key)

        return await self.sendText("", json.dumps({
            "thumbnailUrl": url,
            "thumbnailHeight": w,
            "thumbnailWidth": h,
            "url": url,
            "k": u,
            "cs": hashlib.sha1(data).hexdigest().upper(),
            "s": len(data),
            "w": w,
            "h": h,
            "mt": "image/jpeg"
        }), 2)

    async def sendPhotoPath(self, path, w, h):
        f=open(parh, "rb")
        data=f.read()
        f.close()

        return await self,sendPhoto(data, w, h)

    async def sendPhotoUrl(self, url, w, h):
        r=requests.get(url)
        return await self.sendPhoto(r.content, w, h)
