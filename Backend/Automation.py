# from AppOpener import close, open as appopen # Moved to function scope
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq

from Backend.YoutubeAutomation import YoutubeAutomation
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
from Backend.UltimatePCControl import ultimate_pc

env_vars = dotenv_values(".env")
from Backend.LLM import ChatCompletion
# client = Groq(api_key=GroqAPIKey) # Removed

professional_responses = [
    "Your satisfication is my top priority; feel free to reach out if there's anything I can help you with.",
    "I'm at your service for any additional questions or support you may need dont't hesitate to ask."
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ['Username']}, You're content writer. You have to write content like letter"}]

def GoogleSearch(Topic):
    search(Topic)
    return True

def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])
        
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        
        Answer = ChatCompletion(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            text_only=True
        )
        messages.append({"role": "assistant", "content": Answer})
        return Answer  # Added return to make sure the content is returned
        
    Topic = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)
    
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)
        
    OpenNotepad(rf"Data\{Topic.lower().replace(' ','')}.txt")
    return True

def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    """
    Beast Mode App Opening:
    1. Try AppOpener (Smart match)
    2. Try common path mappings
    3. Try shell execution
    4. Fallback: Google Search & Open Link
    """
    app_lower = app.lower().strip()
    from Backend.ExecutionState import set_state
    
    try:
        from AppOpener import open as appopen
        print(f"[Automation] Attempting to open {app} via AppOpener...")
        appopen(app, match_closest=True, output=False, throw_error=True)
        set_state("last_opened_app", app)
        return True
    except Exception as e:
        print(f"[Automation] AppOpener failed for {app}: {e}")
        
    # Manual common paths (Win + R equivalents/Direct EXEs)
    common_aliases = {
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "chrome": "chrome",
        "browser": "chrome",
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "cmd": "cmd",
        "powershell": "powershell"
    }
    
    executable = common_aliases.get(app_lower, app_lower)
    try:
        subprocess.Popen(executable, shell=True)
        set_state("last_opened_app", app)
        return True
    except:
        pass

    # Final Fallback: Web Search
    print(f"[Automation] App not found on system. Searching web for {app}...")
    try:
        def extract_links(html):
            if html is None: return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a')
            valid_links = []
            for link in links:
                href = link.get('href')
                if href and "url?q=" in href and not "google.com" in href:
                    valid_links.append(href.split("url?q=")[1].split("&")[0])
            return valid_links

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            return response.text if response.status_code == 200 else None

        html = search_google(app)
        if html:
            links = extract_links(html)
            if links:
                webopen(links[0])
                return True
    except:
        pass
        
    return False

def CloseApp(app):
    """
    Beast Mode App Closing:
    1. Try AppOpener Close
    2. Try psutil kill
    3. Try taskkill
    """
    app_lower = app.lower().strip()
    
    try:
        from AppOpener import close
        close(app, match_closest=True, output=False, throw_error=True)
        print(f"[Automation] Closed {app} via AppOpener")
        return True
    except:
        pass
        
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if app_lower in proc.info['name'].lower():
                proc.kill()
                print(f"[Automation] Killed process: {proc.info['name']}")
                return True
    except:
        pass

    try:
        subprocess.run(f"taskkill /f /im *{app_lower}*", shell=True, capture_output=True)
        return True
    except:
        return False
        
