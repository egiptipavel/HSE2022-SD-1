from typing import List

from optional.optional import Optional

from Executor.context import Context
from Executor.file_manager import FileManager


class Cat:
    def __init__(self, args: List[str]):
        self.args = args

    def execute(self, context: Context):
        """
        Проверяет, что все аргументы это пути до существующих файлов.
        Получает содержимое этих файлов и записывает его в Context
        """
        for arg in self.args:
            if not FileManager.is_file(arg):
                context.error = Optional.of('cat: {}: No such file'.format(arg))
                return
        result = ''
        for arg in self.args:
            result += FileManager.get_file_content(arg)
        context.state = Optional.of(result)

    def __str__(self):
        return f'CAT {self.args}'

    def __eq__(self, other):
        if isinstance(other, Cat):
            return self.args == other.args
        return False
