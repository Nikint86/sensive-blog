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
    popular_post_ids = list(
        Post.objects.values('id').annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count').values_list('id', flat=True)[:5]
    )

    most_popular_posts = list(
        Post.objects.filter(id__in=popular_post_ids)
        .select_related('author')
        .prefetch_related('tags')
    )
    most_popular_posts.sort(key=lambda p: popular_post_ids.index(p.id))

    most_fresh_posts = list(
        Post.objects.select_related('author')
        .prefetch_related('tags')
        .order_by('-published_at')[:5]
    )

    all_posts = most_popular_posts + most_fresh_posts
    post_ids = [p.id for p in all_posts]

    comments_counts = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
        count=Count('id')
    )
    comments_dict = {item['post_id']: item['count'] for item in comments_counts}
    for p in all_posts:
        p.comments_count = comments_dict.get(p.id, 0)

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    all_tags = set()
    for p in all_posts:
        for tag in p.tags.all():
            all_tags.add(tag.id)

    if all_tags:
        tags_with_counts = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
        tags_count_dict = {tag.id: tag.posts_count for tag in tags_with_counts}
        for p in all_posts:
            for tag in p.tags.all():
                if tag.id in tags_count_dict:
                    tag.posts_count = tags_count_dict[tag.id]

    context = {
        'most_popular_posts': [
            serialize_post(p) for p in most_popular_posts
        ],
        'page_posts': [
            serialize_post(p) for p in most_fresh_posts
        ],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.select_related('author').get(slug=slug)

    comments = Comment.objects.filter(post=post).select_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes_count = post.likes.count()

    related_tags = post.tags.all()

    if related_tags:
        tag_ids = [tag.id for tag in related_tags]
        tags_with_counts = Tag.objects.filter(id__in=tag_ids).annotate(posts_count=Count('posts'))
        tags_count_dict = {tag.id: tag.posts_count for tag in tags_with_counts}
        for tag in related_tags:
            tag.posts_count = tags_count_dict.get(tag.id, 0)

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    popular_post_ids = list(
        Post.objects.values('id').annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count').values_list('id', flat=True)[:5]
    )

    most_popular_posts = list(
        Post.objects.filter(id__in=popular_post_ids)
        .select_related('author')
        .prefetch_related('tags')
    )
    most_popular_posts.sort(key=lambda p: popular_post_ids.index(p.id))

    if most_popular_posts:
        post_ids = [p.id for p in most_popular_posts]
        comments_counts = Comment.objects.filter(post_id__in=post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_dict = {item['post_id']: item['count'] for item in comments_counts}
        for p in most_popular_posts:
            p.comments_count = comments_dict.get(p.id, 0)

        all_tags = set()
        for p in most_popular_posts:
            for tag in p.tags.all():
                all_tags.add(tag.id)

        if all_tags:
            tags_with_counts = Tag.objects.filter(id__in=all_tags).annotate(posts_count=Count('posts'))
            tags_count_dict_full = {tag.id: tag.posts_count for tag in tags_with_counts}
            for p in most_popular_posts:
                for tag in p.tags.all():
                    if tag.id in tags_count_dict_full:
                        tag.posts_count = tags_count_dict_full[tag.id]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(p) for p in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = list(Tag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5])

    popular_post_ids = list(
        Post.objects.values('id').annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count').values_list('id', flat=True)[:5]
    )

    most_popular_posts = list(
        Post.objects.filter(id__in=popular_post_ids)
        .select_related('author')
        .prefetch_related('tags')
    )
    most_popular_posts.sort(key=lambda p: popular_post_ids.index(p.id))

    related_posts = list(
        tag.posts.all()[:20]
        .select_related('author')
        .prefetch_related('tags')
    )

    all_posts = most_popular_posts + related_posts
    all_post_ids = [p.id for p in all_posts]

    if all_post_ids:
        comments_counts = Comment.objects.filter(post_id__in=all_post_ids).values('post_id').annotate(
            count=Count('id')
        )
        comments_dict = {item['post_id']: item['count'] for item in comments_counts}
        for p in all_posts:
            p.comments_count = comments_dict.get(p.id, 0)

        all_tags_ids = set()
        for p in all_posts:
            for t in p.tags.all():
                all_tags_ids.add(t.id)

        if all_tags_ids:
            tags_with_counts = Tag.objects.filter(id__in=all_tags_ids).annotate(posts_count=Count('posts'))
            tags_count_dict = {t.id: t.posts_count for t in tags_with_counts}
            for p in all_posts:
                for t in p.tags.all():
                    if t.id in tags_count_dict:
                        t.posts_count = tags_count_dict[t.id]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(t) for t in most_popular_tags],
        'posts': [serialize_post(p) for p in related_posts],
        'most_popular_posts': [
            serialize_post(p) for p in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})