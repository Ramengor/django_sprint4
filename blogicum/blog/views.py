from django.http import Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.models import User
from django.db.models import Count

from blog.models import Post, Category, Comment
from blog.constants import NUMBER_POSTS_PER_PAGE
from blog.forms import CommentForm, PostForm, ProfileForm


def get_filtered_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related('author', 'category')


def get_paginator_posts(queryset, request, post_per_page):
    paginator = Paginator(queryset, post_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def annotate_comment_count(queryset):
    return queryset.annotate(
        comment_count=Count('comments')
    )


def index(request):
    posts = annotate_comment_count(
        get_filtered_posts(

        ).order_by('-pub_date'))
    page_obj = get_paginator_posts(posts, request, NUMBER_POSTS_PER_PAGE)
    return render(request, 'blog/index.html', {
        'page_obj': page_obj
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    filtered_posts = get_filtered_posts()
    if post not in filtered_posts and post.author != request.user:
        raise Http404("Post not found")
    comments = post.comments.all().order_by('created_at')
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = annotate_comment_count(
        get_filtered_posts().filter(category=category)
    ).order_by('-pub_date')
    page_obj = get_paginator_posts(posts, request, NUMBER_POSTS_PER_PAGE)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {
        'form': form,
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {
        'form': form
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {
        'post': post,
        'form': PostForm(instance=post),
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.post = post
        new_comment.author = request.user
        new_comment.save()
        return redirect('blog:post_detail', post_id=post_id)
    comments = post.comments.all()
    return render(request, 'blog/create.html', {
        'form': form,
        'post': post,
        'comments': comments,
    })


@login_required()
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(
        Post,
        id=post_id,
    )
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post=post
    )
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment
    })


@login_required()
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post_id=post_id,
        author=request.user
    )
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'comment': comment,
    })


class UserProfileViews(SingleObjectMixin, ListView):
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_POSTS_PER_PAGE

    def get(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        return context

    def get_queryset(self):
        posts = Post.objects.filter(
            author=self.object,
        ).order_by('-pub_date')
        posts = annotate_comment_count(posts)
        return posts


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username
                    })
