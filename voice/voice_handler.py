import asyncio,openai,sounddevice as sd,numpy as np,logging
from voice.voice_config import config as vcfg

logger=logging.getLogger("VoiceHandler")

class VoiceHandler:
    def __init__(s):
        s.client=openai.AsyncOpenAI(api_key=vcfg.OPENAI_API_KEY)
        s._audio_queue=asyncio.Queue()
        s._stop_recording=asyncio.Event()
        s._stream=None
    
    async def _record_audio(s): #录音协程
        try:
            with sd.InputStream(callback=s._audio_callback,channels=1,samplerate=vcfg.SAMPLE_RATE):
                await s._stop_recording.wait()
        except Exception as e:
            logger.error(f"录音错误: {e}")
            raise
    
    def _audio_callback(s,indata,frames,time,status): #录音回调
        if status:logger.warning(f"录音状态: {status}")
        s._audio_queue.put_nowait(indata.copy())
    
    async def _play_audio(s,chunk): #播放音频
        try:
            audio_data=np.frombuffer(chunk,dtype=np.int16)
            sd.play(audio_data,vcfg.SAMPLE_RATE)
            await asyncio.sleep(len(audio_data)/vcfg.SAMPLE_RATE)
        except Exception as e:
            logger.error(f"播放错误: {e}")
            raise
    
    async def stt_stream(s): #语音转文字流
        try:
            s._stop_recording.clear()
            record_task=asyncio.create_task(s._record_audio())
            
            async with s.client.audio.transcriptions.create_streaming(
                model=vcfg.STT_MODEL,
                response_format="text"
            ) as stream:
                async for text in stream:
                    if text.strip():
                        yield text
                        
        except Exception as e:
            logger.error(f"语音识别错误: {e}")
            raise
        finally:
            s._stop_recording.set()
            if record_task:await record_task
    
    async def tts_stream(s,text): #文字转语音流
        try:
            async with s.client.audio.speech.create_streaming(
                model=vcfg.TTS_MODEL,
                voice=vcfg.TTS_VOICE,
                input=text
            ) as stream:
                async for chunk in stream:
                    await s._play_audio(chunk)
                    yield chunk
        except Exception as e:
            logger.error(f"语音合成错误: {e}")
            raise 