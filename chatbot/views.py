import os
import json
import requests
from datetime import datetime ,timedelta
import time
from urllib.parse import urlencode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import (
    BasicAuthentication, 
    SessionAuthentication, 
    TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from dotenv import load_dotenv
from profiledetails.models import ProfileDetails
from .models import GitHubUser
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import asyncio
from mcp_integration.client import mcp_client
from mcp_integration.github_utils import extract_github_intent, format_github_response, get_github_token
import logging

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env

# Configure Groq API
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8000/api/chatbot/github/callback/')
GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_API = 'https://api.github.com/user'

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
            
            # Check if this is a GitHub-related query
            try:
                github_result = extract_github_intent(message.lower())
                if github_result is not None:
                    github_intent, github_params = github_result
                    # Handle GitHub-related query using MCP
                    github_response = self.handle_github_query(request.user, github_intent, github_params)
                    if github_response:
                        chat_message = {
                            'id': len(CHAT_MESSAGES) + 1,
                            'user_id': user_id,
                            'module_id': module_id,
                            'message': message,
                            'response': github_response,
                            'timestamp': datetime.now().isoformat()
                        }
                        CHAT_MESSAGES.append(chat_message)
                        return Response(chat_message, status=status.HTTP_201_CREATED)
            except Exception as github_error:
                logger.error(f"Error in GitHub intent detection: {str(github_error)}")
                # Continue with normal chatbot flow if GitHub detection fails
            
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
            logger.error(f"Unexpected error in chatbot: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred. Please try again later."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_github_query(self, user, intent, params):
        """Handle GitHub-related queries using the MCP server"""
        try:
            # Get GitHub token from the user's GitHubUser model
            token = get_github_token(user)
            if not token:
                return "Please connect your GitHub account first. You can do this by clicking the 'Connect GitHub' button."
            
            # Use asyncio.run to handle the async call properly
            try:
                if intent == 'list_repos':
                    repos = asyncio.run(
                        mcp_client.list_repos(access_token=token, per_page=10)
                    )
                    return format_github_response(intent, repos)
                    
                elif intent == 'list_issues':
                    if 'owner' not in params or 'repo' not in params:
                        return "Please specify both owner and repository, like 'show issues in owner/repo'."
                    
                    issues = asyncio.run(
                        mcp_client.list_issues(
                            access_token=token,
                            owner=params['owner'],
                            repo=params['repo']
                        )
                    )
                    return format_github_response(intent, issues)
                    
                elif intent == 'list_commits':
                    if 'owner' not in params or 'repo' not in params:
                        return "Please specify both owner and repository, like 'show commits in owner/repo'."
                    
                    commits = asyncio.run(
                        mcp_client.list_commits(
                            access_token=token,
                            owner=params['owner'],
                            repo=params['repo']
                        )
                    )
                    return format_github_response(intent, commits)
                    
                else:
                    return "I'm not sure how to handle that GitHub request."
                    
            except Exception as mcp_error:
                logger.error(f"MCP server error: {str(mcp_error)}")
                if "Event loop is closed" in str(mcp_error):
                    # Try once more with a fresh event loop
                    try:
                        if intent == 'list_repos':
                            repos = asyncio.run(
                                mcp_client.list_repos(access_token=token, per_page=10)
                            )
                            return format_github_response(intent, repos)
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {str(retry_error)}")
                        return "Sorry, I encountered an error while processing your GitHub request. Please try again later."
                return "Sorry, I encountered an error while processing your GitHub request. Please try again later."
                
        except Exception as e:
            logger.error(f"Error handling GitHub query: {str(e)}")
            return "Sorry, I encountered an error while processing your GitHub request. Please try again later."
    
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
class GitHubOAuthView(APIView):
    """Initiates the GitHub OAuth flow"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        params = {
            'client_id': GITHUB_CLIENT_ID,
            'redirect_uri': GITHUB_REDIRECT_URI,
            'scope': 'repo,user',  # Requesting repo access for GitHub MCP
            'state': request.user.id,  # Store user ID in state for security
        }
        auth_url = f"{GITHUB_AUTH_URL}?{urlencode(params)}"
        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)


class GitHubOAuthCallbackView(APIView):
    """Handles the GitHub OAuth callback"""
    permission_classes = [AllowAny]  # Must be accessible without auth
    
    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code or not state:
            return Response(
                {'error': 'Missing required parameters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for access token
            token_data = {
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': GITHUB_REDIRECT_URI,
            }
            
            headers = {'Accept': 'application/json'}
            response = requests.post(
                GITHUB_TOKEN_URL, 
                data=token_data, 
                headers=headers
            )
            token_json = response.json()
            
            if 'error' in token_json:
                return Response(
                    {'error': token_json['error_description']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            access_token = token_json.get('access_token')
            
            # Get GitHub user info
            user_response = requests.get(
                GITHUB_USER_API,
                headers={
                    'Authorization': f'token {access_token}',
                    'Accept': 'application/json'
                }
            )
            github_user = user_response.json()
            
            # Store or update GitHub user info
            user = request.user if request.user.is_authenticated else None
            if not user and state.isdigit():
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=int(state))
                except (User.DoesNotExist, ValueError):
                    pass
            
            if not user:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate token expiration (GitHub tokens don't expire by default, but we'll set a default)
            expires_in = token_json.get('expires_in', 60 * 60 * 24 * 30)  # Default 30 days if not provided
            token_expires = timezone.now() + timezone.timedelta(seconds=expires_in)
            
            # Create or update GitHub user record
            github_user_obj, created = GitHubUser.objects.update_or_create(
                user=user,
                defaults={
                    'github_username': github_user.get('login'),
                    'access_token': access_token,
                    'refresh_token': token_json.get('refresh_token'),
                    'token_expires': token_expires,
                }
            )
            
            # Redirect back to the frontend with success status
            frontend_redirect = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/chat?github_connected=true"
            return redirect(frontend_redirect)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GitHubStatusView(APIView):
    """Checks if the current user has connected their GitHub account"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            github_user = GitHubUser.objects.get(user=request.user)
            return Response({
                'connected': True,
                'username': github_user.github_username,
                'expires': github_user.token_expires
            })
        except GitHubUser.DoesNotExist:
            return Response({'connected': False})


class GitHubRepositoriesView(APIView):
    """Lists the authenticated user's GitHub repositories using MCP server"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the GitHub user's access token
            github_user = GitHubUser.objects.get(user=request.user)
            if not github_user.access_token:
                return Response(
                    {"error": "GitHub account not connected"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use asyncio.run to handle the async call properly
            try:
                repos = asyncio.run(
                    mcp_client.list_repos(
                        access_token=github_user.access_token,
                        per_page=100  # Get up to 100 repositories
                    )
                )
                
                # Format the response
                formatted_repos = [{
                    'name': repo.get('name'),
                    'full_name': repo.get('full_name'),
                    'private': repo.get('private', False),
                    'html_url': repo.get('html_url'),
                    'description': repo.get('description'),
                    'language': repo.get('language'),
                    'updated_at': repo.get('updated_at'),
                    'size': repo.get('size', 0)
                } for repo in repos]
                
                return Response({"repositories": formatted_repos}, status=status.HTTP_200_OK)
                
            except Exception as mcp_error:
                logger.error(f"MCP server error: {str(mcp_error)}")
                if "Event loop is closed" in str(mcp_error):
                    # Try once more with a fresh event loop
                    try:
                        repos = asyncio.run(
                            mcp_client.list_repos(
                                access_token=github_user.access_token,
                                per_page=100
                            )
                        )
                        formatted_repos = [{
                            'name': repo.get('name'),
                            'full_name': repo.get('full_name'),
                            'private': repo.get('private', False),
                            'html_url': repo.get('html_url'),
                            'description': repo.get('description'),
                            'language': repo.get('language'),
                            'updated_at': repo.get('updated_at'),
                            'size': repo.get('size', 0)
                        } for repo in repos]
                        return Response({"repositories": formatted_repos}, status=status.HTTP_200_OK)
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {str(retry_error)}")
                        return Response(
                            {"error": "Failed to fetch repositories"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                return Response(
                    {"error": "Failed to fetch repositories"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except GitHubUser.DoesNotExist:
            return Response(
                {"error": "GitHub account not connected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching GitHub repositories: {str(e)}")
            return Response(
                {"error": "Failed to fetch repositories"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GitHubDisconnectView(APIView):
    """Disconnects the user's GitHub account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            github_user = GitHubUser.objects.get(user=request.user)
            github_user.delete()
            return Response({'success': True})
        except GitHubUser.DoesNotExist:
            return Response(
                {'error': 'No GitHub account connected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


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
