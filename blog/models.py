from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.urls import reverse


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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    class PostQuerySet(models.QuerySet):

        def popular(self):
            posts_by_like_count = self.annotate(like_count=Count('likes'))\
                .order_by('-like_count')
            return posts_by_like_count

        # use this instead of annotate(comment_count=Count('comment')) to optimize multiple annotate calls
        # such as when fetching both the like count and the comment count
        def fetch_with_comment_count(self):
            posts = self.all()
            post_ids = [post.id for post in posts]
            posts_with_comments = Post.objects.filter(id__in=post_ids)\
                .annotate(comment_count=Count('comment'))
            ids_and_comments = posts_with_comments.values_list('id', 'comment_count')
            count_for_id = dict(ids_and_comments)
            for post in posts:
                post.comment_count = count_for_id[post.id]
            return posts

    objects = PostQuerySet.as_manager()


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

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

    class TagQuerySet(models.QuerySet):
        def with_post_count(self):
            return self.annotate(post_count=Count('posts'))

        def popular(self):
            tags_by_post_count = self.with_post_count().order_by('-post_count')
            return tags_by_post_count

    objects = TagQuerySet.as_manager()


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
