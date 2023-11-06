# Transcriber telegram bot

Принимает голосовые и аудиосообщения, после чего транскрибирует их и выдает текст пользователю.
Так же принимает ссылки с ютуба, вытаскивает аудио и транскрибирует его, либо скачивает автоматические субтитры, выдает пользователю текст.

Пока не обрабатывает "кружочки" с телеграма, нет многопоточности.

## Установка

### 1. Установить зависимости (в т.ч. Whisper):

```bash
pip install -r requirements.txt
```

### 2. Установить ffmpeg

Транскрибирует посредством [Whisper от OpenAI](https://github.com/openai/whisper), для его работы необходимо поставить ffmpeg:

```bash
# on Ubuntu or Debian:
sudo apt update && sudo apt install ffmpeg
# on Arch Linux:
sudo pacman -S ffmpeg
# on MacOS using Homebrew (https://brew.sh/):
brew install ffmpeg
# on Windows using Chocolatey (https://chocolatey.org/):
choco install ffmpeg
# on Windows using Scoop (https://scoop.sh/):
scoop install ffmpeg
```

### 3. Прописать в .env файле:

`BOT_TOKEN`, полученный в @BotFather

Необязательные но важные парамтеры:

`WHISPER_MODEL = 'base' # Модель для транскрибирования Whisper (tiny, base, large)`

`SUB_LANG = 'en' # Язык субтитров (en, ru, etc.) которые будут скачиваться с ютуба. Если не указано, то субтитры не будут скачиваться.`

## Запуск бота

```bash
python main.py
```
