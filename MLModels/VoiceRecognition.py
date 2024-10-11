import whisper

# Загрузка модели (можно использовать разные уровни: tiny, base, small, medium, large)
model = whisper.load_model("base")

# Преобразование аудиофайла в текст
result = model.transcribe("audio_file.mp3")

print(result["text"])