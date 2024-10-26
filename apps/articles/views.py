from django.shortcuts import render
from django.core import serializers
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import F
from apps.articles.models import *
import datetime
import random
import math

# Create your views here.

def main(request):
    return render(request, 'article_main.html')

def dummy_article(request):
    return render(request, 'dummy_article.html')

def dummy_main(request):
    return render(request, 'dummy_main.html')

def json(request):
    data = Article.objects.all()
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def json_by_id(request, id):
    data = Article.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def calculate_article_rank(article):
    # Define weights for each factor
    like_weight = 20
    comment_weight = 15
    date_weight = 10

    # Calculate the score for each factor
    like_score = article.like_count
    comment_score = article.comment_count
    date_score = (datetime.datetime.now(datetime.timezone.utc) - article.created_at).days

    # Normalize the scores
    max_like_score = Article.objects.all().aggregate(max_like=models.Max('like_count'))['max_like']
    max_comment_score = Article.objects.all().aggregate(max_comment=models.Max('comment_count'))['max_comment']

    normalized_like_score = like_score / max_like_score if max_like_score != 0 else 0
    normalized_comment_score = comment_score / max_comment_score if max_comment_score != 0 else 0
    normalized_date_score = math.exp(-1 * date_score) # More recent articles get higher score

    # Calculate the final rank
    rank = (like_weight * normalized_like_score +
            comment_weight * normalized_comment_score +
            date_weight * normalized_date_score +
            random.gauss((max_like_score + max_comment_score), (max_like_score + max_comment_score) / 100 + 1))

    return rank

all_articles = Article.objects.all()
ranked_articles = sorted(all_articles, key=calculate_article_rank, reverse=True)
def show_main(request):
    global all_articles
    articles = all_articles
    if articles.count() == 0:
        return render(request, 'ar_main.html', {'page_obj': None})
    search = request.GET.get("search")
    sort = request.GET.get("sort")
    if search:
        articles = articles.filter(title__icontains=search)
    if sort:
        if sort == "most_like":
            articles = articles.order_by("-like_count")
        elif sort == "oldest":
            articles = articles.order_by("created_at")
        elif sort == "most_recent":
            articles = articles.order_by("-created_at")
        elif not search:
            articles = ranked_articles
    if not search and not sort:
        articles = ranked_articles

    paginator = Paginator(articles, 10)  # Show 10 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ar_main.html', {'page_obj': page_obj})

def show_article(request, id):
    article = Article.objects.get(pk=id)
    return render(request, 'article.html', {'article': article})