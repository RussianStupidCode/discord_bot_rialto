import bot.utils
import discord
import zmq
from discord.ext import commands
from bot.message_parser import MessageParser
from datetime import datetime
import bot.logger as logger


class DiscordBot:
    bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
    listened_authors = ['test-alerts', 'user', 'Alerts', 'Vendetta']
    config_dict = None
    socket = None
    parser = None
    message_store = {}
    log_path = None

    @classmethod
    def run(cls, config_path, socket_address):
        cls.init(config_path, socket_address)
        cls.bot.run(cls.config_dict['bot_data']['bot_key'])

    @classmethod
    def init(cls, config_path, socket_address):
        cls.socket = zmq.Context().socket(zmq.PUB)
        cls.socket.bind(socket_address)
        cls.config_dict = bot.utils.config_to_dict(config_path)

        date = f'{datetime.now().date()}'.replace("-", "_")
        cls.log_path = f'./log_{date}'

        currencies = [currency.upper() for currency in cls.config_dict['signal_symbols'].keys()]
        cls.parser = MessageParser(currencies, cls.config_dict['mapping'])

    @classmethod
    def message_to_dict(cls, message_content: str) -> dict:
        lines = message_content.split('\n')
        dictionary = {}
        for line in lines:
            line_dict = cls.parser.line_parse(line)
            dictionary.update(line_dict)
        return dictionary

    @classmethod
    def send_message_in_socket(cls, message: str):
        if message is None:
            return

    @classmethod
    def add_message_in_store(cls, message_id: int, message_content: str) -> dict or None:
        message_dictionary = cls.message_to_dict(message_content)
        if len(message_dictionary.keys()) == 0:
            return None

        cls.message_store = {
            message_id: {
                'content': message_content,
                'dict': message_dictionary
            }
        }
        return cls.message_store[message_id]

    @classmethod
    def clear_message(cls, message_id):
        if message_id in cls.message_store.keys():
            del cls.message_store[message_id]

    @classmethod
    def merge_message(cls, message: discord.Message, edit_or_reply_message: discord.Message) -> dict:
        lines_original_message = cls.message_store[edit_or_reply_message.id]['content'].split('\n')

        # create new_content
        lines_new_message = message.content.split('\n')
        new_content_lines = []
        for line in lines_new_message:
            if line not in lines_original_message:
                new_content_lines.append(line)

        new_content = "\n".join(new_content_lines)

        old_dict_info_not_close = {**cls.message_store[edit_or_reply_message.id]['dict']}
        # refresh close operation
        if 'close' in old_dict_info_not_close.keys():
            del old_dict_info_not_close['close']

        new_message_info = cls.add_message_in_store(edit_or_reply_message.id, new_content)
        new_message_info['dict'] = {
            **old_dict_info_not_close,
            **new_message_info['dict']
        }
        return new_message_info

    @classmethod
    def get_message_parse_info(cls, message: discord.Message,
                               edit_or_reply_message: discord.Message or None) -> dict or None:

        if edit_or_reply_message is None:
            message_info = cls.add_message_in_store(message.id, message.content)
        else:
            if edit_or_reply_message.id not in cls.message_store.keys():
                return None
            message_info = cls.merge_message(message, edit_or_reply_message)

        if message_info is None:
            return None

        dictionary = message_info['dict']
        return dictionary

    @classmethod
    def check_correct_message_dict_info(cls, message_info: dict or None) -> bool:
        if message_info is None:
            return False
        if message_info.get('currency') is None and message_info.get('operation') is None:
            return False
        if message_info.get('sl') is None and message_info.get('close') is None:
            return False
        if message_info.get('close') is not None and message_info.get('currency') is None:
            return False
        return True

    @classmethod
    def create_socket_message(cls, message_info: dict, message_id: int,
                              is_edit: bool = False, is_reply: bool = False) -> str:

        if message_info.get('close') is not None:
            result = f'd2m CloseTrade|{message_info["currency"]}|{message_info["close"]}|0||{message_id}'
            if int(message_info['close']) == 100:
                DiscordBot.clear_message(message_id)
            return result

        reply = 1 if is_reply else 0
        symbol = message_info["currency"]
        direction = message_info["operation"]
        price = message_info["cost"]
        risk = cls.config_dict['risk']['usual_risk']
        sl = message_info["sl"]
        tp = message_info.get('tp', '0')
        result = f'd2m NewMessage|{reply}|{symbol}|{direction}|{price}|{risk}|{sl}|1|{tp}|||{message_id}'

        if is_edit:
            result = result.replace('NewMessage', 'NewMessage_edit')
        return result

    @classmethod
    def send_socket_message(cls, message: str):
        cls.socket.send_string(message)


@DiscordBot.bot.event
async def on_ready():
    print('im ready')


@DiscordBot.bot.event
async def on_message(message):
    if message.author.name not in DiscordBot.listened_authors:
        log = logger.create_log_not_listened_author(message)
        logger.out_log(log, DiscordBot.log_path)
        return

    is_reply = False
    message_reference = None
    if message.reference:
        message_reference = message.reference.cached_message
        response = DiscordBot.get_message_parse_info(message, message_reference)
        is_reply = True
    else:
        response = DiscordBot.get_message_parse_info(message, None)

    if DiscordBot.check_correct_message_dict_info(response):
        socket_message = DiscordBot.create_socket_message(response, message.id, False, is_reply)
        DiscordBot.send_socket_message(socket_message)
        log_message = logger.create_log(message, socket_message, message_reference, is_reply)
    else:
        log_message = logger.create_log_uncorrect_message(message)
    logger.out_log(log_message, DiscordBot.log_path)


@DiscordBot.bot.event
async def on_message_edit(old_message, new_message):
    if old_message.author.name not in DiscordBot.listened_authors:
        log = logger.create_log_not_listened_author(new_message)
        logger.out_log(log, DiscordBot.log_path)
        return

    if old_message.content == new_message.content:
        return

    response = DiscordBot.get_message_parse_info(new_message, old_message)
    if DiscordBot.check_correct_message_dict_info(response):
        socket_message = DiscordBot.create_socket_message(response, new_message.id, True)
        DiscordBot.send_socket_message(socket_message)
        log_message = logger.create_log(new_message, socket_message, old_message)
    else:
        log_message = logger.create_log_uncorrect_message(new_message)
    logger.out_log(log_message, DiscordBot.log_path)