import re
import random

import yaml
from beekeeper_chatbot_sdk import BeekeeperChatBot
from beekeeper_chatbot_sdk import CommandHandler
from beekeeper_chatbot_sdk import RegexHandler
from beekeeper_sdk.conversations import ConversationMessage
from beekeeper_sdk.conversations import MESSAGE_TYPE_EVENT

I_WILL_DO_IT_REGEX = re.compile(r"((we|i|you)('ll|\s+should|\s+will)|can\s+you|let\s+me|should\s+(we|i))", flags=re.I)
BROKE_REGEX = re.compile(r"broke", flags=re.I)
HANGMAN_REGEX = r"Failed guesses:|Send exactly one letter to guess"

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def on_say(bot, message):
    text = message.get_text()
    message.reply(text.lstrip('/say').strip())


def on_will_do(bot, message):
    message.reply(ConversationMessage(
        bot.sdk,
        text="But they never did.",
        message_type=MESSAGE_TYPE_EVENT
    ))


def on_broke(bot, message):
    if random.random() > 0.75:
        message.reply("Did you try turning it off and on again?")


def on_hangman(bot, message):
    if random.random() > 0.9:
        message.reply(random.choice(ALPHABET))


def main(options):
    with open(options.config, 'r') as configfile:
        config = yaml.load(configfile, Loader=yaml.BaseLoader)
        bot = BeekeeperChatBot(config['tenant_url'], config['bot_token'])
        bot.add_handler(CommandHandler('say', on_say))
        bot.add_handler(RegexHandler(I_WILL_DO_IT_REGEX, on_will_do))
        bot.add_handler(RegexHandler(BROKE_REGEX, on_broke))
        bot.add_handler(RegexHandler(HANGMAN_REGEX, on_hangman))
        bot.start()


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', default='config.yml', type='string', help="Path of configuration file")
    (opts, args) = parser.parse_args()
    main(opts)
