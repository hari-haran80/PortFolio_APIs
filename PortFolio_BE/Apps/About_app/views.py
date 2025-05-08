from rest_framework import viewsets
from .models import AboutMe, Language, Experience, Education
from .serializers import AboutMeSerializer, LanguageSerializer, ExperienceSerializer, EducationSerializer
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import concurrent.futures


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


def get_commit_count(repo, headers, github_username):
    repo_name = repo.get('name')
    if not repo_name:
        return None

    repo_full_name = repo.get('full_name', f"{github_username}/{repo_name}")
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
    repo_commits = 0
    error = None
    is_private = repo.get('private', False)

    try:
        if not repo.get('permissions', {}).get('push', False):
            error = "No push access - commits may be incomplete"

        commits_response = requests.get(
            commits_url,
            headers=headers,
            params={"per_page": 1, "page": 1}
        )

        if commits_response.status_code == 403:
            error = "API rate limit exceeded" if "rate limit" in commits_response.text else "Access forbidden"
        elif commits_response.status_code != 200:
            error = f"HTTP {commits_response.status_code}"
        else:
            last_page = 1
            if 'Link' in commits_response.headers:
                links = commits_response.headers['Link'].split(',')
                for link in links:
                    if 'rel="last"' in link:
                        last_page_url = link[link.find('<')+1:link.find('>')]
                        try:
                            last_page = int(last_page_url.split('page=')[-1])
                        except (IndexError, ValueError):
                            pass

            if last_page == 1:
                actual_commits = requests.get(
                    commits_url,
                    headers=headers,
                    params={"per_page": 100}
                ).json()
                repo_commits = len(actual_commits) if isinstance(actual_commits, list) else 0
            else:
                repo_commits = last_page

    except Exception as e:
        error = str(e)

    return {
        "name": repo_name,
        "full_name": repo_full_name,
        "commits": repo_commits,
        "private": is_private,
        "error": error,
        "url": repo.get('html_url', '')
    }

@api_view(['GET'])
def total_commits(request):
    try:
        github_username = "hari-haran80"
        headers = {}

        if not hasattr(settings, 'GITHUB_TOKEN'):
            return Response({
                "error": "GitHub token is required in settings to access private repositories",
                "solution": "Add GITHUB_TOKEN to your Django settings"
            }, status=400)

        headers['Authorization'] = f'token {settings.GITHUB_TOKEN}'

        github_api_url = "https://api.github.com/user/repos?affiliation=owner&visibility=all"
        repos_response = requests.get(github_api_url, headers=headers)

        if repos_response.status_code != 200:
            error_msg = repos_response.json().get('message', 'Unknown error')
            return Response({
                "error": "Failed to fetch repositories",
                "github_error": error_msg,
                "docs": "https://docs.github.com/en/rest/repos/repos#list-repositories-for-the-authenticated-user",
                "status_code": repos_response.status_code
            }, status=repos_response.status_code)

        repos = repos_response.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda repo: get_commit_count(repo, headers, github_username), repos))

        repo_details = [r for r in results if r]
        total_commits = sum(r['commits'] for r in repo_details)
        
        return Response({
            "username": github_username,
            "total_commits": total_commits,
            "repositories": repo_details,
            "repository_count": len(repo_details),
            "private_repos_count": sum(1 for r in repo_details if r['private']),
            "public_repos_count": sum(1 for r in repo_details if not r['private'])
        })

    except Exception as e:
        return Response({
            "error": "Internal server error",
            "details": str(e),
            "type": type(e).__name__
        }, status=500)
        