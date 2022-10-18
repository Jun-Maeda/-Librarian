from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget
from .models import Book, Publisher, Author, Supplier, Stock, BookHistory, Rental, Reserve, Inquiry


# Book の入力欄を設定
class BookInline(admin.TabularInline):
    model = Book
    extra = 0


# Stock の入力欄を設定
class StockInline(admin.TabularInline):
    model = Stock
    extra = 0


# BookHistory の入力欄を設定
class BookHistoryInline(admin.TabularInline):
    model = BookHistory
    extra = 0


# Rental の入力欄を設定
class RentalInline(admin.TabularInline):
    model = Rental
    extra = 0


# Reserve の入力欄を設定
class ReserveInline(admin.TabularInline):
    model = Reserve
    extra = 0


class BookAdmin(admin.ModelAdmin):
    list_display = ['isbn', 'title', 'icon_image']
    inlines = [StockInline, BookHistoryInline, RentalInline, ReserveInline]

    # adminの表示を整える
    fieldsets = (
        ('書籍', {
            'fields': (
                ('isbn',),
                ('title', 'title2'),
                ('book_img',),
                ('save_image',),
                ('publisher_name', 'page'),
                ('detail',)
            )
        }),
        ('出版情報', {
            'fields': (
                ('code', 'time',)
            )
        }),
        ('貸出情報', {
            'fields': (
                ('rent', 'book_q',)
            )
        })
    )

    def icon_image(self, obj):
        if obj.save_image:
            return mark_safe('<img src="{}" style="width:100px;height:auto;">'.format(obj.save_image.url))

    # 編集モードの際のルール
    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.readonly_fields = ('isbn', 'title', 'title2', 'time', 'name', 'page', 'detail', 'code','book_img')
        return self.changeform_view(request, object_id, form_url, extra_context)

    # 新規追加の際のルール
    def add_view(self, request, form_url='', extra_context=None):
        self.readonly_fields = ('title', 'title2', 'time', 'name', 'page', 'detail', 'code')
        return self.changeform_view(request, None, form_url, extra_context)






@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [BookInline]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [BookInline]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['buy_date', 'quantity']


@admin.register(BookHistory)
class BookHistoryAdmin(admin.ModelAdmin):
    list_display = ['date']


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['start_datetime']


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']


admin.site.register(Book, BookAdmin)
# admin.site.register(Publisher, PublisherAdmin)
