from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot 
from Backend.TextToSpeech import TextToSpeech

# Import web scraping integration
try:
    from Backend.DirectWebScrapingIntegration import integrate_web_scraping
except ImportError:
    from DirectWebScrapingIntegration import integrate_web_scraping
from Backend.helpers import (
    SetAssistantStatus,
    ShowTextToScreen,
    QueryModifier,
    TempDirectoryPath,
    Assistantname,
    Username
)
from asyncio import run
import subprocess
import os

def TypeQuery(query):
    TaskExecution = False 
    ImageExecution = False
    ImageGenerationQuery = ""
    subprocesses = []
    
    SetAssistantStatus("Thinking ...")
    # Fast path: explicit YouTube automation voice triggers
    try:
        ql = str(query).strip().lower()
        if any(p in ql for p in ["start yt automation", "start youtube automation", "yt automate", "youtube automate", "run youtube automation"]):
            niche = "ai"
            try:
                # try to grab words after 'automate'
                parts = ql.split("automate", 1)
                if len(parts) > 1:
                    after = parts[1].strip()
                    if after:
                        niche = after
            except Exception:
                pass
            ShowTextToScreen(f"{Assistantname} : Starting YouTube automation for '{niche}'...")
            run(Automation([f"youtube automate {niche}"]))
            SetAssistantStatus("Automating...")
            return True

        if "youtube upload now" in ql:
            niche = ql.split("youtube upload now", 1)[1].strip() or "ai"
            ShowTextToScreen(f"{Assistantname} : Upload now stub for '{niche}'")
            run(Automation([f"youtube upload now {niche}"]))
            SetAssistantStatus("Uploading...")
            return True

        if "youtube schedule" in ql or "schedule youtube" in ql:
            # Expected pattern: "youtube schedule <niche> | <ISO_TIME>"
            rest = ql.split("youtube schedule", 1)[1].strip() if "youtube schedule" in ql else ql.split("schedule youtube", 1)[1].strip()
            payload = rest if rest else "ai | "
            ShowTextToScreen(f"{Assistantname} : Scheduling '{payload}'")
            run(Automation([f"youtube schedule {payload}"]))
            SetAssistantStatus("Scheduling...")
            return True
    except Exception:
        pass
    Decision = FirstLayerDMM(query)
    
    print("")
    print(f"Decision : {Decision}")
    print("")

    # Normalize decisions so 'general play ...' becomes 'play ...'
    try:
        normalized = []
        for item in Decision:
            if item.startswith("general "):
                rest = item[len("general "):]
                if rest.lower().startswith("play "):
                    normalized.append(f"play {rest[5:]}")
                    continue
            normalized.append(item)
        Decision = normalized
    except Exception:
        pass

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
            if any(queries.startswith(func) for func in ["open", "close", "play", "system", "content", "google search", "youtube search"]):
                run(Automation(list(Decision)))           
                TaskExecution = True
                
    if ImageExecution == True:
        with open(r"Frontend/Files/ImageGeneration.data", "w") as file:
            file.write(f"{ImageGenerationQuery}, True")
        print(f"Written to ImageGeneration.data: {ImageGenerationQuery}, True")
        
        try:
            p1 = subprocess.Popen(['python', r'Backend/ImageGeneration.py'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE, shell=True)
            subprocesses.append(p1)
            print("Started ImageGeneration.py subprocess")
        except FileNotFoundError:
            print("Error starting ImageGeneration.py: FileNotFoundError")      
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")   
            
    if G and R or R:
        try:
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True
        except Exception as e:
            print(f"Error during real-time search: {e}")
            SetAssistantStatus("Error during real-time search")
            return False

    else:
        for Queries in Decision:
            # Check for web scraping queries first - use fast version
            if any(keyword in Queries.lower() for keyword in ['scrape', 'analyze', 'get content', 'read article', 'extract data']):
                try:
                    SetAssistantStatus("Quick scraping...")
                    QueryFinal = Queries.replace("general ", "").replace("realtime ", "")
                    
                    # Try ultra-fast web scraping first
                    try:
                        from Backend.UltraFastWebScrapingIntegration import integrate_web_scraping_ultra_fast
                        scraping_result = integrate_web_scraping_ultra_fast(QueryFinal)
                    except ImportError:
                        try:
                            from Backend.FastWebScrapingIntegration import integrate_web_scraping_fast
                            scraping_result = integrate_web_scraping_fast(QueryFinal)
                        except ImportError:
                            scraping_result = integrate_web_scraping(QueryFinal)
                    
                    if scraping_result:
                        Answer = scraping_result
                    else:
                        # Fallback to regular chatbot
                        Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                except Exception as e:
                    print(f"Error during web scraping: {e}")
                    SetAssistantStatus("Error during web scraping")
                    return False
            
            elif "general" in Queries:
                try:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = Queries.replace("general ", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                except Exception as e:
                    print(f"Error during general query processing: {e}")
                    SetAssistantStatus("Error during general query processing")
                    return False
                
            elif "realtime" in Queries:
                try:
                    SetAssistantStatus("Searching...")
                    QueryFinal = Queries.replace("realtime ", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                except Exception as e:
                    print(f"Error during real-time query processing: {e}")
                    SetAssistantStatus("Error during real-time query processing")
                    return False
                
            elif "exit" in Queries:
                QueryFinal = "Okay , Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering...")
                os._exit(1)
