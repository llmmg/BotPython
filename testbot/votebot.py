"""Created by Lancelot Magnin \n
    *Based on picbot's source code*

"""

import asyncio
import json
import aiohttp

from api import api_call
from config import DEBUG, TOKEN

RUNNING = True


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
    """This function send text in the chat"""
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
    """Help message function"""
    helpMsg = "Bienvenu sur le votebot!\n" \
              "Pour commencer un vote, il suffit de m'envoyer la commande 'create vote'," \
              " Un sujet de vote + reponses possibles vous serra alors demandé.\n" \
              "Pour clore le vote, il faut m'envoyer la commande \"close vote\"\n" \
              "Une fois un vote fermé, on peut en créer un nouveau avec la commande \"create vote\""

    return await self.sendText(helpMsg, channel_id, team_id)


async def error(self, channel_id, user_name, team_id):
    """Error function, send an error message"""
    error = "Input error, please respect the syntax"
    return await self.sendText(error, channel_id, team_id)


async def setVoteSubject(self, subject, user_name, team_id):
    """Set the question of the vote"""
    self.subject = subject


async def setVoteRep(self, possibleRep, user_name, team_id):
    """Set the possible responses of the vote \n
    - the votes possibilities are split by the '='. \n
    - emoji and definition are saved
    """
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


async def vote(self, voted_emoji):
    """
    **DEPRECATED**\n
    Store a vote \n
        - the votes aren't saved anymore. the number of reaction define the result of the vote
    """
    self.votes.append(voted_emoji)
    print(self.votes)
    print(voted_emoji)



async def dessist(self, voted_emoji):
    """**DEPRECATED**
    remove vote \n
     same as vote function
    - Used when a reaction is removed
    """

    self.votes.remove(voted_emoji)


async def compute_vote(self, channel_id):
    """Count the number of reactions \n
    - Called when a vote is closed
    """
    for chx in self.emojDef.keys():
        reactions = await api_call('reactions.get', {'channel': channel_id,
                                                     'timestamp': self.timestamp})
        reactions = reactions['message']['reactions']
        for name in reactions:
            if chx.strip(":") == name['name']:
                print(name['name'])
                reactions = name
        print(reactions)
        self.result.update({chx: reactions['count']})


async def get_user(self, message):
    """Set the id and name of user from the received data's
    """
    self.user_id = message.get('user')
    # get user's name
    for userName in self.rtm['users']:
        if userName['id'] == self.user_id:
            print('user', userName['name'])
            self.user_name = userName['name']


