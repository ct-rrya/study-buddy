"""
Giphy Service - Fetch study-related GIFs and memes
"""
import os
import random
import requests

GIPHY_API_KEY = os.environ.get('GIPHY_API_KEY')
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
GIPHY_RANDOM_URL = "https://api.giphy.com/v1/gifs/random"

# Study-related search terms for variety
STUDY_TERMS = [
    "studying hard", "brain power", "you got this", "smart", "learning",
    "focus", "motivation", "success", "thinking", "eureka", "genius",
    "proud", "celebrate", "high five", "good job", "nailed it"
]

CORRECT_ANSWER_TERMS = [
    "celebration", "you got this", "proud", "success", "winner",
    "high five", "good job", "nailed it", "smart", "genius"
]

WRONG_ANSWER_TERMS = [
    "its okay", "try again", "you can do it", "dont give up",
    "keep going", "almost", "next time", "learning"
]

BREAK_TIME_TERMS = [
    "relax", "take a break", "chill", "rest", "coffee break",
    "stretch", "breathe", "calm"
]


def get_gif(search_term=None, rating="pg"):
    """
    Fetch a GIF from Giphy
    
    Args:
        search_term: Optional search term. If None, picks a random study term.
        rating: Content rating (g, pg, pg-13, r)
    
    Returns:
        dict with 'url', 'title', or None if failed
    """
    if not GIPHY_API_KEY:
        return None
    
    try:
        if search_term is None:
            search_term = random.choice(STUDY_TERMS)
        
        params = {
            "api_key": GIPHY_API_KEY,
            "q": search_term,
            "limit": 25,
            "rating": rating,
            "lang": "en"
        }
        
        response = requests.get(GIPHY_SEARCH_URL, params=params, timeout=5)
        data = response.json()
        
        if data.get("data"):
            # Pick a random GIF from results
            gif = random.choice(data["data"])
            return {
                "url": gif["images"]["fixed_height"]["url"],
                "title": gif.get("title", ""),
                "width": gif["images"]["fixed_height"]["width"],
                "height": gif["images"]["fixed_height"]["height"]
            }
    except Exception as e:
        print(f"Giphy error: {e}")
    
    return None


def get_correct_answer_gif():
    """Get a celebratory GIF for correct answers"""
    term = random.choice(CORRECT_ANSWER_TERMS)
    return get_gif(term)


def get_wrong_answer_gif():
    """Get an encouraging GIF for wrong answers"""
    term = random.choice(WRONG_ANSWER_TERMS)
    return get_gif(term)


def get_motivation_gif():
    """Get a motivational GIF"""
    term = random.choice(STUDY_TERMS)
    return get_gif(term)


def get_break_gif():
    """Get a relaxing GIF for break time"""
    term = random.choice(BREAK_TIME_TERMS)
    return get_gif(term)


def get_topic_gif(topic):
    """Get a GIF related to a specific study topic"""
    # Add 'funny' or 'meme' to make it more entertaining
    search_term = f"{topic} funny"
    return get_gif(search_term)
