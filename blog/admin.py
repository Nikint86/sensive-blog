from django.contrib import admin
from django.db.models import Count
from blog.models import Post, Tag, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_at', 'likes_count')
    list_filter = ('published_at', 'author', 'tags')
    search_fields = ('title', 'text')
    raw_id_fields = ('author', 'likes')
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'

    def likes_count(self, obj):
        return obj.likes.count()

    likes_count.short_description = 'Количество лайков'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            likes_count=Count('likes')
        ).select_related('author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('title', 'posts_count')
    search_fields = ('title',)

    def posts_count(self, obj):
        return obj.posts.count()

    posts_count.short_description = 'Количество постов'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            posts_count=Count('posts')
        )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'published_at', 'short_text')
    list_filter = ('published_at', 'author')
    search_fields = ('text', 'author__username', 'post__title')
    raw_id_fields = ('post', 'author')
    date_hierarchy = 'published_at'

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Текст комментария'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post', 'author')
