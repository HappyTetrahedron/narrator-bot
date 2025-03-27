import re
import random
import subprocess
import datetime

import yaml

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
sound_files = {}


def get_text(bot, message):
    if state['mode'] == 'beekeeper':
        return message.get_text()
    if state['mode'] == 'telegram':
        return bot.message.text
    if state['mode'] == 'rocketchat':
        return message.data["msg"]


def reply(bot, message, text):
    if state['mode'] == 'beekeeper':
        message.reply(text)
    if state['mode'] == 'telegram':
        bot.message.reply_text(text, quote=False)
    if state['mode'] == 'rocketchat':
        message.reply(text)


def reply_event(bot, message, text):
    if state['mode'] == 'beekeeper':
        message.reply(ConversationMessage(
            bot.sdk,
            text=text,
            message_type=MESSAGE_TYPE_EVENT
        ))
    if state['mode'] == 'telegram':
        bot.message.reply_text(text, quote=False)
    if state['mode'] == 'rocketchat':
        message.reply(text)


def send_voice(bot, message, filename):
    if state['mode'] == 'beekeeper':
        message.reply(ConversationMessage(bot.sdk, media=[sound_files[filename]]))
    if state['mode'] == 'telegram':
        vfile = sound_files[filename]
        if isinstance(vfile, str):
            bot.message.reply_voice(vfile, quote=False)
        else:
            sent = bot.message.reply_voice(vfile, quote=False)
            vfile.close()
            sound_files[filename] = sent.effective_attachment.file_id
    if state['mode'] == 'rocketchat':
        vfile = sound_files[filename]
        bot.api.rooms_upload(message.data["rid"], vfile, tmid=message.data.get("tmid"))

def send_photo(bot, message, filename):
    if state['mode'] == 'beekeeper':
        photo = bot.sdk.files.upload_photo_from_path("meme.png")
        message.reply(ConversationMessage(bot.sdk, media=[photo]))
    if state['mode'] == 'telegram':
        bot.message.reply_photo(open(filename, 'rb'), quote=False)
    if state['mode'] == 'rocketchat':
        bot.api.rooms_upload(message.data["rid"], filename, tmid=message.data.get("tmid"))


def on_say(bot, message):
    text = get_text(bot, message)
    reply(bot, message, text.lstrip('/say').lstrip('$say').strip())


def on_joke(bot, message):
    text = get_text(bot, message)
    command = (text.lstrip('/joke').lstrip('$joke').strip())
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
        print("joke script didn't work")
        return

    send_photo(bot, message, 'meme.png')


def on_help(bot, message):
    if is_casual_chat(bot, message):
        help_text = random.choice(HELPFUL_HELP)
    else:
        help_text = PROFESSIONAL_HELP

    if state['mode'] == 'rocketchat':
        message.reply_in_thread(help_text)
        return

    reply(bot, message, help_text)


def on_ask_help(bot, message):
    if random.random() > 0.9:
        if is_casual_chat(bot, message):
            if random.random() > 0.3:
                reply_event(bot, message, "But nobody came.")
            else:
                reply_event(bot, message, "No one's around to help.")


def on_will_do(bot, message):
    if random.random() > 0.9:
        if is_casual_chat(bot, message):
            reply_event(bot, message, "But they never did.")


def on_broke(bot, message):
    if random.random() > 0.75:
        if is_casual_chat(bot, message):
            if random.random() > 0.25:
                reply(bot, message, "Did you try turning it off and on again?")
            else:
                send_voice(bot, message, 'sadtrombone.opus')


def on_wtf(bot, message):
    if random.random() > 0.90:
        if is_casual_chat(bot, message):
            send_voice(bot, message, 'perfection.opus')


def on_hangman(bot, message):
    if random.random() > 0.9:
        reply(bot, message, random.choice(ALPHABET))


def is_casual_chat(bot, message):
    if state['mode'] == 'beekeeper':
        conversation_id = message.get_conversation_id()
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
    return True


