number_emotes = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

def emote_from_index(index : int):
    return number_emotes[index]

def emote_to_index(emote: str):
    return number_emotes.index(emote)

def format_input(string : str):
    import re
    string = string.lower()  # -- Lower case
    string = string.replace("\'", "\'\'")  # -- Treat '

    # Remove ()
    string = re.sub(r'\(.*\)', '', string)
    # Remove []
    string = re.sub(r'\[.*\]', '', string)

    # Remove typical words
    typical_words = [',', '\"', '.avi', '.mp3', '.mp4', '.wmv', 'music video', 'lyrics', 'official', 'video']
    for typical_word in typical_words:
        string = string.replace(typical_word, "")

    # Remove blank spaces
    params = string.split(" ")
    while "" in params:
        params.remove("")
    string = ' '.join(params)
    return string.title()
