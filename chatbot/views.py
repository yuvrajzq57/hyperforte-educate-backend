import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from profiledetails.models import ProfileDetails
from rest_framework.pagination import PageNumberPagination
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication,SessionAuthentication, TokenAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.test import RequestFactory

load_dotenv()  # Load environment variables from .env

# Configure Groq API - in production, use environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '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')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Mocked database of chat messages and contexts
CHAT_MESSAGES = []
CHAT_CONTEXTS = []


now = datetime.now()


class ChatMessagePagination:
    def __init__(self, page_size=20):
        self.page_size = page_size

    def paginate_queryset(self, queryset, request):
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return queryset[start:end]

    def get_paginated_response(self, data):
        return {
            'results': data,
            'page': int(request.query_params.get('page', 1)),
            'page_size': self.page_size,
            'total_results': len(data)
        }


@method_decorator(csrf_exempt, name='dispatch')
class ChatBotAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get authenticated user details
            user_id = request.user.id
            user_name = request.user.name  # Changed from name to username
            
            message = request.data.get('message')
            module_id = request.data.get('module_id')
            
            # Validate required fields
            if not message or not module_id:
                return Response(
                    {"error": "message and module_id are required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                module_id = int(module_id)
            except ValueError:
                return Response(
                    {"error": "module_id must be an integer."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate AI response with user details
            ai_response = self.generate_ai_response(message, module_id, user_id, user_name)
            
            # Create chat message
            chat_message = {
                'id': len(CHAT_MESSAGES) + 1,
                'user_id': user_id,
                'module_id': module_id,
                'message': message,
                'response': ai_response,
                'timestamp': datetime.now().isoformat()
            }
            CHAT_MESSAGES.append(chat_message)
            
            return Response(chat_message, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get_cybersecurity_context(self, module_id):

        """Returns module-specific cybersecurity context based on module_id"""
        module_contexts = {
            1: {
                "name": "Introduction to Cybersecurity",
                "topics": ["security fundamentals", "CIA triad", "threat landscape"]
            },
            2: {
                "name": "Network Security",
                "topics": ["firewalls", "IDS/IPS", "VPNs", "network protocols"]
            },
            3: {
                "name": "Web Application Security",
                "topics": ["OWASP Top 10", "XSS", "CSRF", "SQL injection"]
            },
            4: {
                "name": "Cryptography",
                "topics": ["encryption", "hashing", "digital signatures", "PKI"]
            },
            5: {
                "name": "Security Operations",
                "topics": ["incident response", "SIEM", "threat hunting", "forensics"]
            }
        }
        
        return module_contexts.get(module_id, {"name": f"Module {module_id}", "topics": ["cybersecurity"]})
    
    def generate_ai_response(self, message, module_id, user_id, user_name):
        """Generate response using Groq API with proper context"""
        try:
            # Get module context
            module_context = self.get_cybersecurity_context(module_id)
            
            # Get user's profile details
            try:
                profile = ProfileDetails.objects.get(user_id=user_id)
                profile_data = {
                    'about': profile.about,
                    'background': profile.background,
                    'student_type': profile.student_type,
                    'learning_style': profile.preferred_learning_style,
                    'learning_preference': profile.learning_preference,
                    'strengths': profile.strengths,
                    'weaknesses': profile.weaknesses,
                    'skill_levels': profile.skill_levels,
                    'learning_goals': profile.learning_goals
                }
            except ProfileDetails.DoesNotExist:
                profile_data = {}
            
            # Get recent messages for context
            recent_messages = [
                msg for msg in CHAT_MESSAGES 
                if msg['user_id'] == user_id and msg['module_id'] == module_id
            ][-5:]
            
            conversation_history = []
            for msg in recent_messages:
                conversation_history.append({"role": "user", "content": msg['message']})
                conversation_history.append({"role": "assistant", "content": msg['response']})
            
            # Format profile data for the prompt
            profile_info = ""
            if profile_data:
                profile_info = "\nStudent Profile Details:"
                if profile_data.get('about'):
                    profile_info += f"\n- About: {profile_data['about']}"
                if profile_data.get('background'):
                    profile_info += f"\n- Background: {profile_data['background']}"
                if profile_data.get('student_type'):
                    profile_info += f"\n- Student Type: {profile_data['student_type'].title()}"
                if profile_data.get('learning_style'):
                    profile_info += f"\n- Preferred Learning Style: {profile_data['learning_style'].title().replace('_', ' ')}"
                if profile_data.get('learning_preference'):
                    profile_info += f"\n- Learning Preferences: {profile_data['learning_preference']}"
                if profile_data.get('strengths'):
                    profile_info += f"\n- Strengths: {', '.join(profile_data['strengths'])}"
                if profile_data.get('weaknesses'):
                    profile_info += f"\n- Areas for Improvement: {', '.join(profile_data['weaknesses'])}"
                if profile_data.get('learning_goals'):
                    goals = ", ".join([goal.get('goal', '') for goal in profile_data['learning_goals'] if goal.get('goal')])
                    if goals:
                        profile_info += f"\n- Learning Goals: {goals}"
            
            # Current time in Indian Standard Time (IST)
            now = timezone.now().astimezone(timezone.get_fixed_timezone(330))  # +5:30 hours
            
            # Create the prompt
            system_prompt = f"""
            You are an expert cybersecurity educator and mentor specializing in {module_context['name']}.
            Focus on topics like {', '.join(module_context['topics'])}.
            
            Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}
            
            Student Information:
            - Name: {user_name}
            {profile_info}
            
            Your responses should be:
            1. Educational and accurate to cybersecurity best practices
            2. Tailored to the student's learning style and preferences
            3. Concise yet comprehensive
            4. Include practical examples when appropriate
            5. Encourage critical thinking about security concepts
            
            For the first interaction, ask about the student's weak points to better tailor your responses.
            Always maintain an encouraging and supportive tone.
            
            Important Guidelines:
            - Avoid giving answers that could enable malicious activities without proper ethical context.
            - If asked about hacking techniques, frame your response in terms of defensive security.
            - Adapt your teaching style based on the student's learning preferences and background.
            - Provide examples and analogies that match the student's experience level.
            - If the student has specific learning goals, help them work towards those goals.
            """
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history for context
            if conversation_history:
                messages.extend(conversation_history)
                
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # FOR TESTING - use direct API call to Groq
            if GROQ_API_KEY != 'your-groq-api-key-here':
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama-3.3-70b-versatile",  # Using Llama 3 70B model - adjust as needed
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 500
                }
                
                response = requests.post(GROQ_API_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    response_data = response.json()
                    return response_data['choices'][0]['message']['content']
                else:
                    print(f"Error from Groq API: {response.status_code} - {response.text}")
                    return "I apologize, but I encountered an error communicating with the AI service. Please try again later."
            
            # Fallback for testing or when API key is not set
            return f"This is a cybersecurity response about {module_context['name']}. Your question was about {message[:30]}..."
            
        except Exception as e:
            # Log the error in a production environment
            print(f"Error generating AI response: {str(e)}")
            return f"I apologize, but I encountered an error processing your request. Please try again later."
    
   

@method_decorator(csrf_exempt, name='dispatch')
class ChatHistoryAPIView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Default user_id for testing
        user_id = 1
        
        module_id = request.query_params.get('module_id')
        
        # Filter messages
        filtered_messages = [
            msg for msg in CHAT_MESSAGES 
            if msg['user_id'] == user_id and 
               (not module_id or msg['module_id'] == int(module_id))
        ]
        
        # Sort messages by timestamp (most recent first)
        filtered_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Paginate results
        paginator = ChatMessagePagination()
        result_page = paginator.paginate_queryset(filtered_messages, request)
        
        return Response(result_page)
