import votebot
import pytest


@pytest.fixture()
def bot():
    return votebot.Bot()


def test_bot_states(bot):
    assert 'zero' == bot.state


def test_content(bot):
    assert {} == bot.emojDef
    assert [] == bot.votes


