"""Sample Slack ping bot using asyncio and websockets."""
import asyncio
import json
import aiohttp

from api import api_call
from config import DEBUG, TOKEN

RUNNING = True


# test
# class Vote:
#     def __init__(self, subject='noSubject'):
#         self.state = 'needASubject'
#         self.subject
#         self.rep = ()  # rep list
#
#     def setSubject(self, subject):
#         self.subject = subject
#
#     def addRep(self, rep):
#         self.rep = rep


class Bot:
    def __init__(self, token=TOKEN):
        self.token = token
        self.rtm = None
        self.state = "zero"
        self.emojDef = {}  # votes possibilities + definitions
        self.votes = []  # list of voted emoji
        self.result = {}

    async def sendText(self, message, channel_id, user_name, team_id):
        return await api_call('chat.postMessage', {"type": "message",
                                                   "channel": channel_id,
                                                   # "text": "<@{0}> {1}".format(user_name["user"]["name"], message),
                                                   "text": message,
                                                   "team": team_id})

    async def help(self, channel_id, user_name, team_id):
        helpMsg = "Bienvenu sur le votebot!"
        return await self.sendText(helpMsg, channel_id, user_name, team_id)

    async def error(self, channel_id, user_name, team_id):
        error = "Input error, please respect the syntax"
        return await self.sendText(error, channel_id, user_name, team_id)

    async def setVoteSubject(self, subject, user_name, team_id):
        self.subject = subject

    async def setVoteRep(self, possibleRep, user_name, team_id):
        # {emoj:'def',emoj2:'def2'}

        choices = possibleRep.split(',')
        for emoj in choices:
            if "=" not in emoj:
                self.error
                break
            emoj = emoj.split("=")
            self.emojDef.update({emoj[0]: emoj[1]})  # emojDef=reponses possible
        # output test
        print(self.emojDef)

    async def vote(self, votedEmoji, channel_id, user_name, team_id):
        self.votes.append(votedEmoji)

    async def computeVote(self):
        for chx in self.emojDef.keys():
            self.result.update({chx: self.votes.count(chx)})

    # async def updateVars(self,message):
    #     # ---TEST FUNCTION---
    #
    #     self.channel_id = message.get('channel')
    #     channel_name = await api_call('channel.info', {'channel': message.get('channel')})
    #
    #     self.team_id = self.rtm['team']['id']
    #     team_name = self.rtm['team']['name']
    #
    #     # a verifier si non inversé
    #     user_id = message.get('user')
    #     user_name = await api_call('users.info', {'user': message.get('user')})
    #
    #     bot_id = self.rtm['self']['id']
    #     bot_name = self.rtm['self']['name']

    async def run(self, message):
        """do stuff with input msg"""

        # global
        channel_id = message.get('channel')
        channel_name = await api_call('channel.info', {'channel': message.get('channel')})

        team_id = self.rtm['team']['id']
        team_name = self.rtm['team']['name']

        # a verifier si non inversé
        user_id = message.get('user')
        user_name = await api_call('users.info', {'user': message.get('user')})

        bot_id = self.rtm['self']['id']
        bot_name = self.rtm['self']['name']

        # lors d'une réaction
        if message.get('type') == 'reaction_added':
            reaction = message.get('reaction')
            print('reaction:', reaction)
            if self.state == 'votes':
                await self.vote(":" + reaction + ":", channel_id, user_name, team_id)

        # changement de presence
        if message.get('type') == 'presence_change':
            await self.sendText('hi!', 'G1CJ05D71', None, None)

        # si un message est reçu
        if message.get('type') == 'message':  # or message.get('type') == 'reaction_added':
            # channel_id = message.get('channel')
            # channel_name = await api_call('channel.info', {'channel': message.get('channel')})
            #
            # team_id = self.rtm['team']['id']
            # team_name = self.rtm['team']['name']
            #
            # # a verifier si non inversé
            # user_id = message.get('user')
            # user_name = await api_call('users.info', {'user': message.get('user')})
            #
            # bot_id = self.rtm['self']['id']
            # bot_name = self.rtm['self']['name']

            message_text = message.get('text')

            # if isinstance(message_text, str):
            #     # when the bot reply, his message is read and replied to.
            #     # so if the input msg is not from the bot then the bot reply
            #     # else not
            #     if not message.get('subtype') == 'bot_message':
            #         print("input: ", message_text)
            #         if message_text == 'startVote':
            #             self.initVote(user_name, team_id)
            #
            #         else:
            #             print(await self.sendText(message_text + " unknow command", channel_id, user_name, team_id))
            #             message_split = message_text.split(':', 1)
            #             result = message_split[0].strip()
            #             print("return: ", result)
            # format(bot_id):
            #             #     core_text = message_split[1].strip()
            #             #     action = self.api.get(core_text) or self.error
            #             #     print(await action(channel_id, user_name, team_id))
            if isinstance(message_text, str):
                if not message.get('subtype') == 'bot_message':
                    if self.state == 'zero':
                        await self.sendText('what\'s your vote subject?', channel_id, user_name, team_id)
                        self.state = 'subject'

                    elif self.state == 'subject':
                        await self.setVoteSubject(message_text, user_name, team_id)
                        await self.sendText(
                            'what\'s your vote\'s reponses? [emoji1=definition1, emoji2=definition2,...]', channel_id,
                            user_name, team_id)
                        self.state = 'setReponses'

                    elif self.state == 'setReponses':
                        # input need to be handled if errors occurs or if input is false
                        await self.setVoteRep(message_text, user_name, team_id)
                        # self.error(channel_id, user_name, team_id)

                        await self.sendText(self.subject + "\nVotes possibles: ", channel_id, user_name, team_id)

                        for key, value in self.emojDef.items():
                            await self.sendText(key + "->" + value, channel_id,
                                                user_name, team_id)
                        self.state = 'votes'

                    elif self.state == 'votes':
                        if not message_text == 'close vote':
                            await self.vote(message_text, channel_id, user_name, team_id)
                        else:
                            self.state = 'voteClosed'
                            await self.sendText("Fin du vote:" + self.subject, channel_id, user_name, team_id)
                            await self.computeVote()
                            await self.sendText("Resultat du vote:" + self.subject, channel_id, user_name, team_id)
                            for vote, nb in self.result.items():
                                await self.sendText("nombre de vote" + vote + self.emojDef[vote] + "=" + str(nb),
                                                    channel_id,
                                                    user_name, team_id)

                    elif self.state == 'voteClosed':
                        await self.sendText("Pas de vote en cours,nouveau vote?[y,n]", channel_id, user_name, team_id)
                        if message_text == 'y' and not message.get('subtype') == 'bot_message':
                            await self.sendText("Quel est le sujet de votre vote?", channel_id, user_name, team_id)
                            self.state == 'subject'
                        else:
                            await self.sendText("d'accord, je reste en attente :slightly_smiling_face:", channel_id, user_name, team_id)

    async def connection(self):
        self.rtm = await api_call('rtm.start')
        assert self.rtm['ok'], self.rtm['error']

        with aiohttp.ClientSession() as client:
            async with client.ws_connect(self.rtm["url"]) as ws:
                async for msg in ws:
                    assert msg.tp == aiohttp.MsgType.text
                    message = json.loads(msg.data)
                    print(message)
                    asyncio.ensure_future(self.run(message))