def System(command):
    def mute():
        keyboard.press_and_release("volume mute")
        
    def unmute():
        keyboard.press_and_release("volume mute")
        
    def volume_up():
        keyboard.press_and_release("volume up")
        
    def volume_down():
        keyboard.press_and_release("volume down")
    
    def brightness_up():
        keyboard.press_and_release("brightness up")
    
    def brightness_down():
        keyboard.press_and_release("brightness down")
    
    def minimize_all():
        keyboard.press_and_release("win+d")
    
    def lock_screen():
        keyboard.press_and_release("win+l")
    
    def task_manager():
        keyboard.press_and_release("ctrl+shift+esc")
        
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    elif command == "brightness up":
        brightness_up()
    elif command == "brightness down":
        brightness_down()
    elif command == "minimize all" or command == "show desktop":
        minimize_all()
    elif command == "lock screen" or command == "lock":
        lock_screen()
    elif command == "task manager":
        task_manager()
    elif command == "shutdown":
        return ultimate_pc.shutdown(60)
    elif command == "restart":
        ultimate_pc.restart(60)
        return "Restarting in 60 seconds"
    elif command == "sleep":
        ultimate_pc.sleep()
        return "System sleeping"
    elif command == "hibernate":
        ultimate_pc.hibernate()
        return "System hibernating"
    elif "battery" in command or "power" in command:
        stats = ultimate_pc.get_beast_stats()
        return f"Battery: {stats.get('battery', {}).get('percent', 'N/A')}% | RAM: {stats['memory']['percent']}%"
    elif "optimize" in command or "clean system" in command:
        return ultimate_pc.optimize_system()
    elif "system health" in command or "pc stats" in command:
        stats = ultimate_pc.get_beast_stats()
        hogs = ", ".join([h['name'] for h in stats['hogs']])
        return f"CPU: {stats['cpu']['total']}% | RAM: {stats['memory']['percent']}% | Uptime: {stats['uptime']}\nHogs: {hogs}"
    elif "grid layout" in command or "arrange all" in command:
        from Backend.WindowManager import grid_layout
        return grid_layout()
    elif command.startswith("focus on "):
        app = command.replace("focus on ", "")
        from Backend.WindowManager import window_manager
        return window_manager.focus_mode(app)
    elif "split screen" in command:
        from Backend.WindowManager import window_manager
        return window_manager.split_screen()
    elif "screenshot" in command:
        import pyautogui
        import datetime
        from Backend.ExecutionState import set_state
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # Take screenshot of primary screen
        pyautogui.screenshot(filename)
        
        # Store state for "open it" command
        set_state("last_screenshot", filename)
        
        print(f"[System] Screenshot saved: {filename}")
        return f"Screenshot saved as {filename}. Do you want me to open it?"
    
    elif command.startswith("create file "):
        # Create a file: "create file test.txt"
        filename = command.replace("create file ", "").strip()
        try:
            with open(filename, "w") as f:
                f.write("")
            
            from Backend.ExecutionState import set_state
            set_state("last_file_created", filename)
            
            print(f"Created file: {filename}")
            return f"Created file {filename}. Do you want to open it?"
        except Exception as e:
            print(f"Failed to create file: {e}")
            return False
    elif command.startswith("delete file "):
        # Delete a file: "delete file test.txt"
        filename = command.replace("delete file ", "").strip()
        try:
            os.remove(filename)
            print(f"Deleted file: {filename}")
        except Exception as e:
            print(f"Failed to delete file: {e}")
    elif command.startswith("copy text "):
        # Copy text to clipboard: "copy text Hello World"
        text = command.replace("copy text ", "").strip()
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"Copied to clipboard: {text}")
        except:
            print("Clipboard operation failed (install pyperclip)")
    elif command == "paste":
        # Paste from clipboard
        keyboard.press_and_release("ctrl+v")
    elif command == "switch app" or command == "next app":
        # Switch to next application
        from Backend.WindowManager import window_manager
        result = window_manager.switch_to_next_app()
        print(result)
    elif command == "previous app" or command == "back app":
        # Switch to previous application
        from Backend.WindowManager import window_manager
        result = window_manager.switch_to_previous_app()
        print(result)
    elif command == "list apps":
        # List open applications
        from Backend.WindowManager import window_manager
        result = window_manager.list_open_apps()
        print(result)
    elif command.startswith("switch to "):
        # Switch to specific app
        app_name = command.replace("switch to ", "")
        from Backend.WindowManager import window_manager
        result = window_manager.switch_to_app(app_name)
        print(result)
    elif command == "tile windows":
        from Backend.WindowManager import window_manager
        result = window_manager.tile_windows()
        print(result)
    elif command == "snap left":
        from Backend.WindowManager import window_manager
        result = window_manager.snap_left()
        print(result)
    elif command == "snap right":
        from Backend.WindowManager import window_manager
        result = window_manager.snap_right()
        print(result)
    elif command == "start gesture control" or command == "gesture mode" or command == "jarvis gesture":
        # Start JARVIS-level hand gesture control
        from Backend.JarvisGesture import jarvis_gesture
        import threading
        thread = threading.Thread(target=jarvis_gesture.run, daemon=True)
        thread.start()
        print("JARVIS Gesture Control started!")
    elif command.lower().startswith("press "):
        # Handle generic keyboard commands e.g., "press win+d"
        keys = command.lower().replace("press ", "").split("+")
        keyboard.press_and_release("+".join(keys))
    else:
        # Try to execute as a general keyboard command if simpler
        try:
            keyboard.press_and_release(command)
        except:
            pass
        
    return True

