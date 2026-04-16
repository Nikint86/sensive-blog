from django.shortcuts import render, get_object_or_404
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

    related_tags = list(post.tags.all())
    if related_tags:
        tag_ids = [tag.id for tag in related_tags]
        tags_data = Tag.objects.filter(id__in=tag_ids).annotate(posts_count=Count('posts'))
        posts_count_by_tag = {tag.id: tag.posts_count for tag in tags_data}
        for tag in related_tags:
            tag.posts_count = posts_count_by_tag.get(tag.id, 0)

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
    tag = get_object_or_404(Tag, title=tag_title)

    most_popular_tags = list(Tag.objects.popular())
    most_popular_posts = list(Post.objects.popular_with_comments())

    related_posts = list(
        tag.posts.all()[:20]
        .select_related('author')
        .prefetch_related('tags')
    )

    if related_posts:
        post_ids = [post.id for post in related_posts]
        comments_data = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_by_post = {item['post_id']: item['count'] for item in comments_data}
        for post in related_posts:
            post.comments_count = comments_by_post.get(post.id, 0)

        all_tags = set()
        for post in related_posts:
            for tag_obj in post.tags.all():
                all_tags.add(tag_obj.id)

        if all_tags:
            tags_data = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
            posts_count_by_tag = {tag.id: tag.posts_count for tag in tags_data}
            for post in related_posts:
                for tag_obj in post.tags.all():
                    if tag_obj.id in posts_count_by_tag:
                        tag_obj.posts_count = posts_count_by_tag[tag_obj.id]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})