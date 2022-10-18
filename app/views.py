import json, requests
from django.views import generic
from .models import Book, Stock, Reserve, Rental, Supplier, Inquiry
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import InquiryForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from librarian import local_settings


class BookIndexView(generic.ListView):
    model = Book
    template_name = 'libr/index.html'


def detail(request, pk):
    if not request.user.is_active:
        return redirect('/accounts/login/')


class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'libr/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        shops = Supplier.objects.all()

        # pk値を取得して別モデル情報を取得
        re_book = Book.objects.get(pk=self.kwargs['pk'])

        # 該当の貸し出し情報を取得
        rent_book = Rental.objects.filter(book=re_book)
        # 返却フラグのないものだけを取得
        renting = rent_book.filter(return_flag=False).order_by('start_datetime')

        # 該当の本の予約情報を取得
        reserve = Reserve.objects.filter(book=re_book)
        # 予約中の人のだけ情報を取得
        reserve_list = reserve.filter(reserve_flag=False).order_by('start_datetime')

        context.update({
            'shops': shops,
            'reserve_list': reserve_list,
            'rental_check': re_book.book_q - len(reserve_list),
            'renting': renting,
        })
        return context

    def post(self, request, *args, **kwargs):
        ac_button = request.POST['action']
        # ログインユーザーのPKを取得
        user_name = self.request.user.pk
        book_info = request.POST['book']

        # postされた本のISBNコードをつかってBookインスタンス化
        book_get = Book.objects.get(isbn=book_info)
        if ac_button == "レンタル":
            Rental.objects.create(book=book_get, user=user_name)
            messages.success(self.request, "レンタルしました。")
        if ac_button == "予約":
            Reserve.objects.create(book=book_get, user=user_name)
            messages.success(self.request, "予約しました。")
        if ac_button == "入荷":
            stock_q = int(request.POST['stock'])
            shop = request.POST['shops']
            # 取得したpk値から仕入れ先情報を取得
            shop_info = Supplier.objects.get(pk=shop)
            Stock.objects.create(book=book_get, shop=shop_info, quantity=stock_q, name=user_name)
            messages.success(self.request, f"{stock_q}冊仕入れました。")

        # 仕入れボタン
        # Stock.objects.create()
        # 予約ボタン
        # Reserve.objects.create()
        #

        return redirect('app:detail', pk=book_get.pk)


class MypageView(generic.View):
    def post(self, request, *args, **kwargs):
        # ログインユーザーの情報を取得
        my_pk = self.request.user
        # 返却ボタンが押されていた場合の処理
        if request.POST.get('return'):
            return_book = request.POST['return']
            # 返却モデルから該当するものを取得して返却フラグにチェック
            r_book = Rental.objects.get(pk=return_book)
            r_book.return_flag = True
            r_book.save()
            messages.success(self.request, f"{r_book.book.title}を返却しました。")

        rental_books = Rental.objects.filter(user=my_pk.pk, return_flag=False)
        context = {
            'mypk': my_pk,
            'rentals': rental_books
        }
        return render(request, 'libr/mypage.html', context)


# def stock_create(request):
#     pass
#
#
# def rental_create(request):
#     pass


# ISBNコードで登録できるものかフォームで確認する
class CheckView(generic.View):
    def post(self, request, *args, **kwargs):
        check = request.POST["isbn"]
        url = requests.get(f"https://api.openbd.jp/v1/get?isbn={check}&pretty")
        text = url.text
        data = json.loads(text)

        book = data[0]
        context = {
            'book': book,
        }
        return render(request, 'libr/check.html', context)


# class StockCreateView(generic.CreateView):
#     model = Stock
#
#     def form_valid(self, form):
#         pass
#
#     def form_invalid(self, form):
#         pass


# お問合せフォーム
class InquiryView(LoginRequiredMixin, generic.CreateView):
    model = Inquiry
    form_class = InquiryForm
    template_name = 'libr/form.html'
    success_url = '/Inquiry'

    # 成功した場合
    def form_valid(self, form):
        messages.success(self.request, 'お問合せを送信しました。')
        # フォームの名前の項目にログインユーザー名を指定する
        form.instance.name = self.request.user

        google_chat = local_settings.google_chat_webhook
        body = f"{form.instance.name}さんから問い合わせです。\n{form.instance.matter}"

        requests.post(google_chat, data=json.dumps({
            "text": body
        }))

        # # メール送信
        # subject = " お問合せ "
        # message = self.request.POST['matter']
        # from_email = 'jun126m@prestigein.com'
        # to = ['jun126m@prestigein.com']
        # email = EmailMessage(subject, message, from_email, to)
        # email.send()

        return super().form_valid(form)


    # 失敗した場合
    def form_invalid(self, form):
        messages.error(self.request, '送信失敗しました。')
        return super().form_valid(form)

# array = {
#     'title': ['Slack タイトル', 'PiVToTグループ作成:man-bowing:'],
#     'color': ['Slack 投稿色', COLOR_CREATE],
#     'username': ['申請者社員番号', user.username],
#     'screenname': ['申請者氏名', user.screenname],
#     'Position': ['申請者役職', user.Position],
#     'email': ['メールアドレス', user.email],
#     'Department': ['AD 所属部署情報', user.Department],
#     'group': ['グループ名', request.POST['name']],
#     'url': ['PiVToT URL', "{0}://{1}{2}".format(request.scheme, request.get_host(), request.path)]
# }
#
# tile = '<!here>' + array['title'][1]
# # ポスト処理
# WEB_HOOK_URL = ''
# requests.post(WEB_HOOK_URL, data=json.dumps({
#     'text': tile,
#     'attachments': [{
#         'link_names': 1,  # 名前をリンク化
#         'color': array['color'][1],  # color設定
#         'fields': [
#             {'title': array['username'][0],
#              'value': array['username'][1], 'short': 'true', },
#             {'title': array['screenname'][0],
#              'value': array['screenname'][1], 'short': 'true', },
#             {'title': array['Position'][0],
#              'value': array['Position'][1], 'short': 'true', },
#             {'title': array['group'][0],
#              'value': array['group'][1], 'short': 'true', },
#             {'title': array['email'][0],
#              'value': array['email'][1], },
#             {'title': array['Department'][0],
#              'value': array['Department'][1], },
#             {'title': array['url'][0],
#              'value': array['url'][1], 'short': 'true', },
#         ]
#     }]
# }))
