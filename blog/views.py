from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count if hasattr(post, 'comments_count') else post.comments.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title if post.tags.exists() else None,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count if hasattr(tag, 'posts_count') else tag.posts.count(),
    }


def index(request):
    most_popular_posts = list(Post.objects.annotate(
        likes_count=Count('likes')
    ).select_related('author').prefetch_related('tags').order_by('-likes_count')[:5])

    most_fresh_posts = list(
        Post.objects.select_related('author').prefetch_related('tags').order_by('-published_at')[:5])

    all_posts = most_popular_posts + most_fresh_posts
    post_ids = [post.id for post in all_posts]

    comments_counts = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
        count=Count('id')
    )
    comments_dict = {item['post_id']: item['count'] for item in comments_counts}

    for post in all_posts:
        post.comments_count = comments_dict.get(post.id, 0)

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    all_tags = set()
    for post in all_posts:
        for tag in post.tags.all():
            all_tags.add(tag.id)

    if all_tags:
        tags_with_counts = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
        tags_count_dict = {tag.id: tag.posts_count for tag in tags_with_counts}

        for post in all_posts:
            for tag in post.tags.all():
                if tag.id in tags_count_dict:
                    tag.posts_count = tags_count_dict[tag.id]

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [
            serialize_post(post) for post in most_fresh_posts
        ],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)
    comments = post.comments.all()
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    most_popular_posts = list(Post.objects.annotate(
        likes_count=Count('likes')
    ).select_related('author').prefetch_related('tags').order_by('-likes_count')[:5])

    if most_popular_posts:
        post_ids = [post.id for post in most_popular_posts]
        comments_counts = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_dict = {item['post_id']: item['count'] for item in comments_counts}
        for post in most_popular_posts:
            post.comments_count = comments_dict.get(post.id, 0)

        all_tags = set()
        for post in most_popular_posts:
            for tag in post.tags.all():
                all_tags.add(tag.id)

        if all_tags:
            tags_with_counts = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
            tags_count_dict = {tag.id: tag.posts_count for tag in tags_with_counts}
            for post in most_popular_posts:
                for tag in post.tags.all():
                    if tag.id in tags_count_dict:
                        tag.posts_count = tags_count_dict[tag.id]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    most_popular_posts = list(Post.objects.annotate(
        likes_count=Count('likes')
    ).select_related('author').prefetch_related('tags').order_by('-likes_count')[:5])

    if most_popular_posts:
        post_ids = [post.id for post in most_popular_posts]
        comments_counts = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_dict = {item['post_id']: item['count'] for item in comments_counts}
        for post in most_popular_posts:
            post.comments_count = comments_dict.get(post.id, 0)

        all_tags = set()
        for post in most_popular_posts:
            for tag in post.tags.all():
                all_tags.add(tag.id)

        if all_tags:
            tags_with_counts = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
            tags_count_dict = {tag.id: tag.posts_count for tag in tags_with_counts}
            for post in most_popular_posts:
                for tag in post.tags.all():
                    if tag.id in tags_count_dict:
                        tag.posts_count = tags_count_dict[tag.id]

    related_posts = tag.posts.all()[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})