from django.shortcuts import render, get_object_or_404
from blog.models import Comment, Post, Tag
from django.db.models import Count


def serialize_post(post):
    tags_to_use = getattr(post, 'prefetched_tags', post.tags.all())

    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count if hasattr(post, 'comments_count') else post.comments.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags_to_use],
        'first_tag_title': tags_to_use[0].title if tags_to_use else None,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count if hasattr(tag, 'posts_count') else tag.posts.count(),
    }


def index(request):
    most_popular_posts = list(Post.objects.popular_with_comments())
    most_fresh_posts = list(Post.objects.fresh_with_comments())
    most_popular_tags = list(Tag.objects.popular())

    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related('author'), slug=slug)

    comments = post.comments.select_related('author')
    serialized_comments = [
        {
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        }
        for comment in comments
    ]

    tags_with_count = Tag.objects.annotate(posts_count=Count('posts'))
    related_tags = list(tags_with_count.filter(posts=post))

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = list(Tag.objects.popular())
    most_popular_posts = list(Post.objects.popular_with_comments())

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = get_object_or_404(Tag.objects.annotate(posts_count=Count('posts')), title=tag_title)

    most_popular_tags = list(Tag.objects.popular())
    most_popular_posts = list(Post.objects.popular_with_comments())

    related_posts = list(
        tag.posts.all()[:20]
        .select_related('author')
        .with_tags_and_posts_count()
    )

    if related_posts:
        post_ids = [post.id for post in related_posts]
        comments_data = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_by_post = {item['post_id']: item['count'] for item in comments_data}
        for post in related_posts:
            post.comments_count = comments_by_post.get(post.id, 0)

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})