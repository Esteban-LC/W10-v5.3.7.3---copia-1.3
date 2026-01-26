from spellchecker import SpellChecker

try:
    spell = SpellChecker(language='es')
    words = ['pondré', 'estaba', 'siento', 'estoy', 'preguntando', 'preguntaron']
    print(f"Checking words: {words}")
    unknown = spell.unknown(words)
    print(f"Unknown words: {unknown}")
    
    # Check if we can add them
    spell.word_frequency.load_words(['pondré'])
    print(f"After adding 'pondré', unknown: {spell.unknown(['pondré'])}")

except Exception as e:
    print(f"Error: {e}")
