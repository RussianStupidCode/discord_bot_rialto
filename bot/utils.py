from configparser import ConfigParser


def no_except_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return None
    return wrapper


def log(message, log_path: str = None):
    if log_path is None:
        print(message)
        return
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f'{message}\n')


def log_except_wrapper(log_path: str = None):
    def no_except(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log(e, log_path)
                return None
        return wrapper
    return no_except


def config_to_dict(config: str or ConfigParser) -> dict:
    c = config

    if isinstance(config, str):
        c = ConfigParser()
        c.read(config, encoding='utf-8')

    result = dict()

    for key, value in c.items():
        if key == 'DEFAULT':
            continue
        result[key] = dict()
        for section_key, section_value in value.items():
            result[key][section_key] = section_value

    return result
