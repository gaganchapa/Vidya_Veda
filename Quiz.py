import json
import streamlit as st
from typing import Dict
from langchain_core.prompts import PromptTemplate
import os
import random

# Initialize API keys
os.environ["GOOGLE_API_KEY"] = "AIzaSyCLvuJfmS9v01Bvkq-lQ5lZTFWSJ4OMR3I"
from langchain_google_genai import ChatGoogleGenerativeAI

# Set up LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Define the template for generating quiz questions
question_template = """
You are an AI Quiz Master specialized in creating educational content.
Previous conversation:
{chat_history}
New human question: {question}
Response:
"""

question_prompt = PromptTemplate(
    template=question_template,
    input_variables=['question', 'chat_history']
)

question_chain = question_prompt | llm

# Define the template for generating roadmap
roadmap_template = """
You are an AI Learning Path Designer.
Create a personalized learning roadmap for the topic: {topic}
Divide the learning into exactly 3 categories or levels that make sense for this topic.
For each category, provide:
1. A name for the category
2. A brief description (1-2 sentences)
3. Two specific subtopics within this category that would be good for quiz questions

Format your response as a JSON object:
{{
  "categories": [
    {{
      "name": "Category 1 Name",
      "description": "Brief description of category 1",
      "subtopics": ["Subtopic 1", "Subtopic 2"]
    }},
    {{
      "name": "Category 2 Name",
      "description": "Brief description of category 2",
      "subtopics": ["Subtopic 1", "Subtopic 2"]
    }},
    {{
      "name": "Category 3 Name",
      "description": "Brief description of category 3",
      "subtopics": ["Subtopic 1", "Subtopic 2"]
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON without any additional explanation or markdown formatting.
"""

roadmap_prompt = PromptTemplate(
    template=roadmap_template,
    input_variables=['topic']
)

roadmap_chain = roadmap_prompt | llm

# Initialize chat history
chat_history = [
    {
        "role": "system",
        "content": "You are a REST API server with an endpoint /generate-random-question/:topic, which generates unique random quiz question in json data.",
    },
    {"role": "user", "content": "GET /generate-random-question/devops"},
    {
        "role": "assistant",
        "content": '''
        {
            "question": "What is the difference between Docker and Kubernetes?",
            "options": ["Docker is a containerization platform whereas Kubernetes is a container orchestration platform", "Kubernetes is a containerization platform whereas Docker is a container orchestration platform", "Both are containerization platforms", "Neither are containerization platforms"],
            "answer": "Docker is a containerization platform whereas Kubernetes is a container orchestration platform",
            "explanation": "Docker helps you create, deploy, and run applications within containers, while Kubernetes helps you manage collections of containers, automating their deployment, scaling, and more."
        }
        ''',
    }
]

# Function to get a roadmap from a given topic
def get_roadmap_from_topic(topic: str) -> Dict:
    response = roadmap_chain.invoke({'topic': topic})
    
    # Extract the content from the AIMessage object
    roadmap_str = response.content
    
    # Clean up the response
    import re
    roadmap_str = re.sub(r'```json|```', '', roadmap_str).strip()
    
    try:
        roadmap = json.loads(roadmap_str)
        if not 'categories' in roadmap:
            raise ValueError("Missing required keys in the response JSON")
        return roadmap
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error decoding roadmap JSON: {e}")
        # Return a default roadmap structure
        return {
            "categories": [
                {
                    "name": f"Basics of {topic}",
                    "description": f"Foundational concepts of {topic}",
                    "subtopics": ["Introduction", "Key concepts"]
                },
                {
                    "name": f"Intermediate {topic}",
                    "description": f"More advanced concepts in {topic}",
                    "subtopics": ["Common practices", "Tools and techniques"]
                },
                {
                    "name": f"Advanced {topic}",
                    "description": f"Expert-level knowledge of {topic}",
                    "subtopics": ["Best practices", "Cutting-edge developments"]
                }
            ]
        }

