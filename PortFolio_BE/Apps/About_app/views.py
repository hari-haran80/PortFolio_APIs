from rest_framework import viewsets
from .models import AboutMe, Language, Experience, Education
from .serializers import AboutMeSerializer, LanguageSerializer, ExperienceSerializer, EducationSerializer
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

class AboutMeViewSet(viewsets.ModelViewSet):
    queryset = AboutMe.objects.all()
    serializer_class = AboutMeSerializer

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer


# commits/views.py
GITHUB_USERNAME = "hari-haran80"
GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"

@api_view(['GET'])
def total_commits(request):
    try:
        # Add GitHub token if available (in settings.py)
        headers = {}
        if hasattr(settings, 'GITHUB_TOKEN'):
            headers['Authorization'] = f'token {settings.GITHUB_TOKEN}'

        # Get all repos
        repos_response = requests.get(GITHUB_API_URL, headers=headers)
        
        # Check if request was successful
        if repos_response.status_code != 200:
            return Response({
                "error": f"Failed to fetch repositories: {repos_response.json().get('message', 'Unknown error')}"
            }, status=repos_response.status_code)

        repos = repos_response.json()
        total_commits = 0

        for repo in repos:
            if not isinstance(repo, dict):
                continue  # Skip if not a dictionary
                
            repo_name = repo.get('name')
            if not repo_name:
                continue

            commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits"
            
            try:
                # First request to get pagination info
                commits_response = requests.get(
                    commits_url, 
                    headers=headers,
                    params={"per_page": 1}
                )

                if commits_response.status_code != 200:
                    print(f"Skipping repo {repo_name}, status code: {commits_response.status_code}")
                    continue

                # Handle pagination
                if 'Link' in commits_response.headers:
                    links = commits_response.headers['Link'].split(',')
                    for link in links:
                        if 'rel="last"' in link:
                            last_page_url = link[link.find('<')+1:link.find('>')]
                            try:
                                last_page_number = int(last_page_url.split('page=')[-1])
                                total_commits += last_page_number
                            except (IndexError, ValueError):
                                # Fallback to counting commits if pagination fails
                                total_commits += len(commits_response.json())
                else:
                    total_commits += len(commits_response.json())

            except Exception as repo_error:
                print(f"Error processing repo {repo_name}: {str(repo_error)}")
                continue

        return Response({
            "username": GITHUB_USERNAME,
            "total_commits": total_commits
        })

    except Exception as e:
        return Response({
            "error": "An error occurred while calculating total commits",
            "details": str(e)
        }, status=500)