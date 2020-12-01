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


def reply(bot, message, text):
    if state['mode'] == 'beekeeper':
        message.reply(text)
    if state['mode'] == 'telegram':
        bot.message.reply_text(text)


def reply_event(bot, message, text):
    if state['mode'] == 'beekeeper':
        message.reply(ConversationMessage(
            bot.sdk,
            text=text,
            message_type=MESSAGE_TYPE_EVENT
        ))
    if state['mode'] == 'telegram':
        bot.message.reply_text(text)


def send_voice(bot, message, filename):
    if state['mode'] == 'beekeeper':
        message.reply(ConversationMessage(bot.sdk, media=[sound_files[filename]]))
    if state['mode'] == 'telegram':
        vfile = sound_files[filename]
        if isinstance(vfile, str):
            bot.message.reply_voice(vfile)
        else:
            sent = bot.message.reply_voice(vfile)
            vfile.close()
            sound_files[filename] = sent.effective_attachment.file_id


def send_photo(bot, message, filename):
    if state['mode'] == 'beekeeper':
        photo = bot.sdk.files.upload_photo_from_path("meme.png")
        message.reply(ConversationMessage(bot.sdk, media=[photo]))
    if state['mode'] == 'telegram':
        bot.message.reply_photo(open(filename, 'rb'))


def on_say(bot, message):
    text = get_text(bot, message)
    reply(bot, message, text.lstrip('/say').strip())


def on_joke(bot, message):
    text = get_text(bot, message)
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

    send_photo(bot, message, 'meme.png')


def on_badum(bot, message):
    send_voice(bot, message, 'badum')


def on_trombone(bot, message):
    send_voice(bot, message, 'trombone')


def on_migros(bot, message):
    send_voice(bot, message, 'migros')


def on_pingui(bot, message):
    send_voice(bot, message, 'pingui')


def on_drama(bot, message):
    send_voice(bot, message, 'drama')


def on_perfection(bot, message):
    send_voice(bot, message, 'perfection')


def on_silence(bot, message):
    send_voice(bot, message, 'silence')


def on_help(bot, message):
    if is_casual_chat(bot, message):
        reply(bot, message, random.choice(HELPFUL_HELP))
    else:
        reply(bot, message, PROFESSIONAL_HELP)


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
                on_trombone(bot, message)


def on_wtf(bot, message):
    if random.random() > 0.90:
        if is_casual_chat(bot, message):
            on_perfection(bot, message)


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


def init_sound_files(bot):
    if state['mode'] == 'beekeeper':
        sound_files['badum'] = bot.sdk.files.upload_file_from_path("media/badumdish.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['trombone'] = bot.sdk.files.upload_file_from_path("media/sadtrombone.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['migros'] = bot.sdk.files.upload_file_from_path("media/migros.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['pingui'] = bot.sdk.files.upload_file_from_path("media/pingui.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['drama'] = bot.sdk.files.upload_file_from_path("media/drama.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['perfection'] = bot.sdk.files.upload_file_from_path("media/perfection.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
        sound_files['silence'] = bot.sdk.files.upload_file_from_path("media/silence.opus", upload_type=FILE_UPLOAD_TYPE_VOICE)
    if state['mode'] == 'telegram':
        sound_files['badum'] = open("media/badumdish.opus", 'rb')
        sound_files['trombone'] = open("media/sadtrombone.opus", 'rb')
        sound_files['migros'] = open("media/migros.opus", 'rb')
        sound_files['pingui'] = open("media/pingui.opus", 'rb')
        sound_files['drama'] = open("media/drama.opus", 'rb')
        sound_files['perfection'] = open("media/perfection.opus", 'rb')
        sound_files['silence'] = open("media/silence.opus", 'rb')


def main(options):
    if state['mode'] == 'beekeeper':
        bot = BeekeeperChatBot(config['tenant_url'], config['bot_token'])
        kwargs = {'message_types': [MESSAGE_TYPE_REGULAR, MESSAGE_TYPE_CONTROL]}

    if state['mode'] == 'telegram':
        updater = Updater(config['bot_token'])
        bot = updater.dispatcher
        kwargs = {}

    init_sound_files(bot)
    bot.add_handler(CommandHandler('say', on_say, **kwargs))
    bot.add_handler(CommandHandler('joke', on_joke, **kwargs))
    bot.add_handler(CommandHandler('badum', on_badum, **kwargs))
    bot.add_handler(CommandHandler('trombone', on_trombone, **kwargs))
    bot.add_handler(CommandHandler('sadtrombone', on_trombone, **kwargs))
    bot.add_handler(CommandHandler('migros', on_migros, **kwargs))
    bot.add_handler(CommandHandler('pingui', on_pingui, **kwargs))
    bot.add_handler(CommandHandler('drama', on_drama, **kwargs))
    bot.add_handler(CommandHandler('perfection', on_perfection, **kwargs))
    bot.add_handler(CommandHandler('silence', on_silence, **kwargs))
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


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', default='config.yml', type='string', help="Path of configuration file")
    (opts, args) = parser.parse_args()
    with open(opts.config, 'r') as configfile:
        config = yaml.load(configfile, Loader=yaml.BaseLoader)
        state['casual_conversation_marker'] = config['casual_conversation_marker_uuid']
        state['mode'] = config['mode']
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