async def TranslateAndExecute(commands: list[str]):
    funcs = []
    
    for command in commands:
        if command.startswith("open "):
            if "open it" in command:
                # Handle "open it" (smart follow-up)
                from Backend.ExecutionState import get_state
                last_screenshot = get_state("last_screenshot")
                last_file = get_state("last_file_created")
                
                target_file = last_screenshot or last_file
                if target_file:
                    fun = asyncio.to_thread(OpenApp, target_file)
                    funcs.append(fun)
                else:
                    yield "I'm not sure what to open. I haven't created any files recently."
                continue
            
            if "open file" == command:
                pass
            
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)
                
        elif command.startswith("general "):
            pass
        
        elif command.startswith("realtime "):
            pass
        
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)
            
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)
            
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("chrome "):
            # Chrome automation commands
            from Backend.ChromeAutomation import chrome_command, chrome_search, chrome_open
            
            chrome_cmd = command.removeprefix("chrome ").strip()
            
            if chrome_cmd.startswith("search "):
                query = chrome_cmd.replace("search ", "")
                fun = asyncio.to_thread(chrome_search, query, "google")
            elif chrome_cmd.startswith("youtube "):
                query = chrome_cmd.replace("youtube ", "")
                fun = asyncio.to_thread(chrome_search, query, "youtube")
            elif chrome_cmd.startswith("open "):
                url = chrome_cmd.replace("open ", "")
                fun = asyncio.to_thread(chrome_open, url)
            else:
                fun = asyncio.to_thread(chrome_command, chrome_cmd)
            
            funcs.append(fun)

        elif command.startswith("youtube automate "):
            niche = command.removeprefix("youtube automate ").strip()
            def run_yt():
                ya = YoutubeAutomation()
                ya.run_once(niche or "ai")
                return True
            fun = asyncio.to_thread(run_yt)
            funcs.append(fun)

        elif command.startswith("youtube upload now "):
            niche = command.removeprefix("youtube upload now ").strip()
            def up_now():
                ya = YoutubeAutomation()
                return ya.upload_now(niche or "ai")
            funcs.append(asyncio.to_thread(up_now))

        elif command.startswith("youtube schedule "):
            rest = command.removeprefix("youtube schedule ").strip()
            try:
                niche, when_iso = rest.split(" | ", 1)
            except ValueError:
                niche, when_iso = rest, ""
            def sched():
                ya = YoutubeAutomation()
                return ya.schedule(niche or "ai", when_iso or "")
            funcs.append(asyncio.to_thread(sched))
            
        elif command.startswith("search_web "):
            from Backend.JarvisWebScraper import quick_search, scrape_markdown
            query = command.replace("search_web ", "").strip()
            async def run_search():
                results = await quick_search(query)
                if results:
                    return f"Top Result: {results[0]['title']}\n{results[0]['link']}"
                return "No results found."
            funcs.append(run_search())

        elif command.startswith("scrape_site "):
            from Backend.JarvisWebScraper import scrape_markdown
            url = command.replace("scrape_site ", "").strip()
            funcs.append(scrape_markdown(url))

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)
            
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)
            
        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)
            
        else:
            print(f"No Function Found for {command}")
            
    results = await asyncio.gather(*funcs, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Error in automation: {result}")
        elif isinstance(result, str):
            yield result
        else:
            yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    
    return True

if __name__ == "__main__":
    asyncio.run(Automation(["open google", "open instagram", "open notepad", "play husn", "content song for me"]))
    # asyncio.run(Automation(["content a letter to a house from bank to pay the loan", "open Intagram", "open google", "open notepad", "play husn", "content song for me", "close notepad", "close google", "close Intagram"]))
