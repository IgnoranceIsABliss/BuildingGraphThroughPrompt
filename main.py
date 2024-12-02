import utils.audio_utils
# Время записи (в секундах)
record_seconds = 5
# Размер модели Whisper (tiny, base, small, medium, large)
model_size = "base"
  
# Транскрипция текста с голосового ввода
transcribed_text = utils.audio_utils.voice_to_text(record_seconds=record_seconds, model_size=model_size)
print("Распознанный текст:", transcribed_text)