async def run(self, message):
    """

        Main Function
        -------------
        This function is called everytime a data is received trougth the connexion. \n

        State machine
        +++++++++++++

        The vote process have four states:\n
        - zero \n
            * This state is the initial state of the bot. it wait the instruction of user. \n
                *User can start the vote or get help command*.\n
                 When create commande is insert, state switch to 'createVote'

        - createVote \n
            * In this state, the bot ask user to give the subject and the emojis for the vote.
                When user have define his vote, the state goes to setReactions

        - setReactions\n
            * The reaction are add to the slack message (in the chat...) so users can easily click to vote
                go to state vote when all reactions have been added

        - vote \n
            * It wait the user to close the vote or ask for help command \n
                When user close the vote, the state go to 'zero'

    """

    # ----------When reaction is added--------------
    #  DEPRECATED ,adding votes in list 'vote' is now useless
    # =>Count the nb of reaction in the interface
    # ----------------------------------
    # if message.get('type') == 'reaction_added':
    #
    #     # channel is in ['item']['channel']
    #     channel_id = message.get('item')['channel']
    #     # channel_name = await api_call('channel.info', {'channel': channel_id})  # maybe useless
    #     print(channel_id)
    #
    #     reaction = message.get('reaction')
    #     print('reaction:', reaction)
    #
    #     # vote with reactions
    #     if self.state == 'votes':
    #         # add reaction emoji in votes
    #         await self.vote(":" + reaction + ":")
    #
    # elif message.get('type') == 'reaction_removed' and self.state == 'votes':
    #     reaction = message.get('reaction')
    #     await self.dessist(":" + reaction + ":")

    # changement de presence =>useless? (')>
    # if message.get('type') == 'presence_change':
    #     user_name=message.get('user')
    #     #await self.sendText('hi!', 'G1CJ05D71', None, None)
    #     await self.sendText('hi!',channel_id ,user_name,team_id)

    # if received data is message type
    if message.get('type') == 'message':

        channel_id = message.get('channel')
        channel_name = await api_call('channel.info', {'channel': channel_id})

        team_id = self.rtm['team']['id']
        team_name = self.rtm['team']['name']

        # print('team_name=', team_name)

        bot_id = self.rtm['self']['id']
        bot_name = self.rtm['self']['name']

        message_text = message.get('text')

        if self.state == 'setReactions':
            # get timestamp
            self.timestamp = message.get('ts')

            print('channel', channel_id)
            for key, value in self.emojDef.items():
                print(key)
                print(await api_call('reactions.add', {'timestamp': self.timestamp,
                                                       'channel': channel_id,
                                                       'name': key[1:-1]}))  # emoji's name without ':'

            # now that reactions are displayed, people can votes
            self.state = 'votes'

        # if it's not the bot who send messages
        if message_text and not message.get('subtype') == 'bot_message':
            # respond to help command
            msg = message_text.split(':', 1)
            if msg[0].strip() == '<@{0}>'.format(bot_id) and msg[1].strip() == 'help':
                await self.help(channel_id, team_id)

            else:
                # state 'zero' is the initial state where the bot 'wait' for msg
                if self.state == 'zero':
                    # Clear the vote before a new one is started
                    self.emojDef.clear()
                    self.votes.clear()

                    # STORE THE USER NAME FOR THE WHOLE VOTE
                    # => WILL REACT ONLY WITH THIS USER (vote subject and close vote)
                    await self.get_user(message)

                    # if message is addressed to the bot and message is 'create vote'
                    if msg[0].strip() == '<@{0}>'.format(bot_id) and msg[1].strip() == 'create vote':
                        await self.sendText(
                            'hi ' + self.user_name + '!\n Create your vote with [Vote subject]/[emoji1=definition1,'
                                                     ' emoji2=definition2,...]',
                            channel_id, team_id)
                        self.state = 'createVote'
                    else:
                        # if command is wrong, call the help
                        await self.help(channel_id, team_id)

                # user create a vote (question+emotes...)
                elif self.state == 'createVote':
                    # if message is addressed to the bot
                    if msg[0].strip() == '<@{0}>'.format(bot_id):
                        # if it's the same user as the one in 'zero' state
                        if message.get('user') == self.user_id:
                            # take the part without the '@botname'
                            contain = msg[1].strip().split('/', 1)

                            subject = contain[0].strip()
                            print(subject)
                            responses = contain[1].strip()
                            print(responses)

                            await self.setVoteSubject(subject, self.user_name, team_id)
                            await self.setVoteRep(responses, self.user_name, team_id)
                            await self.sendText(self.subject, channel_id, team_id)

                            self.state = 'setReactions'

                elif self.state == 'votes':

                    # if message is addressed to the bot
                    if msg[0].strip() == '<@{0}>'.format(bot_id):

                        # check that's the user who created the vote speaking
                        if message.get('user') == self.user_id and msg[1].strip() == 'close vote':
                            await self.sendText("Fin du vote:" + self.subject, channel_id, team_id)
                            await self.compute_vote(channel_id)
                            await self.sendText("Resultat du vote:" + self.subject, channel_id, team_id)
                            for vote, nb in self.result.items():
                                print(nb)
                                await self.sendText(
                                    "nombre de vote" + vote + self.emojDef[vote] + "=" + str(nb - 1),
                                    channel_id, team_id)
                            await self.sendText(
                                "Pas de vote en cours,"
                                " adressez vous à moi pour créer un nouveau vote :sunglasses::bar_chart:",
                                channel_id, team_id)

                            self.state = 'zero'
                        else:
                            await self.help(channel_id, team_id)


async def connection(self):
    """Connect bot to Slack"""
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
