from datetime import datetime


def out_log(message, log_path=None):
    message = f'{message}\n'
    try:
        file = open(log_path, 'a', encoding='utf-8')
        file.write(message)
        file.close()
    except:
        pass
    print(message)


def create_log_not_listened_author(message) -> str:
    log = f"""
=========================================
{datetime.now()}
not listened author
author: {message.author.name}
content: 
{message.content} 
=========================================
"""
    return log


def create_log_uncorrect_message(message) -> str:
    log = f"""
=========================================
{datetime.now()}
uncorrect message
author: {message.author.name}
content: 
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
content: 
{old_message.content}
"""

    message_header = "its reply" if is_reply else "new message"
    if not is_reply and old_message is not None:
        message_header = "its edit"

    log = f"""
=========================================
{datetime.now()}
{message_header} 
author: {message.author.name}
content: 
{message.content}
{old_message_log}  
mt4: {mt4}
=========================================
"""
    return log
