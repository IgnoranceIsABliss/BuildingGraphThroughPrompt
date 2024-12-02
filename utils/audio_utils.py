import whisper
import pyaudio
import wave

# Функция для записи аудио
def record_audio(file_name="input_audio.wav", record_seconds=5, sample_rate=16000, channels=1):
    """Запись аудио с микрофона в файл .wav"""
    audio = pyaudio.PyAudio()

    # Настройка записи
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=1024)

    print("Начинаю запись...")
    frames = []

    # Запись звука
    for i in range(0, int(sample_rate / 1024 * record_seconds)):
        data = stream.read(1024)
        frames.append(data)

    print("Запись завершена.")

    # Остановка и закрытие потока
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Сохранение аудиофайла
    wave_file = wave.open(file_name, 'wb')
    wave_file.setnchannels(channels)
    wave_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(sample_rate)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()

# Функция для преобразования аудиофайла в текст
def transcribe_audio(audio_file, model_size="base"):
    """Транскрибирует аудиофайл в текст с помощью модели Whisper"""
    # Загрузка модели Whisper
    model = whisper.load_model(model_size)
    
    # Преобразование аудиофайла в текст
    result = model.transcribe(audio_file)
    
    return result["text"]

# Основная функция для записи голоса и его преобразования в текст
def voice_to_text(record_seconds=5, model_size="base"):
    """Записывает голос и транскрибирует его в текст"""
    audio_file = "input_audio.wav"
    
    # Запись аудио с микрофона
    record_audio(file_name=audio_file, record_seconds=record_seconds)
    
    # Преобразование аудио в текст
    text = transcribe_audio(audio_file, model_size=model_size)
    
    return text
