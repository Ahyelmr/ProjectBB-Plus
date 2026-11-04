import pyttsx3
import time

def test_audio_latency():
    print("Initializing TTS Engine...")
    
    try:
        # Initialize the native Windows SAPI5 voice engine
        engine = pyttsx3.init()
        
        # Configure acoustic tuning (Volume 0.0 to 1.0)
        # Set to 1.0 (Maximum) to cut through ambient diner noise
        engine.setProperty('volume', 1.0) 
        
        # Configure speech rate (Words per minute)
        # Default is usually 200; 150 provides clearer enunciation for paging
        engine.setProperty('rate', 150)
        
        test_phrase = "Order number 1 0 5 is ready for pickup."
        print(f"Testing phrase: '{test_phrase}'")
        
        # Start the high-resolution timer
        start_time = time.perf_counter()
        
        # Direct hardware audio execution
        engine.say(test_phrase)
        engine.runAndWait()
        
        # Stop the timer and calculate milliseconds
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000
        
        print(f"✅ Audio playback successful!")
        print(f"⏱️ Audio Execution Latency: {latency:.2f} ms")
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}\nVerify that your speaker is plugged in and set as the default Windows audio output device.")

if __name__ == "__main__":
    test_audio_latency()