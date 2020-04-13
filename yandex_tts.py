import json
import requests
from flask import abort
import os
import wave
import base64
from app.config import Config
config = Config()

def yandex_tts(text, filename, lang='ru-RU', voice='oksana', emotion='neutral', speed=1.0,sample_rate=8000):
    iam_token = get_token()

    if YandexTTSValidator.validate_iam_token(iam_token) is not True:
        abort(409, "Error yandex connection")

    if YandexTTSValidator.validate_lang(lang) is not True:
        abort(409, "Unsupported language for Yandex TTS")

    if YandexTTSValidator.validate_text(text) is not True:
        abort(409, "Yandex TTS: incorrect text length")


    wav_file =  generateWAV(text, filename, iam_token, lang, voice, emotion, speed, sample_rate)

    return make_base_64(wav_file)

def synthesize(text, iam_token, lang, voice, emotion, speed, sample_rate):
    id_folder = config['yandex_synth']['FOLDER_ID']
    headers={
        'Authorization': 'Bearer ' + iam_token,
    }
    data={
        'text': text,
        'lang': lang,
        'voice': voice,
        'emotion': emotion,
        'folderId': id_folder,
        'speed': speed,
        'format': 'lpcm',
        'sampleRateHertz': sample_rate,

    }
    with requests.post(url=config['yandex_synth']['URL_SYN'], headers=headers, data=data) as resp:
        if resp.status_code != 200:
            message = ("Request to Yandex TTS failed: code: {}, body: {}".format(resp.status_code, resp.text))
            abort(409, message)

    # return resp
    for chunk in resp.iter_content(chunk_size=None):
        yield chunk

def generateWAV(text, filename, iam_token, lang, voice, emotion, speed, sample_rate):
    basedir = os.path.abspath(os.path.dirname(__file__))

    file_path = (basedir + config['yandex_synth']['UPLOAD_FOLDER_ENTITY'] + filename)
    try:
        with wave.open(file_path + '.wav', "wb") as f:
            f.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
            for audio_content in synthesize(text, iam_token, lang, voice, emotion, speed, sample_rate):
                f.writeframes(audio_content)
        return (file_path + '.wav')
    except Exception as e:
        abort(409, "Wave file does not exist")

def get_token():
    url = config['yandex_synth']['URL_OAUTH']
    oauth_token = config['yandex_synth']['yandexPassportOauthToken']
    params = {'yandexPassportOauthToken': oauth_token}
    response = requests.post(url, params=params)
    decode_response = response.content.decode('UTF-8')
    text = json.loads(decode_response)
    iam_token = text.get('iamToken')
    expires_iam_token = text.get('expiresAt')
    return iam_token

def make_base_64(wav_file):
    try:
        with open(wav_file, 'rb') as record:
            data_base64 = base64.b64encode(record.read())
            response_code = 201
            return data_base64, response_code
    except FileNotFoundError:
        return abort(409, 'Error: file does not exist')

class YandexTTSValidator:

    @staticmethod
    def validate_lang(lang):
        if lang in ["en-US", "ru-RU", "tr-TR"]:
            return True
        else:
            return False

    @staticmethod
    def validate_iam_token(iam_token):
        id_folder = config['yandex_synth']['FOLDER_ID']
        headers = {
            'Authorization': 'Bearer ' + iam_token,
        }
        data = {
            'text': "тест",
            'lang': 'ru-RU',
            'folderId': id_folder,
            'speed': 1.0,
            'emotion': 'neutral'
        }
        resp = requests.post(config['yandex_synth']['URL_SYN'], headers=headers, data=data, stream=True)
        if resp.status_code == 200:
            return True
        else:
            return False

    @staticmethod
    def validate_text(text):
        if len(text) < 5000:
            return True
        else:
            return False


if __name__== '__main__':
    z = yandex_tts(text = 'внимание проверка', filename= 'test', lang='ru-RU', voice='oksana', emotion='neutral', speed=1.0, sample_rate=8000)
