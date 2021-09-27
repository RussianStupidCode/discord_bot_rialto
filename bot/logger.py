from datetime import datetime


def out_log(message, log_path=None):
    message = f'{message}\n'
    if log_path is None:
        print(message)
    else:
        with open(log_path, 'a', encoding='utf-8') as file:
            file.write(message)


def create_log_not_listened_author(message):
    log = f"""
=========================================
{datetime.now()}
not listened author
author: {message.author.name}
message: 
{message.content} 
=========================================
"""
    return log


def create_log_uncorrect_message(message):
    log = f"""
=========================================
{datetime.now()}
uncorrect message
author: {message.author.name}
message: 
{message.content} 
=========================================
"""
    return log


def create_log(message, mt4: str, old_message: None, is_reply=False) -> str:
    old_message_log = ""
    if old_message:
        old_message_log = f"""
old message
author: {old_message.author.name}
message: 
{old_message.content}
"""

    message_header = "its reply" if is_reply else ""
    if not is_reply and old_message is not None:
        message_header = "its edit"

    log = f"""
=========================================
{datetime.now()}
{message_header} 
author: {message.author.name}
message: 
{message.content}
{old_message_log}  
mt4: {mt4}
=========================================
"""
    return log
