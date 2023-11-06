
import logging
import asyncio
import yt_dlp
import whisper
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineQueryResultArticle, InputTextMessageContent

import os
import traceback
from pydub import AudioSegment
from pydub.silence import detect_silence
import requests
import json

from dotenv import load_dotenv
load_dotenv()

bot_token = os.environ.get('BOT_TOKEN')
whisper_model = os.environ.get('WHISPER_MODEL') or 'tiny'
SUB_LANG = os.environ.get('SUB_LANG')

model = whisper.load_model(whisper_model)


# TODO update code:
async def download_audio(update, context):
    # user = update.message.from_user
    # message = update.message
    
    f_name = f"{user.id}-{message.id}.ogg"
    await asyncio.sleep(2)
    await event.respond("Загрузка больших файлов может занять некоторое время.\n")
    # await context.message.reply_text

    await bot.download_media(message.audio if message.audio else message.voice, f_name)

    await event.respond("Аудиофайл "+f_name+" успешно сохранен.\n"
                                        "Начинаю транскрипцию. \n"
                                        "Ожидайте ответа")

    result = await trnscrb(event, f_name)


async def download_link(url, filename, update):
    answer = ''

    # await con.respond("Начинаю загрузку файла")
    await update.message.reply_text("Начинаю загрузку файла")

    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
    video_title = info.get('title', None)

    if SUB_LANG and info['automatic_captions'][SUB_LANG]:
     for s_url in info['automatic_captions'][SUB_LANG]:
        if s_url['ext'] == 'json3':
            response = requests.get(s_url['url'])
            json_data = response.json()
            for i in json_data['events']:
                for j in i:
                    if j == 'segs':
                        for k in i[j]:
                            for l in k:
                                if l == 'utf8':
                                    answer = answer + k['utf8']
            answer = answer.replace("\n", " ")
            await get_answer(update, answer)
    else:
        # await event.respond('Эх, не повезло, субтитры отсутствуют!')
        await update.message.reply_text('Эх, не повезло, субтитры отсутствуют!')
        await asyncio.sleep(2)
        
        update.message.reply_text(f"Загружаю файл {video_title}")

        ydl_opts = {
            'format': 'worstaudio',
            'outtmpl': filename
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        await update.message.reply_text(f"Файл {filename} сохранен")

        result = await trnscrb(update, filename)
        print(result)



async def get_answer(update, answer):
    if len(answer) > 4096:
        n = int(len(answer) / 4096)
        k = 0
        i = 0
        for x in range(0, n):
            i = i + k
            j = i + 4096
            k = 4096
            while j > i:
                if answer[j] == ' ':
                    break
                j -= 1
                k -= 1

            await update.message.reply_text(answer[i:i + k])

        await update.message.reply_text(answer[i + k:len(answer)])

    else:
        await update.message.reply_text(answer)

#Транскрипция
async def trnscrb(update, f_name, audio_file=None):

    if audio_file is None:
        audio_file = f_name
            
    t = 10 * 60000
    audio = AudioSegment.from_file(audio_file).set_frame_rate(22050)
    # print("Transcribe without splitting")
    # audio.export(f_name+'_tmp.mp3', format="mp3", bitrate="64k")
    # result = model.transcribe(f_name+'_tmp.mp3', fp16=False)
    # print('result: ',result['text'])
    # await get_answer(update, result['text'])
    # return result['text']
    
    # Проверяем длину аудиофайла
    if len(audio) <= t:
        print("Less than 10 minutes, transcribe without splitting")
        audio.export(f_name+'_tmp.mp3', format="mp3", bitrate="64k")
        result = model.transcribe(f_name+'_tmp.mp3', fp16=False)
        print('result: ',result['text'])
        await get_answer(update, result['text'])
        # os.remove(f_name+'_tmp.mp3')
    else:
        print("More than 10 minutes, split and transcribe")
        parts = int(len(audio) / t)
        print('len(audio) =', len(audio), 'parts =', parts)
        # Разбиваем на части
        start = 0
        print('Detecting silence...')
        chunks = detect_silence(audio, min_silence_len=600, silence_thresh=-25)
        print('Got chunks:', chunks, '\n')
        prmp = ''
        try:
            for i in range(0, parts):
                print('i =', i)
                target_chunk = get_closest_chunk((i + 1) * t, chunks)
                print(target_chunk, '\n')
                end = target_chunk[1]
                segment = audio[start:end]
                segment.export(f_name+'_part{}.mp3'.format(i), format="mp3", bitrate="64k")
                result = model.transcribe(f_name+'_part{}.mp3'.format(i), fp16=False)
                
                prmp = f'{prmp} {result["text"]}' if prmp else result['text']
                
                await get_answer(update, result['text'])
                start = target_chunk[1] - 300 # начало 2й части
                # os.remove(f_name+'_part{}.mp3'.format(i))

            segment = audio[start:]
            segment.export(f_name+'_part{}.mp3'.format(parts), format="mp3", bitrate="64k")
            result = model.transcribe(f_name + '_part{}.mp3'.format(parts), fp16=False)

            await get_answer(update, result['text'])
            # os.remove(f_name + '_part{}.mp3'.format(part))
        except Exception as e:
            print(e, traceback.format_exc())
            # await event.respond("Что-то пошло не так")
            await update.message.reply_text("Что-то пошло не так")
    os.remove(audio_file)

# Находим чанк максимально близкий к 10 минутам
def get_closest_chunk(time, chunks):
    closest = []
    min_diff = float("inf")

    for start, end in chunks:

        diff = abs(end - time)
        if diff < min_diff:
            min_diff = diff
            closest = [start, end]

    return closest


async def message_handler(update, context):
    message = update.message
    user = update.message.from_user
    url = message.text
    filename = os.path.join('voices', f"{user.id}-{message.id}.mp3")
    # user = update.message.from_user.username or update.message.from_user.first_name

    if any(domain in message.text for domain in ['youtube.com', 'youtu.be', 'youtube.com/shorts']):
        await download_link(url, filename, update)

    # elif message.media:
    #     await download_audio(update, context)

    else:
        await update.respond("Я понимаю только ссылки на YouTube видео или аудиосообщения")


async def save_voice(update, context, filename):
    file_id = update.message.voice.file_id
    # Download voice message from Telegram servers:
    file = await context.bot.get_file(file_id)
    os.makedirs('voices', exist_ok=True)
    voice_path = os.path.join(
        'voices',
        filename
    )
    audio_file = await file.download_to_drive(voice_path)
    return audio_file


async def voice_handler(update, context):
    message = update.message
    user = update.message.from_user
    f_name = f"{user.id}-{message.id}.ogg"

    audio_file = await save_voice(update, context, f_name)

    await update.message.reply_text((
        f"Аудиофайл {f_name} успешно сохранен.\n"
        "Начинаю транскрипцию. \n"
        "Ожидайте ответа"
    ))

    result = await trnscrb(update, f_name, audio_file=audio_file)
    print(result)

if __name__ == '__main__':
    application = Application.builder().token(bot_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.run_polling()