"""
Study Bot Service - Powered by Groq (Free & Fast!) with Memory!
"""
import os
from groq import Groq

# Initialize Groq client lazily
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        _client = Groq(api_key=api_key)
    return _client

class StudyBot:
    SYSTEM_PROMPT = """You are a friendly, supportive study buddy named Buddy. You help students learn from their study materials.

Your personality:
- Casual and friendly, like a college friend helping out
- Use emojis occasionally but don't overdo it
- Be encouraging and supportive
- Keep responses concise but helpful
- Use phrases like "Ayy", "Let's go!", "You got this!", "Nailed it!"
- When they get something wrong, be supportive not critical

You have access to the student's study notes. Use them to:
- Answer questions about the material
- Generate quiz questions (MCQ, fill-in-blank, short answer)
- Explain concepts in simple terms
- Help them understand difficult topics

IMPORTANT: When you create quizzes or ask questions, remember them! When the student answers, evaluate their response based on the questions you asked."""

    def __init__(self, content, conversation_history=None):
        self.content = content
        self.conversation_history = conversation_history or []
    
    def _chat(self, user_message, task_context=""):
        """Send a message to Groq with conversation history"""
        try:
            # Limit content size for faster responses
            content_preview = self.content[:4000] if len(self.content) > 4000 else self.content
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "system", "content": f"Study notes:\n{content_preview}"},
            ]
            
            if task_context:
                messages.append({"role": "system", "content": task_context})
            
            # Add conversation history for context (last 10 messages to remember quizzes)
            for msg in self.conversation_history[-10:]:
                messages.append({"role": msg['role'], "content": msg['content']})
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            response = get_client().chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
        except Exception as e:
            return f"Oops, something went wrong on my end 😅 Error: {str(e)}"
    
    def get_history(self):
        """Return current conversation history"""
        return self.conversation_history
    
    def generate_quiz(self, num_questions=5):
        """Generate a quiz from the content using AI"""
        import random
        
        focus_hints = [
            "Focus on key concepts and definitions.",
            "Ask about details that are often overlooked.",
            "Test understanding, not just memorization.",
            "Focus on practical applications.",
            "Ask about relationships between concepts.",
            "Cover different sections of the material."
        ]
        random_focus = random.choice(focus_hints)
        random_seed = random.randint(1000, 9999)
        
        prompt = f"""Create exactly {num_questions} NEW and UNIQUE questions based on the study notes. (Seed: {random_seed})

{random_focus}

QUESTION TYPES TO USE:

1. Fill-in-the-blank:
Q1: The _____ is responsible for [function].
A1: [correct word]

2. Short Answer:
Q2: What is [concept]?
A2: [brief 1-3 word answer]

3. True/False:
Q3: True or False: [statement]
A3: True (or False)

4. Identification:
Q4: Identify: [description of a term, person, concept, or thing]
A4: [the term/name being identified]

5. Multiple Choice (format the answer as just the letter):
Q5: What does [concept] do? (A) first option (B) second option (C) third option (D) fourth option
A5: B

REQUIRED FORMAT:
QUIZ_START
Q1: [question]
A1: [short answer - 1-3 words max]
Q2: [question]
A2: [short answer]
(continue for all {num_questions} questions)
QUIZ_END

IMPORTANT: 
- Keep ALL answers SHORT (1-3 words max, or just a letter for MCQ)
- For MCQ, put all options on ONE line with (A) (B) (C) (D) format
- Mix different question types
- Generate DIFFERENT questions than any previous quiz!"""

        response = self._chat(prompt)
        
        # Parse the quiz response
        questions = []
        try:
            lines = response.split('\n')
            current_q = None
            for line in lines:
                line = line.strip()
                if line.startswith('Q') and ':' in line:
                    current_q = line.split(':', 1)[1].strip()
                elif line.startswith('A') and ':' in line and current_q:
                    answer = line.split(':', 1)[1].strip()
                    questions.append({
                        'question': current_q,
                        'answer': answer,
                        'type': 'ai_generated'
                    })
                    current_q = None
        except:
            pass
        
        if not questions:
            # Fallback if parsing failed
            return {
                'type': 'message',
                'response': response
            }
        
        return {
            'type': 'quiz',
            'greeting': "Alright, quiz time! Let's see what you've learned 💪",
            'questions': questions,
            'total': len(questions)
        }
    
    def ask_question(self):
        """Generate a question for the user to answer"""
        prompt = """Ask the student ONE thought-provoking question about their study material. 
Make it conversational, like you're quizzing a friend. 
Remember this question because you'll need to evaluate their answer!
Don't give the answer - just ask the question and wait for their response."""

        response = self._chat(prompt)
        
        return {
            'type': 'open_question',
            'question': response,
            'context': ''
        }
    
    def answer_question(self, user_question):
        """Answer a user's question or evaluate their quiz answer"""
        
        user_lower = user_question.lower().strip()
        
        # Check if user is asking for a quiz/MCQ in chat
        quiz_keywords = ['create quiz', 'make quiz', 'give me quiz', 'mcq', 'multiple choice', 
                        'generate quiz', 'test me', 'quiz me', 'give me questions']
        if any(kw in user_lower for kw in quiz_keywords):
            return {
                'type': 'answer',
                'response': "For quizzes, click the **Generate Quiz** button above! 👆 It'll create a proper quiz with answer checking. In chat, I'm better at explaining concepts and answering your questions about the material! 📚",
                'confidence': 'high'
            }
        
        # Regular Q&A - tell the bot NOT to create quizzes
        task_context = """Answer the student's question based on the study notes. 
DO NOT create quizzes or MCQs in chat - just answer their question directly.
If they ask for a quiz, tell them to use the Generate Quiz button."""
        
        response = self._chat(user_question, task_context)
        
        return {
            'type': 'answer',
            'response': response,
            'confidence': 'high'
        }
    
    def generate_flashcards(self, num_cards=8):
        """Generate flashcards from the content"""
        import random
        random_seed = random.randint(1000, 9999)
        
        prompt = f"""Create exactly {num_cards} flashcards from the study notes. (Seed: {random_seed})

Each flashcard should have:
- FRONT: A term, concept, question, or prompt (keep it short!)
- BACK: The definition, answer, or explanation (concise but complete)

Mix different types:
- Term → Definition
- Question → Answer  
- Concept → Explanation
- "What is..." → Answer

FORMAT (follow exactly):
FLASHCARDS_START
CARD_1_FRONT: [front text]
CARD_1_BACK: [back text]
CARD_2_FRONT: [front text]
CARD_2_BACK: [back text]
(continue for all {num_cards} cards)
FLASHCARDS_END

Keep fronts SHORT (1-10 words). Backs can be longer but still concise."""

        response = self._chat(prompt)
        
        # Parse flashcards
        cards = []
        try:
            lines = response.split('\n')
            current_front = None
            for line in lines:
                line = line.strip()
                if '_FRONT:' in line:
                    current_front = line.split(':', 1)[1].strip()
                elif '_BACK:' in line and current_front:
                    back = line.split(':', 1)[1].strip()
                    cards.append({
                        'front': current_front,
                        'back': back
                    })
                    current_front = None
        except:
            pass
        
        if not cards:
            return {
                'type': 'message',
                'response': "Had trouble creating flashcards. Try again! 😅"
            }
        
        return {
            'type': 'flashcards',
            'cards': cards,
            'total': len(cards)
        }
    
    def check_answer(self, question, user_answer):
        """Check if user's answer is correct - now with context!"""
        prompt = f"""The student's answer: {user_answer}

Based on our conversation and the study notes, evaluate their answer.

IMPORTANT: Start your response with either [CORRECT] or [INCORRECT] or [PARTIAL] on the first line, then give your feedback.

- If fully correct: Start with [CORRECT] then celebrate!
- If partially correct: Start with [PARTIAL] then acknowledge what they got right and what needs work
- If wrong: Start with [INCORRECT] then be supportive and explain the right answer"""

        response = self._chat(prompt)
        
        # Check the tag at the start of response
        response_lower = response.lower()
        if '[correct]' in response_lower and '[incorrect]' not in response_lower:
            is_correct = True
        elif '[partial]' in response_lower:
            is_correct = True  # Give credit for partial
        else:
            is_correct = False
        
        # Clean up the tag from the displayed response
        clean_response = response
        for tag in ['[CORRECT]', '[INCORRECT]', '[PARTIAL]', '[correct]', '[incorrect]', '[partial]']:
            clean_response = clean_response.replace(tag, '').strip()
        
        return {
            'type': 'feedback',
            'correct': is_correct,
            'message': clean_response
        }
