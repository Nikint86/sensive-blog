from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class PostQuerySet(models.QuerySet):

    def year(self, year):
        return self.filter(published_at__year=year).order_by('published_at')

    def popular(self):
        return self.annotate(
            likes_count=models.Count('likes')
        ).order_by('-likes_count')[:5]

    def fresh(self):
        return self.order_by('-published_at')[:5]

    def with_author_and_tags(self):
        return self.select_related('author').prefetch_related('tags')

    def fetch_with_comments_count(self):
        post_ids = [post.id for post in self]

        if not post_ids:
            return self

        comments_data = Comment.objects.filter(
            post_id__in=post_ids
        ).values('post_id').annotate(
            count=models.Count('id')
        )

        comments_by_post = {item['post_id']: item['count'] for item in comments_data}

        for post in self:
            post.comments_count = comments_by_post.get(post.id, 0)

        return self

    def popular_with_comments(self):
        return self.popular().with_author_and_tags().fetch_with_comments_count()

    def fresh_with_comments(self):
        return self.fresh().with_author_and_tags().fetch_with_comments_count()


class TagQuerySet(models.QuerySet):

    def popular(self):
        return self.annotate(
            posts_count=models.Count('posts')
        ).order_by('-posts_count')[:5]

    def with_posts_count(self):
        tag_ids = [tag.id for tag in self]

        if not tag_ids:
            return self

        tags_data = self.filter(id__in=tag_ids).annotate(posts_count=models.Count('posts'))
        posts_count_by_tag = {tag.id: tag.posts_count for tag in tags_data}

        for tag in self:
            tag.posts_count = posts_count_by_tag.get(tag.id, 0)

        return self


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
