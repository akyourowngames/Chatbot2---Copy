from dotenv import dotenv_values
import os

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
Username = env_vars.get("Username")

def SetAssistantStatus(Status):
    with open(TempDirectoryPath("Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

def ShowTextToScreen(Text):
    with open(TempDirectoryPath("Responses.data"), 'w', encoding='utf-8') as file:
        file.write(Text)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "when", "where", "why", "who", "which", "whom", "whose", "can you", "what's", "where's", "how's"]
    
    if query_words:
        if any(word + "" in new_query for word in question_words):
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + "?"
            else:
                new_query = new_query + "?"
        else:
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + "."
            else:
                new_query = new_query + "."
    
    return new_query.capitalize()

def TempDirectoryPath(Filename):
    current_dir = os.getcwd()
    TempDirPath = rf"{current_dir}\Frontend\Files"
    Path = rf'{TempDirPath}\{Filename}'
    return Path

def SetMicrophoneStatus(Command):
    TempDirPath = os.path.join(os.getcwd(), 'Frontend', 'Files')
    with open(os.path.join(TempDirPath, 'Mic.data'), "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    TempDirPath = os.path.join(os.getcwd(), 'Frontend', 'Files')
    with open(os.path.join(TempDirPath, 'Mic.data'), "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def GetAssistantStatus():
    TempDirPath = os.path.join(os.getcwd(), 'Frontend', 'Files')
    with open(os.path.join(TempDirPath, 'Status.data'), "r", encoding='utf-8') as file:
        Status = file.read()
    return Status
