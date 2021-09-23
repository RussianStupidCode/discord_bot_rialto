import bot.utils
import discord
import zmq
from discord.ext import commands
from bot.message_parser import MessageParser


class DiscordBot:
    bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
    listened_authors = ['test-alerts', 'user', 'Alerts', 'Vendetta']
    config_dict = None
    socket = None
    parser = None
    message_store = {}

    @classmethod
    def run(cls, config_path, socket_address):
        cls.init(config_path, socket_address)
        cls.bot.run(cls.config_dict['bot_data']['bot_key'])

    @classmethod
    def init(cls, config_path, socket_address):
        cls.socket = zmq.Context().socket(zmq.PUB)
        cls.socket.bind(socket_address)
        cls.config_dict = bot.utils.config_to_dict(config_path)

        currencies = [currency.upper() for currency in cls.config_dict['signal_symbols'].keys()]
        cls.parser = MessageParser(currencies, cls.config_dict['signal_symbols'])

    @classmethod
    def message_to_dict(cls, message: discord.Message) -> dict:
        lines = message.content.split('\n')
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
    def add_message_in_store(cls, message: discord.Message) -> dict:
        cls.message_store = {
            message.id: {
                'content': message.content,
                'dict': cls.message_to_dict(message)
            }
        }
        return cls.message_store[message.id]

    @classmethod
    def create_message_for_socket(cls, message: discord.Message,
                                  old_or_reply_message: discord.Message or None) -> str or None:

        if old_or_reply_message is None:
            message_info = cls.add_message_in_store(message)
        return f'{message_info}'


@DiscordBot.bot.event
async def on_ready():
    print('im ready')


@DiscordBot.bot.event
async def on_message(message):
    if message.author.name not in DiscordBot.listened_authors:
        return

    response = DiscordBot.create_message_for_socket(message, None)
    print(response)


@DiscordBot.bot.event
async def on_message_edit(old_message, new_message):
    if old_message.author.name not in DiscordBot.listened_authors:
        return

    if old_message.content == new_message.content:
        return

    response = DiscordBot.create_message_for_socket(new_message, True)
    if response:
        DiscordBot.socket.send_string(response)
        print(response)
