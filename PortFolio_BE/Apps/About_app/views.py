import concurrent.futures
import logging

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from Apps.Authentication_App.permissions import IsAdminOrReadOnly
from .models import AboutMe, Language, Experience, Education
from .serializers import AboutMeSerializer, LanguageSerializer, ExperienceSerializer, EducationSerializer

logger = logging.getLogger(__name__)

GITHUB_TIMEOUT = 10  # seconds per request
COMMITS_CACHE_KEY = "github_total_commits"
COMMITS_CACHE_SECONDS = 60 * 60  # GitHub is slow and rate limited; refresh hourly


class AboutMeViewSet(viewsets.ModelViewSet):
    queryset = AboutMe.objects.prefetch_related("languages").order_by("id")
    serializer_class = AboutMeSerializer
    permission_classes = [IsAdminOrReadOnly]


class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.order_by("id")
    serializer_class = LanguageSerializer
    permission_classes = [IsAdminOrReadOnly]


class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.order_by("-start_date")
    serializer_class = ExperienceSerializer
    permission_classes = [IsAdminOrReadOnly]


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.order_by("-end_year")
    serializer_class = EducationSerializer
    permission_classes = [IsAdminOrReadOnly]


def _last_page_from_link_header(link_header):
    """Parse GitHub's Link header and return the page number of rel="last" (or None)."""
    for link in link_header.split(","):
        if 'rel="last"' in link:
            url = link[link.find("<") + 1:link.find(">")]
            for part in url.split("?", 1)[-1].split("&"):
                if part.startswith("page="):
                    try:
                        return int(part[len("page="):])
                    except ValueError:
                        return None
    return None


def get_commit_count(repo, headers, github_username):
    repo_name = repo.get('name')
    if not repo_name:
        return None

    repo_full_name = repo.get('full_name', f"{github_username}/{repo_name}")
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
    repo_commits = 0
    error = None

    try:
        # With per_page=1 the number of the last page equals the number of commits.
        resp = requests.get(commits_url, headers=headers, params={"per_page": 1}, timeout=GITHUB_TIMEOUT)

        if resp.status_code == 403:
            error = "API rate limit exceeded" if "rate limit" in resp.text else "Access forbidden"
        elif resp.status_code == 409:
            error = "Empty repository"
        elif resp.status_code != 200:
            error = f"HTTP {resp.status_code}"
        else:
            last_page = _last_page_from_link_header(resp.headers.get('Link', ''))
            if last_page is not None:
                repo_commits = last_page
            else:
                data = resp.json()
                repo_commits = len(data) if isinstance(data, list) else 0
    except Exception as e:  # network errors must not break the whole endpoint
        error = str(e)

    return {
        "name": repo_name,
        "full_name": repo_full_name,
        "commits": repo_commits,
        "private": repo.get('private', False),
        "error": error,
        "url": repo.get('html_url', ''),
    }


def _fetch_all_repos(headers):
    repos, page = [], 1
    while True:
        resp = requests.get(
            "https://api.github.com/user/repos",
            headers=headers,
            params={"affiliation": "owner", "visibility": "all", "per_page": 100, "page": page},
            timeout=GITHUB_TIMEOUT,
        )
        if resp.status_code != 200:
            return None, resp
        batch = resp.json()
        repos.extend(batch)
        if len(batch) < 100:
            return repos, resp
        page += 1


@api_view(['GET'])
@permission_classes([AllowAny])
def total_commits(request):
    cached = cache.get(COMMITS_CACHE_KEY)
    if cached is not None:
        return Response(cached)

    github_username = settings.GITHUB_USERNAME
    if not settings.GITHUB_TOKEN:
        return Response({
            "error": "GitHub token is not configured",
            "solution": "Set the GITHUB_TOKEN environment variable",
        }, status=503)

    headers = {
        'Authorization': f'token {settings.GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
    }

    try:
        repos, resp = _fetch_all_repos(headers)
        if repos is None:
            try:
                error_msg = resp.json().get('message', 'Unknown error')
            except ValueError:
                error_msg = 'Unknown error'
            return Response({
                "error": "Failed to fetch repositories",
                "github_error": error_msg,
                "status_code": resp.status_code,
            }, status=502)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda repo: get_commit_count(repo, headers, github_username), repos))

        repo_details = [r for r in results if r]
        data = {
            "username": github_username,
            "total_commits": sum(r['commits'] for r in repo_details),
            "repositories": repo_details,
            "repository_count": len(repo_details),
            "private_repos_count": sum(1 for r in repo_details if r['private']),
            "public_repos_count": sum(1 for r in repo_details if not r['private']),
        }
        cache.set(COMMITS_CACHE_KEY, data, COMMITS_CACHE_SECONDS)
        return Response(data)

    except Exception:
        logger.exception("Failed to compute total GitHub commits")
        return Response({"error": "Internal server error"}, status=500)
