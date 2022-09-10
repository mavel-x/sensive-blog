from django.shortcuts import render
from django.db.models import Count, Prefetch
from blog.models import Comment, Post, Tag


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comment_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


# some views don't need full info about a post
def serialize_post_short(post):
    return {
        'title': post.title,
        'author': post.author.username,
        'published_at': post.published_at,
        'slug': post.slug,
    }


# index view needs slightly different fields than serialize_post_short but not full info
def serialize_post_short_index(post):
    return {
        'title': post.title,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'first_tag_title': post.tags.first().title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.post_count,
    }


def index(request):
    most_popular_posts = Post.objects.popular()[:5].prefetch_related('tags')

    most_fresh_posts = Post.objects.order_by('published_at')\
        .prefetch_related('author')[:5]\
        .prefetch_related(Prefetch('tags', queryset=Tag.objects.with_post_count()))\
        .annotate(comment_count=Count('comment'))

    popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post_short_index(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.select_related('author').get(slug=slug)
    comments = Comment.objects.filter(post=post).prefetch_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': post.tags.all(),
    }

    popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = Post.objects.popular().prefetch_related('author')[:5]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in popular_tags],
        'most_popular_posts': [serialize_post_short(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    popular_tags = Tag.objects.popular()[:5].with_post_count()

    most_popular_posts = Post.objects.popular().prefetch_related('author')[:5]

    related_posts = tag.posts.all()[:20]\
        .prefetch_related('author')\
        .prefetch_related(Prefetch('tags', queryset=Tag.objects.with_post_count()))\
        .with_comment_count()

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_short(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