# Function to get a quiz question from a given topic
def get_quiz_from_topic(topic: str) -> Dict[str, str]:
    global chat_history
    current_chat = chat_history[:]
    
    current_user_message = {
        "role": "user",
        "content": f"GET /generate-random-question/{topic}",
    }
    current_chat.append(current_user_message)
    
    # Format chat history as a string
    formatted_chat_history = "\n".join([json.dumps(msg) for msg in current_chat])
    
    # Generate the quiz using the LLM chain
    response = question_chain.invoke({
        'question': f"GET /generate-random-question/{topic}",
        'chat_history': formatted_chat_history
    })
    
    # Extract the content from the AIMessage object
    quiz = response.content
    
    # Add the assistant's response to the chat history
    current_assistant_message = {"role": "assistant", "content": quiz}
    chat_history.append(current_user_message)
    chat_history.append(current_assistant_message)
    
    # Clean up the response and return the JSON data
    import re
    quiz = re.sub(r'```json|```', '', quiz).strip()

    try:
        json_string = json.loads(quiz)
        if not all(key in json_string for key in ['question', 'options', 'answer', 'explanation']):
            raise ValueError("Missing required keys in the response JSON")
        return json_string
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error decoding quiz JSON: {e}")
        return {
            "question": f"What is a key concept in {topic}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
            "explanation": f"This is a placeholder explanation about {topic}."
        }

