import re
import random
import subprocess
import datetime

import yaml
from beekeeper_chatbot_sdk import BeekeeperChatBot
from beekeeper_chatbot_sdk import CommandHandler
from beekeeper_chatbot_sdk import RegexHandler
from beekeeper_sdk.conversations import ConversationMessage
from beekeeper_sdk.conversations import MESSAGE_TYPE_CONTROL
from beekeeper_sdk.conversations import MESSAGE_TYPE_EVENT
from beekeeper_sdk.conversations import MESSAGE_TYPE_REGULAR
from beekeeper_sdk.files import FILE_UPLOAD_TYPE_VOICE

I_WILL_DO_IT_REGEX = re.compile(r"((we|i|you)('ll|\s+should|\s+will)|can\s+you|let\s+me|should\s+(we|i))", flags=re.I)
ASK_HELP_REGEX = re.compile(r"^help|[^\/]help", flags=re.I)
BROKE_REGEX = re.compile(r"broke|bork", flags=re.I)
WTF_REGEX = re.compile(r"w\.?\s?t\.?\s?f\.?", flags=re.I)
HANGMAN_REGEX = r"Failed guesses:|Send exactly one letter to guess"

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
HELPFUL_HELP = [
    "You looked for help everywhere, but alas, there was none.",
    "Why are you looking at me? I'm just a narrator!",
    "Helplessness is a lifestyle.",
    "But nobody came.",
    "You turned to the bot and said: \"/help\", but the bot didn't answer.",
    "You quickly realize that you wouldn't find any help here.",
]
PROFESSIONAL_HELP = "I can send various sound effects to a chat. Try /badum or /sadtrombone, for example."

state = {}
conversation_cache = {}


def on_say(bot, message):
    text = message.get_text()
    message.reply(text.lstrip('/say').strip())


def on_joke(bot, message):
    text = message.get_text()
    command = (text.lstrip('/joke').strip())
    if ',' in command:
        parts = command.split(',')
    else:
        parts = command.split()
    if len(parts) != 2:
        return
    top = parts[0]
    bottom = parts[1]

    cmd = "jokescript/thejoke '{}' '{}' meme".format(top, bottom)

    process = subprocess.run(
        cmd,
        capture_output=True,
        shell=True,
    )
    status = process.returncode
    if status != 0:
        return
    photo = bot.sdk.files.upload_photo_from_path("meme.png")
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_badum(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/badumdish.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_trombone(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/sadtrombone.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_migros(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/migros.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_pingui(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/pingui.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_drama(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/drama.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_perfection(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/perfection.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_silence(bot, message):
    photo = bot.sdk.files.upload_file_from_path("media/silence.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    message.reply(ConversationMessage(bot.sdk, media=[photo]))


def on_help(bot, message):
    if is_casual_chat(bot, message.get_conversation_id()):
        message.reply(random.choice(HELPFUL_HELP))
    else:
        message.reply(PROFESSIONAL_HELP)


def on_ask_help(bot, message):
    if random.random() > 0.9:
        if is_casual_chat(bot, message.get_conversation_id()):
            if random.random() > 0.3:
                message.reply(ConversationMessage(
                    bot.sdk,
                    text="But nobody came",
                    message_type=MESSAGE_TYPE_EVENT
                ))
            else:
                message.reply(ConversationMessage(
                    bot.sdk,
                    text="No one's around to help",
                    message_type=MESSAGE_TYPE_EVENT
                ))


def on_will_do(bot, message):
    if random.random() > 9.0:
        if is_casual_chat(bot, message.get_conversation_id()):
            message.reply(ConversationMessage(
                bot.sdk,
                text="But they never did.",
                message_type=MESSAGE_TYPE_EVENT
            ))


def on_broke(bot, message):
    if random.random() > 0.75:
        if is_casual_chat(bot, message.get_conversation_id()):
            if random.random() > 0.25:
                message.reply("Did you try turning it off and on again?")
            else:
                on_trombone(bot, message)


def on_wtf(bot, message):
    if random.random() > 0.90:
        if is_casual_chat(bot, message.get_conversation_id()):
            on_perfection(bot, message)


def on_hangman(bot, message):
    if random.random() > 0.9:
        message.reply(random.choice(ALPHABET))


def is_casual_chat(bot, conversation_id):
    if conversation_id in conversation_cache:
        time = conversation_cache[conversation_id]['timestamp']
        if datetime.datetime.now() - time < datetime.timedelta(hours=4):
            return conversation_cache[conversation_id]['is_casual']
    members = bot.sdk.conversations.get_members_of_conversation_iterator(conversation_id, True)
    is_casual = any([member.get_id() == state['casual_conversation_marker'] for member in members])
    conversation_cache[conversation_id] = {
        'timestamp': datetime.datetime.now(),
        'is_casual': is_casual,
    }
    return is_casual


def main(options):
    with open(options.config, 'r') as configfile:
        config = yaml.load(configfile, Loader=yaml.BaseLoader)
        state['casual_conversation_marker'] = config['casual_conversation_marker_uuid']
        bot = BeekeeperChatBot(config['tenant_url'], config['bot_token'])
        bot.add_handler(CommandHandler('say', on_say, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('joke', on_joke, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('badum', on_badum, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('trombone', on_trombone, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('sadtrombone', on_trombone, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('migros', on_migros, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('pingui', on_pingui, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('drama', on_drama, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('perfection', on_perfection, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('silence', on_silence, message_types=[MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]))
        bot.add_handler(CommandHandler('help', on_help))
        bot.add_handler(RegexHandler(ASK_HELP_REGEX, on_ask_help))
        bot.add_handler(RegexHandler(I_WILL_DO_IT_REGEX, on_will_do))
        bot.add_handler(RegexHandler(BROKE_REGEX, on_broke))
        bot.add_handler(RegexHandler(WTF_REGEX, on_wtf))
        bot.add_handler(RegexHandler(HANGMAN_REGEX, on_hangman))
        bot.start()


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', default='config.yml', type='string', help="Path of configuration file")
    (opts, args) = parser.parse_args()
    main(opts)
