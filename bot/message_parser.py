import re


def operation_to_number(operation_name: str) -> int:
    operation_name = operation_name.lower()
    if 'buy' in operation_name or 'long' in operation_name:
        if 'limit' in operation_name:
            return 2
        else:
            return 0
    else:
        if 'limit' in operation_name:
            return 3
        else:
            return 1


class MessageParser:
    re_number = r"\d+\.?\d+"

    def __init__(self, currencies: list, replace_currencies: dict):
        self._currencies = currencies
        self._replace_currencies = replace_currencies
        self._operations = ['BUY', 'SELL', 'SHORT', 'LONG']
        self._additional = ['LIMIT']
        self._take_profit = ['TAKE', 'TP', 'TAKEPROFIT']
        self._stop_loss = ['SL', 'STOP', 'STOPLOSS']
        self._closed = ['CLOSE', 'CLOSED']
        self._closed_additional = ['HALF', 'PARTIAL']
        self._patterns = {
            'currency': self._get_currency_pattern(),
            'operation': self._get_operation_pattern(),
            'additional': self._get_additional_pattern(),
            'sl': self._get_stop_loss_pattern(),
            'tp': self._get_take_profit_pattern(),
            'close': self._get_close_pattern(),
            'close_additional': self._get_close_additional_pattern()
        }

        self._line_to_dict = {
            'currency': self._get_currency_dict,
            'operation': self._get_operation_dict,
            'sl': self._get_stop_loss_dict,
            'tp': self._get_take_profit_dict,
            'close': self._get_close_dict
        }

    @staticmethod
    def _get_simple_words_pattern(pattern_words: list) -> re.Pattern:
        words = "|".join(pattern_words)
        return re.compile(fr".*({words})\b", re.VERBOSE | re.ASCII | re.IGNORECASE)

    @staticmethod
    def _get_word_number_pattern(pattern_words: list) -> re.Pattern:
        words = "|".join(pattern_words)
        return re.compile(fr".*({words})\b"
                          fr"[^\d]*({MessageParser.re_number})", re.VERBOSE | re.ASCII | re.IGNORECASE)

    def _get_currency_pattern(self) -> re.Pattern:
        return self._get_simple_words_pattern(self._currencies)

    def _get_operation_pattern(self) -> re.Pattern:
        return self._get_word_number_pattern(self._operations)

    def _get_additional_pattern(self) -> re.Pattern:
        return self._get_simple_words_pattern(self._additional)

    def _get_take_profit_pattern(self) -> re.Pattern:
        return self._get_word_number_pattern(self._take_profit)

    def _get_stop_loss_pattern(self) -> re.Pattern:
        return self._get_word_number_pattern(self._stop_loss)

    def _get_close_pattern(self) -> re.Pattern:
        return self._get_simple_words_pattern(self._closed)

    def _get_close_additional_pattern(self) -> re.Pattern:
        return self._get_simple_words_pattern(self._closed_additional)

    def _get_currency_dict(self, line: str) -> dict:
        match = self._patterns['currency'].match(line)
        if match is None:
            return {}
        currency = match.group(1).upper()
        if currency in self._replace_currencies.keys():
            currency = self._replace_currencies[currency]
        return {'currency': currency}

    def _get_operation_dict(self, line: str) -> dict:
        match = self._patterns['operation'].match(line)
        if match is None:
            return {}
        operation_name = match.group(1)
        operation_cost = match.group(2)

        additional = self._patterns['additional'].match(line)
        if additional is None:
            additional = ''

        operation_name = f'{operation_name}{additional}'
        return {'operation': operation_to_number(operation_name), 'cost': operation_cost}

    def _get_stop_loss_dict(self, line) -> dict:
        match = self._patterns['sl'].match(line)
        if match is None:
            return {}

        sl_name = match.group(1)
        sl_cost = match.group(2)
        return {'sl': sl_cost}

    def _get_take_profit_dict(self, line) -> dict:
        match = self._patterns['tp'].match(line)
        if match is None:
            return {}

        tp_name = match.group(1)
        tp_cost = match.group(2)
        return {'tp': tp_cost}

    def _get_close_dict(self, line) -> dict:
        match = self._patterns['close'].match(line)
        if match is None:
            return {}

        additional = self._patterns['close_additional'].match(line)
        close_percent = 100
        if additional is not None:
            close_percent = 50
        return {'close': close_percent}

    def get_dict_line(self, line) -> dict:
        result = {}
        for key, value in self._line_to_dict.items():
            dictionary = value(line)
            result.update(dictionary)
        return result

    def line_parse(self, line):
        return self.get_dict_line(line)


if __name__ == "__main__":
    m = MessageParser(['GBPJPY', 'GOLD', 'EURGBP'], {'EURGBP': 'GOLD'})
    res = m.line_parse("GBPJPY SELL @ LIMIT @ 151.60")
    print(res)
    print(m.line_parse('TP 123.1'))
    print(m.line_parse('MOVE sl  @ 123'))
    print(m.line_parse('close @ 12 with'))