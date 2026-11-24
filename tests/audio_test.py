import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")
for i, voice in enumerate(speaker.GetVoices()):
    print(f"{i}: {voice.GetDescription()}")