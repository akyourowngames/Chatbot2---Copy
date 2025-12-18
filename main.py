from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from threading import Thread
from json import load, dump
from dotenv import dotenv_values
from Backend.TypeQuery import TypeQuery
import asyncio
from time import sleep 
import time 
import subprocess
import threading
import json 
import os
import struct
import datetime
from Backend.Basic import ChromeCode

# Env setup
env_vars = dotenv_values(".env") 
Username = env_vars.get("Username")
WakeWordAPIKey = "pKTkEFJzE5noAcbw7gYkMAVszshY/LcZV2jxAKwnBXdChmiouehw4g=="
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may i help you?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# Modules to be lazy loaded
RealtimeSearchEngine = None
Automation = None
FirstLayerDMM = None
SpeechRecognition = None
ChatBot = None
TextToSpeech = None

def load_backend_modules():
    global RealtimeSearchEngine, Automation, FirstLayerDMM, SpeechRecognition, ChatBot, TextToSpeech
    
    print("\nLoading Backend Modules in background...")
    
    # 1. Realtime Search
    try:
        from Backend.RealtimeSearchEngine_Enhanced import RealtimeSearchEngine
        print("✅ Realtime Search Loaded")
    except ImportError:
        from Backend.RealtimeSearchEngine import RealtimeSearchEngine
        
    # 2. Automation
    try:
        from Backend.Automation_Enhanced import Automation
        print("✅ Automation Loaded")
    except ImportError:
        from Backend.Automation import Automation
        
    # 3. Model
    try:
        from Backend.Model_Enhanced import FirstLayerDMM
        print("✅ Decision Model Loaded")
    except ImportError:
        from Backend.Model import FirstLayerDMM
        
    # 4. Speech
    try:
        from Backend.SpeechToText_Enhanced import SpeechRecognition
        print("✅ Enhanced Speech Loaded")
    except ImportError:
        from Backend.SpeechToText import SpeechRecognition
        
    # 5. Chatbot
    try:
        from Backend.Chatbot_Enhanced import ChatBot
        print("✅ Chatbot Loaded")
    except ImportError:
        from Backend.Chatbot import ChatBot
        
    # 6. TTS
    try:
        from Backend.TextToSpeech_Enhanced import TextToSpeech
        print("✅ TTS Loaded")
    except ImportError:
        from Backend.TextToSpeech import TextToSpeech
    
    print("🚀 All Backend Modules Ready!\n")

def ShowDefaultChatIfNoChats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chatlog_path = os.path.join(current_dir, "Data", "ChatLog.json")
    try:
        with open(chatlog_path, "r", encoding='utf-8') as File:
            if len(File.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(DefaultMessage)
    except FileNotFoundError:
        with open(chatlog_path, "w", encoding='utf-8') as f:
            json.dump([], f)
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chatlog_path = os.path.join(current_dir, "Data", "ChatLog.json")
    with open(chatlog_path, 'r', encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
      json_data = ReadChatLogJson()
      formatted_chatlog = ""
      for entry in json_data:
            if entry["role"] == "user":
                  formatted_chatlog += f"user: {entry['content']}\n"
            elif entry["role"] == "assistant":
                  formatted_chatlog += f"Assistant: {entry['content']}\n"
      formatted_chatlog = formatted_chatlog.replace("User",Username + " ")
      formatted_chatlog = formatted_chatlog.replace("Assistant",Assistantname + " ") 
      with open(TempDirectoryPath('Database.data'),'w', encoding='utf-8') as file:
              file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
           File = open(TempDirectoryPath('Database.data'),"r",encoding='utf-8')
           Data = File.read()
           if len(str(Data))>0:
                  lines = Data.split('\n')
                  result = '\n' .join(lines)  
                  File.close()
                  File = open(TempDirectoryPath('Responses.data'),"w", encoding='utf-8')
                  File.write(result)
                  File.close() 

def InitialExecution():
       SetMicrophoneStatus("False")
       ShowTextToScreen("")
       ShowDefaultChatIfNoChats()
       ChatLogIntegration()
       ShowChatsOnGUI()

def MainExecution():
    global SpeechRecognition, FirstLayerDMM, Automation, RealtimeSearchEngine, ChatBot, TextToSpeech
    
    # Wait for modules to load if they haven't yet
    while SpeechRecognition is None:
        time.sleep(0.5)
        
    TaskExecution = False 
    ImageExecution = False
    ImageGenerationQuery = ""
    
    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    
    if Query is None:
        # No speech detected or error
        return
        
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking ...")
    Decision = FirstLayerDMM(Query)
    
    print(f"\nDecision : {Decision}\n")

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])

    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    
    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if TaskExecution == False:
            is_automation = False
            for func in Functions:
                if queries.lower().startswith(func):
                    is_automation = True
                    break
            
            if is_automation:
                run_automation_step(queries)
                TaskExecution = True
            elif "vision" in queries:
                 from Backend.Vision import VisionAnalysis
                 ShowTextToScreen(f"{Assistantname} : Analyzing screen...")
                 SetAssistantStatus("Looking...")
                 vision_response = VisionAnalysis(Query)
            elif "remember" in queries:
                 from Backend.Memory import Remember
                 response = Remember(Query)
                 ShowTextToScreen(f"{Assistantname} : {response}")
                 TextToSpeech(response)
                 TaskExecution = True
            elif "workflow" in queries:
                 from Backend.WorkflowEngine import workflow_engine
                 import asyncio
                 
                 # Extract workflow name
                 workflow_name = queries.replace("workflow ", "").strip()
                 
                 ShowTextToScreen(f"{Assistantname} : Executing workflow: {workflow_name}")
                 TextToSpeech(f"Starting {workflow_name}")
                 
                 # Run workflow
                 asyncio.run(workflow_engine.execute_workflow(workflow_name))
                 
                 ShowTextToScreen(f"{Assistantname} : Workflow complete!")
                 TextToSpeech("Workflow completed successfully")
                 TaskExecution = True

    if ImageExecution == True:
        handle_image_generation(ImageGenerationQuery)

    if G and R or R:
        handle_realtime_search(Mearged_query)
    else:
        handle_general_conversation(Decision)

