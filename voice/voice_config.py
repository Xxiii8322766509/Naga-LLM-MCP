from pydantic import BaseModel

class VoiceConfig(BaseModel): #语音配置
    STT_MODEL:str="whisper-1" #语音识别模型
    TTS_MODEL:str="tts-1" #语音合成模型
    TTS_VOICE:str="alloy" #语音合成声音
    SAMPLE_RATE:int=16000 #采样率
    CHUNK_SIZE:int=4096 #音频块大小
    ENABLED:bool=False #是否启用语音
    
config=VoiceConfig() #全局配置实例 