# async def producer():
#     """Produce a ping message every 10 seconds."""
#     await asyncio.sleep(10)
#     return json.dumps({"type": "ping"})
#
#
# async def consumer(message):
#     """Consume the message by printing them."""
#     print(message)
#
# async def bot(token):
#     """Create a bot that joins Slack."""
#     loop = asyncio.get_event_loop()
#     with aiohttp.ClientSession(loop=loop) as client:
#         async with client.post("https://slack.com/api/rtm.start",
#                                data={"token": TOKEN}) as response:
#             assert 200 == response.status, "Error connecting to RTM."
#             rtm = await response.json()
#
#     async with websockets.connect(rtm["url"]) as ws:
#         while RUNNING:
#             listener_task = asyncio.ensure_future(ws.recv())
#             producer_task = asyncio.ensure_future(producer())
#
#             done, pending = await asyncio.wait(
#                 [listener_task, producer_task],
#                 return_when=asyncio.FIRST_COMPLETED
#             )
#
#
#             for task in pending:
#                 task.cancel()
#
#             if listener_task in done:
#                 message = listener_task.result()
#                 await consumer(message)
#
#             if producer_task in done:
#                 message = producer_task.result()
#                 await ws.send(message)
#
#
# def stop():
#     """Gracefully stop the bot."""
#     global RUNNING
#     RUNNING = False
#     print("Stopping... closing connections.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)
    bot = Bot(TOKEN)
    loop.run_until_complete(bot.connection())
    loop.close()
