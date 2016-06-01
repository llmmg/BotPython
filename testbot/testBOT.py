"""Created by Lancelot Magnin
Based on picbot's source code"""

import asyncio
import json
import aiohttp

from api import api_call
from config import DEBUG, TOKEN

RUNNING = True

"""TO DO:
    -the bot react only in his initied channel
    -the bot create vote subject and responses only
    -   from the one who started the vote (=usable in noisy groups)

    -- faire que le bot ne créer un vote que a partir de celui qui lui a dit bonjour
"""


class Bot:
    def __init__(self, token=TOKEN):
        self.token = token
        self.rtm = None
        self.state = "zero"
        self.emojDef = {}  # votes possibilities + definitions
        self.votes = []  # list of voted emoji
        self.result = {}
        self.user_name = None
        self.user_id = None

    async def sendText(self, message, channel_id, team_id):
        return await api_call('chat.postMessage', {"type": "message",
                                                   "channel": channel_id,
                                                   # "text": "<@{0}> {1}".format(user_name["user"]["name"], message),
                                                   "text": message,
                                                   "team": team_id  # ,
                                                   # "attachments": [
                                                   #  {
                                                   #     "text": ":bowtie:",
                                                   #     "fields": [
                                                   #         {
                                                   #             "title": "test",
                                                   #             "value": ":bowtie:",
                                                   #             "short": "false"
                                                   #         }
                                                   #     ]
                                                   # }]
                                                   })

    async def help(self, channel_id, team_id):
        helpMsg = "Bienvenu sur le votebot!\n" \
                  "Pour commencer un vote, il suffit de me parler, un sujet de vote + reponses possibles vous serra alors demandé.\n" \
                  "Pour clore le vote, il faut m'envoyer la commande \"close vote\"\n" \
                  "Une fois un vote fermé, on peut en créer un nouveau avec la commande \"create vote\""

        return await self.sendText(helpMsg, channel_id, team_id)

    async def error(self, channel_id, user_name, team_id):
        error = "Input error, please respect the syntax"
        return await self.sendText(error, channel_id, team_id)

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

    async def vote(self, votedEmoji):
        self.votes.append(votedEmoji)

    """**remove vote**
    used when a reaction is removed"""

    async def dessist(self, votedEmoji):
        self.votes.remove(votedEmoji)

    async def computeVote(self):
        for chx in self.emojDef.keys():
            self.result.update({chx: self.votes.count(chx)})

    async def getUser(self, message):
        self.user_id = message.get('user')
        # get user's name
        for userName in self.rtm['users']:
            if userName['id'] == self.user_id:
                print('user', userName['name'])
                self.user_name = userName['name']

    async def run(self, message):
        """do stuff with input msg"""

        channel_id = message.get('channel')
        channel_name = await api_call('channel.info', {'channel': channel_id})

        team_id = self.rtm['team']['id']
        team_name = self.rtm['team']['name']
        # print('team_name=', team_name)

        # user_id = message.get('user')
        # # get user's name
        # for userName in self.rtm['users']:
        #     if userName['id'] == user_id:
        #         print('user', userName['name'])
        #         user_name = userName['name']

        bot_id = self.rtm['self']['id']
        bot_name = self.rtm['self']['name']

        # ----------When reaction is added--------------
        if message.get('type') == 'reaction_added':
            # channel is in ['item']['channel']
            channel_id = message.get('item')['channel']
            channel_name = await api_call('channel.info', {'channel': channel_id})  # maybe useless
            print(channel_id)

            reaction = message.get('reaction')
            print('reaction:', reaction)

            # vote with reactions
            if self.state == 'votes':
                # add reaction emoji in votes
                await self.vote(":" + reaction + ":")

        elif message.get('type') == 'reaction_removed' and self.state == 'votes':
            reaction = message.get('reaction')
            await  self.dessist(":" + reaction + ":")

        # changement de presence =>useless? (')>
        # if message.get('type') == 'presence_change':
        #     user_name=message.get('user')
        #     #await self.sendText('hi!', 'G1CJ05D71', None, None)
        #     await self.sendText('hi!',channel_id ,user_name,team_id)

        # if received data is message type
        if message.get('type') == 'message':
            message_text = message.get('text')

            if self.state == 'setReactions':
                # get timestamp
                timestamp = message.get('ts')

                print('channel', channel_id)
                for key, value in self.emojDef.items():
                    print(key)
                    print(await api_call('reactions.add', {'timestamp': timestamp,
                                                           'channel': channel_id,
                                                           'name': key[1:-1]}))  # emoji's name without ':'

                # now that reactions are displayed, people can votes
                self.state = 'votes'

            if message_text:

                # if it's not the bot who send messages
                if not message.get('subtype') == 'bot_message':

                    # respond to help command
                    if message_text.split(':', 1)[0].strip() == '<@{0}>'.format(bot_id) and message_text.split(':',1)[1].strip() == 'help':
                        await self.help(channel_id, team_id)

                    else:
                        # state 'zero' is the initial state where the bot 'wait' for msg
                        if self.state == 'zero':
                            # Clear the vote before a new one is started
                            self.emojDef.clear()
                            self.votes.clear()

                            # STORE THE USER NAME FOR THE WHOLE VOTE => WILL REACT ONLY WITH THIS USER (vote subject and close vote)
                            await self.getUser(message)
                            # if message is addressed to the bot
                            if message_text.split(':', 1)[0].strip() == '<@{0}>'.format(bot_id):
                                await self.sendText(
                                    'hi ' + self.user_name + '!\n Create your vote with [Vote subject]/[emoji1=definition1, emoji2=definition2,...]',
                                    channel_id, team_id)
                                self.state = 'createVote'

                        # -----NEWS STATES TEST-> createVote / setReactions / votes / voteClosed / idleRenew
                        elif self.state == 'createVote':
                            # if message is addressed to the bot
                            message_split = message_text.split(':', 1)
                            if message_split[0].strip() == '<@{0}>'.format(bot_id):
                                # if it's the same user as the one in 'zero' state
                                if message.get('user') == self.user_id:
                                    # take the part without the '@botname'
                                    contain = message_split[1].strip().split('/', 1)

                                    subject = contain[0].strip()
                                    print(subject)
                                    responses = contain[1].strip()
                                    print(responses)

                                    await self.setVoteSubject(subject, self.user_name, team_id)
                                    await self.setVoteRep(responses, self.user_name, team_id)
                                    await self.sendText(self.subject, channel_id, team_id)

                                    self.state = 'setReactions'
                        # DEPRECATED
                        # elif self.state == 'idleRenew':
                        #     msg = message_text.split(':', 1)
                        #     if msg[0].strip() == '<@{0}>'.format(bot_id):
                        #         if msg[1].strip() == 'new vote':
                        #             await self.sendText("Quel est le sujet de votre vote?", channel_id, user_name, team_id)
                        #             self.state = 'createVote'
                        #         else:
                        #             await self.sendText("d'accord, je reste en attente :slightly_smiling_face:", channel_id,user_name, team_id)


                        # -----END NEW STATES

                        # # DEPRECATED
                        # elif self.state == 'subject':
                        #     # if message is addressed to this
                        #     message_split = message_text.split(':', 1)
                        #     if message_split[0].strip() == '<@{0}>'.format(bot_id):
                        #         # take the part without the '@botname'
                        #         await self.setVoteSubject(message_split[1].strip(), user_name, team_id)
                        #         await self.sendText(
                        #             'what\'s your vote\'s reponses? [emoji1=definition1, emoji2=definition2,...]',
                        #             channel_id,
                        #             user_name, team_id)
                        #         self.state = 'setReponses'
                        #
                        # # DEPRECATED
                        # elif self.state == 'setReponses':
                        #     # if message is addressed to this
                        #     message_split = message_text.split(':', 1)
                        #
                        #     if message_split[0].strip() == '<@{0}>'.format(bot_id):
                        #         # input need to be handled if errors occurs or if input is false
                        #         await self.setVoteRep(message_split[1].strip(), user_name, team_id)
                        #         # self.error(channel_id, user_name, team_id)
                        #
                        #         await self.sendText(self.subject + "\nVotes possibles: ", channel_id, user_name, team_id)
                        #         for key, value in self.emojDef.items():
                        #             await self.sendText(key + "->" + value, channel_id,
                        #                                 user_name, team_id)
                        #
                        #         self.state = 'setReactions'

                        elif self.state == 'votes':
                            # if message is addressed to the bot
                            msg = message_text.split(':', 1)
                            if msg[0].strip() == '<@{0}>'.format(bot_id):
                                if message.get('user') == self.user_id and msg[1].strip() == 'close vote':
                                    await self.sendText("Fin du vote:" + self.subject, channel_id, team_id)
                                    await self.computeVote()
                                    await self.sendText("Resultat du vote:" + self.subject, channel_id,team_id)
                                    for vote, nb in self.result.items():
                                        await self.sendText(
                                            "nombre de vote" + vote + self.emojDef[vote] + "=" + str(nb - 1),
                                            channel_id, team_id)
                                    await self.sendText(
                                        "Pas de vote en cours, adressez vous à moi pour créer un nouveau vote :sunglasses::bar_chart:",
                                        channel_id,team_id)

                                    self.state = 'zero'

                                    # DEPRECATED
                                    # elif self.state == 'voteClosed':
                                    #     # if message is addressed to this
                                    #     msg = message_text.split(':', 1)
                                    #     if msg[0].strip() == '<@{0}>'.format(bot_id):
                                    #         await self.sendText("Pas de vote en cours, adressez vous à moi pour créer un nouveau vote :sunglasses::bar_chart:",
                                    #                             channel_id, user_name,
                                    #                             team_id)
                                    #         self.state = 'zero'

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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)
    bot = Bot(TOKEN)
    loop.run_until_complete(bot.connection())
    loop.close()