def register_sounds(bot, kwargs):
    with open('sounds.yml', 'r') as soundfile:
        sounds = yaml.load(soundfile, Loader=yaml.BaseLoader)
    for sound in sounds:
        if state['mode'] == 'beekeeper':
            sound_files[sound['file']] = bot.sdk.files.upload_file_from_path("media/{}".format(sound['file']), upload_type=FILE_UPLOAD_TYPE_VOICE)
        if state['mode'] == 'telegram':
            sound_files[sound['file']] = open("media/{}".format(sound['file']), 'rb')
        if state['mode'] == 'rocketchat':
            sound_files[sound['file']] = "media/{}".format(sound['file'])
        for command in sound['commands']:
            bot.add_handler(CommandHandler(command, (lambda bot, message, s=sound['file']: send_voice(bot, message, s)), **kwargs))


def main(options):
    if state['mode'] == 'beekeeper':
        bot = BeekeeperChatBot(config['tenant_url'], config['bot_token'])
        kwargs = {'message_types': [MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]}

    if state['mode'] == 'telegram':
        updater = Updater(config['bot_token'])
        bot = updater.dispatcher
        kwargs = {}

    if state['mode'] == 'rocketchat':
        if 'bot_token' in config:
            bot = RocketchatBot(api_token=config['bot_token'], user_id=config['bot_id'], server_url=config['server_url'])
        else:
            bot = RocketchatBot(username=config['bot_user'], password=config['bot_password'], server_url=config['server_url'])
        kwargs = {}

    register_sounds(bot, kwargs)

    bot.add_handler(CommandHandler('say', on_say, **kwargs))
    bot.add_handler(CommandHandler('joke', on_joke, **kwargs))
    bot.add_handler(CommandHandler('help', on_help))
    bot.add_handler(RegexHandler(ASK_HELP_REGEX, on_ask_help))
    bot.add_handler(RegexHandler(I_WILL_DO_IT_REGEX, on_will_do))
    bot.add_handler(RegexHandler(BROKE_REGEX, on_broke))
    bot.add_handler(RegexHandler(WTF_REGEX, on_wtf))
    bot.add_handler(RegexHandler(HANGMAN_REGEX, on_hangman))

    if state['mode'] == 'beekeeper':
        bot.start()
    if state['mode'] == 'telegram':
        updater.start_polling()
        updater.idle()
    if state['mode'] == 'rocketchat':
        asyncio.run(bot.run_forever())


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', default='config.yml', type='string', help="Path of configuration file")
    (opts, args) = parser.parse_args()
    with open(opts.config, 'r') as configfile:
        config = yaml.load(configfile, Loader=yaml.BaseLoader)
        state['casual_conversation_marker'] = config.get('casual_conversation_marker_uuid')
        state['mode'] = config['mode']
        if state['mode'] == 'rocketchat':
            from rocketchat_bot_sdk import RocketchatBot
            from rocketchat_bot_sdk import CommandHandler
            from rocketchat_bot_sdk import RegexHandler
            import asyncio
        if state['mode'] == 'beekeeper':
            from beekeeper_chatbot_sdk import BeekeeperChatBot
            from beekeeper_sdk.conversations import ConversationMessage
            from beekeeper_sdk.conversations import MESSAGE_TYPE_CONTROL
            from beekeeper_sdk.conversations import MESSAGE_TYPE_EVENT
            from beekeeper_sdk.conversations import MESSAGE_TYPE_REGULAR
            from beekeeper_sdk.files import FILE_UPLOAD_TYPE_VOICE
            from beekeeper_chatbot_sdk import CommandHandler
            from beekeeper_chatbot_sdk import RegexHandler

        if state['mode'] == 'telegram':
            from telegram.ext import CommandHandler
            from telegram.ext import RegexHandler
            from telegram.ext import Updater
    main(opts)