# Custom CSS for improved UI
st.markdown("""
<style>
    .roadmap-category {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #4c78a8;
    }
    .roadmap-title {
        color: #0e1117;
        font-size: 18px;
        font-weight: bold;
    }
    .roadmap-description {
        color: #444444;
        font-style: italic;
        margin-bottom: 10px;
    }
    .subtopic-item {
        background-color: #e6f3ff;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .subtopic-item:hover {
        background-color: #cce5ff;
        transform: scale(1.02);
    }
    .completed {
        border-left: 5px solid #00cc66 !important;
    }
    .current {
        border-left: 5px solid #ffaa00 !important;
    }
    .quiz-container {
        background-color: black;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: black;
    }
    .question-text {
        font-size: 18px;
        font-weight: bold;
        color: white;
        margin-bottom: 15px;
    }
    .results-card {
        background-color: black;
        border-radius: 10px;
        padding: 20px;
        margin-top: 30px;
        text-align: center;
        color: black
    }
    .animate-in {
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .progress-bar {
        height: 10px;
        border-radius: 5px;
        background-color: #e9ecef;
        margin-bottom: 20px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 5px;
        background-color: #4c78a8;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# App title with animation
st.markdown("""
<div style="text-align: center; animation: fadeIn 1.2s ease-in-out;">
    <h1>🧠 Smart Learning Path</h1>
    <p>Personalized quiz experience based on your selected topic</p>
</div>
""", unsafe_allow_html=True)

# Read initial topic from file if available
try:
    with open("user_data.txt", "r") as f:
        main = f.readline().strip()
        sub = f.readline().strip()
        initial_topic = f"{main} {sub}".strip()
except:
    initial_topic = "DevOps"

# Sidebar for topic selection
st.sidebar.markdown("## 🎯 Topic Selection")
topic = st.sidebar.text_input(
    "Enter your learning topic",
    value=initial_topic
)

# Initialize session state
if "roadmap" not in st.session_state:
    st.session_state.roadmap = None
    st.session_state.current_category = 0
    st.session_state.current_subtopic = 0
    st.session_state.questions = {}
    st.session_state.answers = {}
    st.session_state.quiz_active = False
    st.session_state.quiz_complete = False
    st.session_state.correct_count = 0
    st.session_state.total_questions = 0

# Generate roadmap when user clicks the button
if st.sidebar.button("Generate Learning Path"):
    with st.spinner("Creating your personalized learning path..."):
        st.session_state.roadmap = get_roadmap_from_topic(topic)
        st.session_state.questions = {}
        st.session_state.answers = {}
        st.session_state.current_category = 0
        st.session_state.current_subtopic = 0
        st.session_state.quiz_active = False
        st.session_state.quiz_complete = False
        st.session_state.correct_count = 0
        st.session_state.total_questions = 0

# Function to get subtopic key
def get_subtopic_key(cat_idx, sub_idx):
    return f"cat{cat_idx}_sub{sub_idx}"

# Display roadmap if available
if st.session_state.roadmap:
    st.markdown("## 🗺️ Your Learning Roadmap")
    
    # Display progress bar
    total_subtopics = sum(len(cat["subtopics"]) for cat in st.session_state.roadmap["categories"])
    completed_subtopics = len(st.session_state.answers)
    progress_percentage = (completed_subtopics / total_subtopics) * 100 if total_subtopics > 0 else 0
    
    st.markdown(f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress_percentage}%;"></div>
    </div>
    <p style="text-align: center;">{completed_subtopics} of {total_subtopics} subtopics completed ({progress_percentage:.1f}%)</p>
    """, unsafe_allow_html=True)
    
    # Display categories and subtopics
    for cat_idx, category in enumerate(st.session_state.roadmap["categories"]):
        # Determine if this category is completed, current, or upcoming
        category_subtopic_keys = [get_subtopic_key(cat_idx, sub_idx) for sub_idx in range(len(category["subtopics"]))]
        category_completed = all(key in st.session_state.answers for key in category_subtopic_keys)
        category_current = cat_idx == st.session_state.current_category and not category_completed
        
        category_class = "roadmap-category"
        if category_completed:
            category_class += " completed"
        elif category_current:
            category_class += " current"
        
        st.markdown(f"""
        <div class="{category_class}">
            <div class="roadmap-title">{cat_idx + 1}. {category["name"]}</div>
            <div class="roadmap-description">{category["description"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        for sub_idx, subtopic in enumerate(category["subtopics"]):
            subtopic_key = get_subtopic_key(cat_idx, sub_idx)
            completed = subtopic_key in st.session_state.answers
            
            if sub_idx % 2 == 0:
                with col1:
                    if st.button(
                        f"{'✅ ' if completed else ''}Learn: {subtopic}",
                        key=f"btn_{cat_idx}_{sub_idx}",
                        disabled=st.session_state.quiz_active and (st.session_state.current_category != cat_idx or st.session_state.current_subtopic != sub_idx)
                    ):
                        st.session_state.current_category = cat_idx
                        st.session_state.current_subtopic = sub_idx
                        st.session_state.quiz_active = True
                        
                        # Generate questions if not already generated
                        if subtopic_key not in st.session_state.questions:
                            with st.spinner(f"Generating questions about {subtopic}..."):
                                question = get_quiz_from_topic(f"{topic} {subtopic}")
                                st.session_state.questions[subtopic_key] = question
            else:
                with col2:
                    if st.button(
                        f"{'✅ ' if completed else ''}Learn: {subtopic}",
                        key=f"btn_{cat_idx}_{sub_idx}",
                        disabled=st.session_state.quiz_active and (st.session_state.current_category != cat_idx or st.session_state.current_subtopic != sub_idx)
                    ):
                        st.session_state.current_category = cat_idx
                        st.session_state.current_subtopic = sub_idx
                        st.session_state.quiz_active = True
                        
                        # Generate questions if not already generated
                        if subtopic_key not in st.session_state.questions:
                            with st.spinner(f"Generating questions about {subtopic}..."):
                                question = get_quiz_from_topic(f"{topic} {subtopic}")
                                st.session_state.questions[subtopic_key] = question

    # Display quiz if active
    if st.session_state.quiz_active:
        current_cat = st.session_state.roadmap["categories"][st.session_state.current_category]
        current_subtopic = current_cat["subtopics"][st.session_state.current_subtopic]
        subtopic_key = get_subtopic_key(st.session_state.current_category, st.session_state.current_subtopic)
        
        st.markdown("---")
        st.markdown(f"""
        <div class="quiz-container animate-in">
            <h2 style:"color: blue">📝 Quiz: {current_subtopic}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if subtopic_key in st.session_state.questions:
            question = st.session_state.questions[subtopic_key]
            
            # If already answered, just show the results
            if subtopic_key in st.session_state.answers:
                user_answer = st.session_state.answers[subtopic_key]
                correct = user_answer == question["answer"]
                
                st.markdown(f"""
                <div class="question-text">{question["question"]}</div>
                """, unsafe_allow_html=True)
                
                st.radio(
                    "Your answer:",
                    options=question["options"],
                    index=question["options"].index(user_answer),
                    key=f"answered_{subtopic_key}",
                    disabled=True
                )
                
                if correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer is: {question['answer']}")
                
                with st.expander("📚 Explanation", expanded=True):
                    st.markdown(question["explanation"])
                
                if st.button("Continue to Next Topic"):
                    # Find the next subtopic to move to
                    next_found = False
                    for next_cat_idx in range(len(st.session_state.roadmap["categories"])):
                        next_cat = st.session_state.roadmap["categories"][next_cat_idx]
                        for next_sub_idx in range(len(next_cat["subtopics"])):
                            next_key = get_subtopic_key(next_cat_idx, next_sub_idx)
                            
                            # Skip if we're still looking at earlier or current subtopics
                            if next_cat_idx < st.session_state.current_category:
                                continue
                            if next_cat_idx == st.session_state.current_category and next_sub_idx <= st.session_state.current_subtopic:
                                continue
                            
                            # Found the next unanswered subtopic
                            if next_key not in st.session_state.answers:
                                st.session_state.current_category = next_cat_idx
                                st.session_state.current_subtopic = next_sub_idx
                                st.session_state.quiz_active = True
                                next_found = True
                                break
                        if next_found:
                            break
                    
                    # If no next subtopic, mark as complete
                    if not next_found:
                        st.session_state.quiz_active = False
                        st.session_state.quiz_complete = True
                        st.experimental_rerun()
            
            # If not answered yet, show the quiz
            else:
                st.markdown(f"""
                <div class="question-text">{question["question"]}</div>
                """, unsafe_allow_html=True)
                
                user_answer = st.radio(
                    "Select your answer:",
                    options=question["options"],
                    key=f"quiz_{subtopic_key}"
                )
                
                if st.button("Submit Answer"):
                    st.session_state.answers[subtopic_key] = user_answer
                    st.session_state.total_questions += 1
                    
                    if user_answer == question["answer"]:
                        st.session_state.correct_count += 1
                    
                    st.experimental_rerun()
        
        else:
            st.info("Please Select Next Module to take the Quiz")
    
    # Show final results if all quizzes are complete
    if st.session_state.quiz_complete or len(st.session_state.answers) == total_subtopics:
        st.markdown("---")
        
        # Calculate score
        score_percentage = (st.session_state.correct_count / st.session_state.total_questions) * 100 if st.session_state.total_questions > 0 else 0
        
        # Display different messages based on score
        if score_percentage >= 80:
            emoji = "🏆"
            message = "Outstanding! You've mastered this topic!"
        elif score_percentage >= 60:
            emoji = "🌟"
            message = "Great job! You have a solid understanding of the material."
        elif score_percentage >= 40:
            emoji = "📚"
            message = "Good effort! Keep studying to improve your knowledge."
        else:
            emoji = "🔍"
            message = "You're just getting started. More practice will help you improve!"
        
        st.markdown(f"""
        <div class="results-card">
            <h2 style:"color: black">{emoji} Learning Path Complete! {emoji}</h2>
            <h3 style:"color: black">Your Score: {st.session_state.correct_count}/{st.session_state.total_questions} ({score_percentage:.1f}%)</h3>
            <p>{message}</p>
        </div>
        """, unsafe_allow_html=True)
        
    
            
            # Reset for a new learning path
        if st.button("Start a New Learning Path"):
            st.session_state.roadmap = None
            st.session_state.current_category = 0
            st.session_state.current_subtopic = 0
            st.session_state.questions = {}
            st.session_state.answers = {}
            st.session_state.quiz_active = False
            st.session_state.quiz_complete = False
            st.session_state.correct_count = 0
            st.session_state.total_questions = 0
            st.experimental_rerun()
        
        # Download quiz data
        st.sidebar.download_button(
            "📥 Download Quiz Data",
            data=json.dumps({
                "topic": topic,
                "roadmap": st.session_state.roadmap,
                "questions": {k: q for k, q in st.session_state.questions.items()},
                "answers": {k: a for k, a in st.session_state.answers.items()},
                "score": {
                    "correct": st.session_state.correct_count,
                    "total": st.session_state.total_questions,
                    "percentage": score_percentage
                }
            }, indent=4),
            file_name="learning_path_results.json",
            mime="application/json",
        )

else:
    # Welcome message when no roadmap is generated yet
    st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: white ; border-radius: 0px">
        <div style="display: flex; justify-content: center;">
            <img src="https://miro.medium.com/v2/resize:fit:1400/1*PW1IvvLzODIG1TFUhINKbQ.gif" 
                 alt="Learning GIF" style="max-width: 100%; height: auto; border-radius: 8px;">
        </div>
        <h2 style="margin-top: 20px; color: black">Welcome to Your Smart Learning Journey!</h2>
        <p style="color: black">Enter your topic of interest in the sidebar and click "Generate Learning Path" to start.</p>
        <p style="font-style: italic; margin-top: 15px; color: black">The app will create a personalized roadmap with categories and subtopics specifically tailored to your learning needs.</p>
    </div>
    """, unsafe_allow_html=True)

    
    # Show some suggested topics
    st.markdown("### 💡 Suggested Topics")
    topic_cols = st.columns(3)
    
    suggested_topics = [
        "DevOps", "Machine Learning", "JavaScript", 
        "Python", "Data Science", "Web Development",
        "Cloud Computing", "Cybersecurity", "Blockchain"
    ]
    
    for i, suggested_topic in enumerate(suggested_topics):
        with topic_cols[i % 3]:
            if st.button(suggested_topic, key=f"suggest_{i}"):
                topic = suggested_topic
                st.session_state.roadmap = get_roadmap_from_topic(topic)
                st.session_state.questions = {}
                st.session_state.answers = {}
                st.experimental_rerun()