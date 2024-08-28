from django.http import Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.models import User
from django.db.models import Count

from blog.models import Post, Category, Comment
from blog.constants import MAX_NUMBER_POSTS
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

    page_obj = get_paginator_posts(posts, request, MAX_NUMBER_POSTS)

    return render(request, 'blog/index.html', {
        'page_obj': page_obj
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not ((post.is_published and post.category.is_published
             and post.pub_date <= timezone.now())
            or post.author == request.user):
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

    posts = annotate_comment_count(Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now(),
    ).order_by('-pub_date'))

    page_obj = get_paginator_posts(posts, request, MAX_NUMBER_POSTS)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(
                'blog:profile',
                username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {
        'form': form
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
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
    comments = Comment.objects.filter(post=post).order_by('created_at')
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


class UserProfileViews(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        posts = annotate_comment_count(Post.objects.filter(
            author=user,
        ).order_by('-pub_date'))

        context['page_obj'] = get_paginator_posts(
            posts,
            self.request,
            MAX_NUMBER_POSTS
        )

        return context

    def get_object(self, **kwargs):
        return get_object_or_404(User, username=self.kwargs['username'])


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={
                'username': self.request.user.username
            })
