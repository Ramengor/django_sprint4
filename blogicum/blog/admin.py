from django.contrib import admin

from blog.models import Category, Location, Post


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'name',
        'is_published',
        'created_at',
    )
    list_editable = ('is_published',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
        'description',
        'is_published',
        'created_at',
    )
    list_editable = ('is_published',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'author',
        'category',
        'pub_date',
        'location',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'author', 'location',)
    list_filter = ('category', 'location',)
    list_display_links = ('title',)
    list_per_page = 7
    date_hierarchy = 'pub_date'
