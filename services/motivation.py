"""
Motivation Service - Daily tips, memes, encouragement
"""
import random
from datetime import datetime

class MotivationEngine:
    TIPS = [
        "Try the Pomodoro Technique: 25 minutes of focus, then a 5-minute break! 🍅",
        "Teaching someone else is the best way to learn. Explain concepts out loud! 🗣️",
        "Stay hydrated! Your brain works better when you drink enough water. 💧",
        "Take short walks between study sessions to boost memory retention. 🚶",
        "Use active recall: close your notes and try to remember what you just read. 🧠",
        "Get enough sleep! Your brain consolidates memories while you rest. 😴",
        "Break big topics into smaller chunks - it's easier to digest! 🍕",
        "Create mind maps to visualize connections between concepts. 🗺️",
        "Study in different locations to improve memory recall. 📍",
        "Reward yourself after completing study goals! 🎁"
    ]
    
    MEMES = [
        {
            'text': "Me: I'll study for 5 minutes.\n*3 hours later*\nStill on the same page 😅",
            'mood': 'relatable'
        },
        {
            'text': "Brain before exam: I know nothing.\nBrain at 3am: Here's a random memory from 2015 🧠",
            'mood': 'funny'
        },
        {
            'text': "Study tip: Crying counts as studying if it's about the material 📖😭",
            'mood': 'dark_humor'
        },
        {
            'text': "Me: Opens textbook.\nTextbook: You dare approach me? 📚⚔️",
            'mood': 'anime'
        },
        {
            'text': "When you finally understand a concept:\n*chef's kiss* 👨‍🍳💋",
            'mood': 'victory'
        },
        {
            'text': "My brain during class: 💤\nMy brain at 2am: What if aliens use Reddit? 👽",
            'mood': 'random'
        }
    ]
    
    ENCOURAGEMENTS = {
        'streak_1': "You started! That's the hardest part. Keep it up! 🌱",
        'streak_3': "3 days strong! You're building momentum! 🚀",
        'streak_7': "A WHOLE WEEK! You're officially a study machine! 🤖",
        'streak_14': "Two weeks of dedication! You're unstoppable! 💪",
        'streak_30': "30 DAYS! You've built an incredible habit! 🏆",
        'first_quiz': "First quiz completed! How did it feel? 📝",
        'perfect_score': "PERFECT SCORE! You absolutely crushed it! 🎯",
        'improvement': "Your scores are improving! Hard work pays off! 📈",
        'comeback': "Welcome back! Ready to pick up where you left off? 🔄"
    }
    
    @classmethod
    def get_daily_motivation(cls, user_stats):
        """Get personalized motivation based on user stats"""
        streak = user_stats.get('streak', 0)
        total_sessions = user_stats.get('total_sessions', 0)
        last_accuracy = user_stats.get('last_accuracy', 0)
        
        # Determine the best encouragement
        if streak >= 30:
            encouragement = cls.ENCOURAGEMENTS['streak_30']
        elif streak >= 14:
            encouragement = cls.ENCOURAGEMENTS['streak_14']
        elif streak >= 7:
            encouragement = cls.ENCOURAGEMENTS['streak_7']
        elif streak >= 3:
            encouragement = cls.ENCOURAGEMENTS['streak_3']
        elif streak >= 1:
            encouragement = cls.ENCOURAGEMENTS['streak_1']
        elif total_sessions > 0:
            encouragement = cls.ENCOURAGEMENTS['comeback']
        else:
            encouragement = "Welcome! Ready to start your learning journey? 🎉"
        
        return {
            'encouragement': encouragement,
            'tip': random.choice(cls.TIPS),
            'meme': random.choice(cls.MEMES)
        }
    
    @classmethod
    def get_session_feedback(cls, questions_answered, correct_answers):
        """Get feedback after a study session"""
        if questions_answered == 0:
            return "Good reading session! Try some quizzes next time to test yourself! 📚"
        
        accuracy = (correct_answers / questions_answered) * 100
        
        if accuracy == 100:
            return cls.ENCOURAGEMENTS['perfect_score']
        elif accuracy >= 80:
            return f"Excellent! {accuracy:.0f}% accuracy! You really know this material! 🌟"
        elif accuracy >= 60:
            return f"Good job! {accuracy:.0f}% accuracy. Keep practicing! 💪"
        else:
            return f"{accuracy:.0f}% - Don't worry! Every mistake is a learning opportunity! 📖"
