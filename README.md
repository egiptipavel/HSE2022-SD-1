# Software Design

![alt text](https://github.com/eshelukhina/HSE2022-SD/blob/task1/cliArch.png?raw=true)

* **App** – Точка входа в приложение. Использует другие модули для обработки запросов.

* **I/O** – Компонента, отвечающая за работу с входным и выходным потоками данных (в нашем случае с консолью).

* **Parser** – Парсит строку и возвращает очередь команд для выполнения.<br>
  *Описание:* <br>
  Получаем на вход строку. Выполняем подстановку: для этого пройдемся по строчке запоминая, в каких самых внешних кавычках мы находимся (если находимся вообще). Будем искать конструкции $varName. Если внешняя кавычка одинарная, то идем до следующей одинарной без подстановок, если двойная, то идем до следующей двойной и делаем подстановки (даже если $varName находится внутри одинарных кавычек). Если необходима подстановка переменной, которая отсутствует в окружении, подставляем пустую строку. Передаем строку лексеру, который разобьет ее на токены. 

  Token List:
  - CAT, где CAT=’cat’
  - ECHO, где ECHO=’echo’
  - WC, где WC=’wc’
  - PWD, где PWD=’pwd’
  - EXIT, где EXIT=’exit’
  - PIPE, где PIPE=’|’
  - EQ, где EQ=’=’
  - ID, где ID удовлетворяет следующему regex’у `[^\s]+`
  - VARNAME, где VARNAME удовлетворяет следующему regex’у `[a-zA-Z_][a-zA-Z0-9_]*`
  - PROCESSNAME, где PROCESSNAME удовлетворяет следующему regex’у `[a-zA-Z0-9_-]+`

  Далее полученные токены передаем парсеру, и строим AST дерево по следующей грамматике:

  ```
  args:  | ID
         | ID args

  expr:  | expr PIPE expr
         | ECHO args
         | CAT args
         | WC args
         | PWD args
         | EXIT args
         | VARNAME EQ ID
         | PROCESSNAME args
  ```
  Где args - аргументы, передаваемые в команды, а expr - выражение, которое хотим распарсить.

  После этого проходимся по построенному AST слева направо и создаем очередь из команд, воспользовавшись **Command Storage**, который хранит мапу String → лямбду, которая вызывает конструктор и возвращает экземпляр класса при передаче ей аргументов.

  При создании команд CAT, WC, EQ убираем у ID внешние кавычки, если таковые имеются (`cat file.txt` эквивалентно `cat ‘file.txt’`)

  Если на каком либо из этапов произошла ошибка (например при токенизации строки), необходимо бросить исключение с описанием ошибки.



* **Substitution** – Модуль, отвечающий за подстановку переменных в строку. Вырезает содержимое одинарных кавычек. Далее выполняет подстановку на всей строке: находит все переменные `$text` и выполняет подстановку из Environment. Возвращает в строку содержимое одинарных кавычек (по порядковому номеру). Выполняется для второй фазы.

* **Environment** – Хранилище переменных из окружения. <br>
  *Описание:* <br>
  Храним мапу со всеми переменными окружения.


* **Executor** – Элемент программы, который отвечает за запуск команд из очереди<br>
  *Описание:* <br>
  Принимает на вход очередь команд. Создает и поддерживает в корректном состоянии класс Context, в котором будут лежать:
  - Общее кол-во команд в цепочке команд
  - Номер текущей исполняемой команды
  - Строка с ошибками
  - Входная строка
  
  Последовательно выполняет команды. После выполнения очередной команды обновляет номер текущей исполняемой команды, результат команды присваивает во входную строку. Если при выполнении команды произошла ошибка (строка с ошибками не пуста), то выводим ее через **I/O** и прекращаем выполнение команд. После обработки всех команд передаем входную строку в **I/O** для отображения результата пользователю. 

* **FileManager** – Компонента, отвечающая за работу с файловой системой. Необходима для выполнения базовых операций с файлами.<br>
  *Описание:* <br>
  Список методов:
  - getFileType - получает на вход путь до файла. Проверяет, что файл существует и возвращает Enum из трех значений: directory, file, unknown. Directory - если путь относится к директории, file - к файлу, unknown - если не существует такого файла/директории. 
  - getFileContent - возвращает содержимое файла
  - getCurrentDirectory - Получить текущую директорию


* **Command** – Интерфейс от которого наследуются все команды. Содержит единственный метод execute, который выполняет команду, получая на вход **Context**  и возвращает результирующую строку.

* **ExternalCommand** – запускаем через subprocess (python), передаем текущий **Environment**.

* **Описание команд:**
  - cat [FILE] — вывести на экран содержимое файла;<br>
  *Описание:*  Отображение текстовых файлов. Получаем на вход параметры, которые нам передали. Затем проверяем их корректность – на данный момент проверяем существует ли такой файл (через **FileManager**). Если передали несколько файлов подряд, пишем их последовательно, объединяя содержимое в потоке выхода. 
  Если же хотя бы один из аргументов не является файлом, то пишем в поток ошибок, что такого файла не существует, либо что обратились к директории. 

  - echo — вывести на экран свой аргумент (или аргументы);<br>
  *Описание:*  Выводит переданные аргументы по следующему принципу: отдельно смотрим на каждый переданный аргумент. Если же он находится в двойных или одинарных кавычках, то убираем их (в случае, когда внутри одних кавычек есть другие, убираем только внешние). Далее просто пишем все переданные аргументы в поток вывода. 

  - wc [FILE] — вывести количество строк, слов и байт в файле;<br>
  *Описание:*  Смотрим на переданные аргументы. Через **FileManager** проверяем существуют ли такие файлы, затем обрабатываем их содержимое в переданном порядке, затем объединяем результат и пишем в поток вывода. Если аргументов не передано, то два варианта:
    - Если WC вызвана через pipeline, то обрабатываем данные из входного потока как файл
    - Пишем в поток ошибок, что аргумент не передан
    
    Входной поток игнорируется, если у WC есть аргументы

  - pwd — распечатать текущую директорию;<br>
  *Описание:*  Выводит пользователю текущую директорию используя **FileManager**

  - exit — выйти из интерпретатора. <br>
    *Описание:*  Рассмотрим несколько случаев. 
    - Exit встретился внутри pipeline (будем смотреть на номер команды и общее количество команд, исходя из этого делать выводы) – возвращаем пустой выходной поток.
    - Exit введен как стандартная команда – завершаемся (в глобальном флаге exit ставим true) и пишем в поток вывода, что процесс завершен. 
  - = — обновляет/добавляет значение переменной в **Environment**