def run_automation_step(query):
    # Separate function to clean up MainExecution
    response_text = "Executing command"
    q_lower = query.lower()
    if "open " in q_lower and "chrome" not in q_lower: response_text = f"Opening {q_lower.replace('open ', '')}"
    elif "close " in q_lower: response_text = f"Closing {q_lower.replace('close ', '')}"
    elif "play " in q_lower: response_text = f"Playing {q_lower.replace('play ', '')}"
    elif "chrome " in q_lower: response_text = "Running Chrome automation"
    elif "system " in q_lower: response_text = "System control"
    
    ShowTextToScreen(f"{Assistantname} : {response_text}")
    TextToSpeech(response_text)
    asyncio.run(Automation([query]))

def execute_command(msg, cmd):
    ShowTextToScreen(f"{Assistantname} : {msg}")
    TextToSpeech(msg)
    import keyboard
    keyboard.press_and_release(cmd)

def handle_reminder(query):
    from Backend.Reminder import set_reminder
    try:
        parts = query.split(" on ")
        if len(parts) == 1: parts = query.split(" at ")
        reminder_text = parts[0].replace("set reminder ", "").strip()
        reminder_time_str = parts[1].strip()
        reminder_time = datetime.datetime.strptime(reminder_time_str, "%Y-%m-%d at %H:%M")
        if reminder_time > datetime.datetime.now():
            response = set_reminder(reminder_text, reminder_time)
            ShowTextToScreen(f"{Assistantname} : {response}")
            TextToSpeech(response)
        else:
            ShowTextToScreen(f"{Assistantname} : Please provide a future time.")
            TextToSpeech("Please provide a future time.")
    except Exception as e:
        ShowTextToScreen(f"{Assistantname} : Error setting reminder.")
        TextToSpeech("I couldn't set the reminder.")

def handle_image_generation(query):
    with open(r"Frontend/Files/ImageGeneration.data", "w") as file:
        file.write(f"{query}, True")
    try:
        p1 = subprocess.Popen(['python', r'Backend/ImageGeneration.py'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, shell=True)
        subprocesses.append(p1)
    except Exception as e:
        print("Error starting ImageGeneration.py:", e)

def handle_realtime_search(query):
    try:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
    except Exception as e:
        print("Error during real-time search:", e)

def handle_general_conversation(decisions):
    for Queries in decisions:
        if "general" in Queries or "realtime" in Queries:
            try:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general ", "").replace("realtime ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return
            except Exception as e:
                print("Error during general query:", e)
        elif "exit" in Queries:
            QueryFinal = "Okay, Bye!"
            Answer = ChatBot(QueryModifier(QueryFinal))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            TextToSpeech(Answer)
            os._exit(0)

def WakeWordDetection():
    import pvporcupine
    import pyaudio
    try:
        porcupine = pvporcupine.create(access_key=WakeWordAPIKey, keywords=["hey google", "alexa"])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        print("Wake Word System Active: Included 'hey google', 'alexa'")
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                SetMicrophoneStatus("True")
                
    except Exception as e:
        # print(f"Wake word detection error: {e}")
        # Keep thread alive
        while True: time.sleep(10)

def FirstThread():
    # Start Backend Loading in Parallel
    Thread(target=load_backend_modules, daemon=True).start()
    
    # Start Wake Word
    Thread(target=WakeWordDetection, daemon=True).start()
    
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if "Available..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    from Backend.Reminder import start_reminder_checker
    start_reminder_checker()
    
    InitialExecution()
    
    # Start background thread
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    
    # Run GUI on main thread
    SecondThread()
