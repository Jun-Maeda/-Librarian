from django.db import models
from django.utils import timezone
import json, requests
import datetime
from user.models import User
from django.core.files import File
from imageio import imread
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

# 現在の時刻を取得
now_time = datetime.datetime.now()


# 出版情報
class Publisher(models.Model):
    name = models.CharField(
        verbose_name='出版社名',
        max_length=50,
    )

    def __str__(self):
        return self.name


# 著者情報
class Author(models.Model):
    name = models.CharField(
        verbose_name='著者名',
        max_length=50,
    )
    a_detail = models.TextField(
        verbose_name='著者紹介',
        max_length=100,
        null=True, blank=True,
    )

    def __str__(self):
        return self.name


class Book(models.Model):
    isbn = models.CharField(
        verbose_name='ISBN',
        max_length=50,
    )
    rent = models.BooleanField(
        verbose_name='帯出区分',
        default=False,
    )
    title = models.CharField(
        verbose_name='書籍名',
        max_length=50,
        null=True, blank=True,
    )
    title2 = models.CharField(
        verbose_name='ショセキメイ',
        max_length=50,
        null=True, blank=True,
    )
    name = models.ForeignKey(
        Author, on_delete=models.CASCADE,
        verbose_name='著者名',
        null=True, blank=True,
    )

    book_img = models.CharField(
        verbose_name='画像リンク',
        max_length=100,
        null=True, blank=True,
    )
    publisher_name = models.ForeignKey(
        Publisher, on_delete=models.CASCADE,
        verbose_name='出版社',
        null=True, blank=True, )
    code = models.CharField(
        verbose_name='Cコード',
        max_length=100,
        null=True, blank=True,
    )
    time = models.CharField(
        verbose_name='出版日',
        max_length=10,
        null=True, blank=True,
    )
    page = models.IntegerField(
        verbose_name='ページ数',
        null=True, blank=True,
    )
    detail = models.TextField(
        verbose_name='内容',
        max_length=500,
        null=True, blank=True,
    )
    book_q = models.IntegerField(
        verbose_name='在庫数',
        blank=True,
        null=True,
        default=0,
    )
    save_image = models.ImageField(
        verbose_name='保存画像',
        upload_to='images',
        default='',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.isbn

    # # adminで画像表示させる
    # def admin_og_image(self):
    #     if self.save_image:
    #         return '<img src="{}" style="width:100px;height:auto;">'.format(self.save_image)
    #     else:
    #         return 'no image'
    #     admin_og_image.allow_tags = True

    def save(self, *args, **kwargs):
        # APIで本の情報を取得
        url = requests.get(f"https://api.openbd.jp/v1/get?isbn={self.isbn}&pretty")
        text = url.text
        data = json.loads(text)

        # 取得したjsonデータよりそれぞれの項目を取得する
        book = data[0]
        name_info = book['onix']['DescriptiveDetail']['TitleDetail']['TitleElement']['TitleText']
        book_name = name_info['content']
        book_name2 = name_info['collationkey']
        author = book['onix']['DescriptiveDetail']['Contributor'][0]['PersonName']['content']
        book_image = book['onix']['CollateralDetail']['SupportingResource'][0]['ResourceVersion'][0]['ResourceLink']
        publisher = book['summary']['publisher']

        c_code = book['onix']['DescriptiveDetail']['Subject'][0]['SubjectCode']
        syuppan_date = book['hanmoto']['dateshuppan']
        book_page = book['onix']['DescriptiveDetail']['Extent'][0]['ExtentValue']
        book_detail = book['onix']['CollateralDetail']['TextContent'][0]['Text']
        author_detail = book['onix']['DescriptiveDetail']['Contributor'][0]['BiographicalNote']

        # 出版社名が同じものがすでに保存されているか確認する
        p = Publisher.objects.filter(name=publisher)
        if p.count() < 1:
            Publisher(name=publisher).save()

        p = Publisher.objects.get(name=publisher)

        # 著者名が同じものがすでに保存されているか確認する
        a = Author.objects.filter(name=author)
        if a.count() < 1:
            Author(name=author, a_detail=author_detail).save()

        a = Author.objects.get(name=author)

        # p_name = [publisher.id for publisher in Publisher.objects.filter(name=publisher)][0]

        # 取得したデータをオーバーライド
        self.title = book_name
        self.title2 = book_name2
        self.name = a
        self.book_img = book_image
        self.publisher_name = p
        self.code = c_code
        self.time = syuppan_date
        self.page = book_page
        self.detail = book_detail

        # 画像をダウンロードして保存
        if self.book_img and not self.save_image:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(book_image).read())
            img_temp.flush()
            self.save_image.save(f"image_{self.pk}.jpg", File(img_temp))

        super(Book, self).save(*args, **kwargs)




# 本の履歴情報
class BookHistory(models.Model):
    change = models.IntegerField(
        verbose_name='在庫変動数',
        default=0,
    )
    date = models.DateTimeField(
        verbose_name='日付',
        default=timezone.now,
        null=True, blank=True,
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE,
        verbose_name='ISBN',
        null=True, blank=True,
    )
    user = models.CharField(
        verbose_name='作業した人',
        max_length=50,
    )
    sup_flag = models.BooleanField(
        verbose_name='入荷フラグ',
        default=False,
    )
    rental_flag = models.BooleanField(
        verbose_name='レンタルフラグ',
        default=False,
    )
    return_flag = models.BooleanField(
        verbose_name='返却フラグ',
        default=False,
    )

    def __str__(self):
        return self.user


# 仕入れ先
class Supplier(models.Model):
    name = models.CharField(
        verbose_name='仕入れ先名',
        max_length=50,
    )

    def __str__(self):
        return self.name


# 入荷情報
class Stock(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE,
        verbose_name='ISBN',
        null=True, blank=True,
    )
    buy_date = models.DateTimeField(
        verbose_name='入荷日',
        null=True, blank=True,
    )
    quantity = models.IntegerField(
        verbose_name='入荷数',
        default=0,
    )
    shop = models.ForeignKey(
        Supplier, on_delete=models.CASCADE,
        verbose_name='仕入れ先',
        null=True, blank=True,
    )
    name = models.CharField(
        verbose_name='担当者',
        max_length=50,
    )

    def save(self, *args, **kwargs):
        # 現在の在庫数に追加する
        b = Book.objects.get(isbn=self.book)
        b_q = b.book_q
        change = self.quantity
        now_q = b_q + change

        # 保存する
        b.book_q = now_q
        b.save()

        self.buy_date = now_time
        super(Stock, self).save(*args, **kwargs)

        # 履歴に追加
        BookHistory.objects.create(change=change, book=b, date=self.buy_date, user=self.name, sup_flag=True)

    def __int__(self):
        return self.quantity


# 貸し出し情報
class Rental(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE,
        verbose_name='ISBN',
        null=True, blank=True,
    )
    user = models.CharField(
        verbose_name='貸出者名',
        max_length=50,
    )
    start_datetime = models.DateTimeField(
        verbose_name='貸出日',
        null=True, blank=True,
    )
    end_datetime = models.DateTimeField(
        verbose_name='返却日',
        null=True, blank=True,
    )
    return_flag = models.BooleanField(
        verbose_name='返却フラグ',
        default=False,
    )
    late_flag = models.BooleanField(
        verbose_name='延滞フラグ',
        default=False,
    )

    def save(self, *args, **kwargs):
        # 貸し出し情報から返却情報を取得
        r = self.return_flag

        # もし返却フラグがついていたら
        if r:
            # 在庫数から貸し出し分を増やす
            b = Book.objects.get(isbn=self.book)
            b_q = b.book_q
            change = 1
            ch_couunt = b_q + change
            b.book_q = ch_couunt
            b.book_q = ch_couunt
            # 保存する
            b.save()

            self.return_flag = True
            self.end_datetime = now_time
            super(Rental, self).save(*args, **kwargs)

            # 履歴に追加
            BookHistory.objects.create(change=change, book=b, date=now_time, user=self.user, return_flag=True)


        else:
            # 在庫数から貸し出し分を減らす
            b = Book.objects.get(isbn=self.book)
            b_q = b.book_q
            change = -1
            ch_couunt = b_q + change
            b.book_q = ch_couunt

            # 保存する
            b.save()

            self.start_datetime = now_time
            super(Rental, self).save(*args, **kwargs)

            # 履歴に追加
            BookHistory.objects.create(change=change, book=b, date=self.start_datetime, user=self.user,
                                       rental_flag=True)

    def __str__(self):
        return self.user


class Reserve(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE,
        verbose_name='ISBN',
        null=True, blank=True,
    )
    user = models.CharField(
        verbose_name='予約者名',
        max_length=50,
    )
    start_datetime = models.DateTimeField(
        verbose_name='予約日',
        null=True, blank=True,
    )
    end_datetime = models.DateTimeField(
        verbose_name='予約完了日',
        null=True, blank=True,
    )
    reserve_flag = models.BooleanField(
        verbose_name='予約完了フラグ',
        default=False,
    )

    def save(self, *args, **kwargs):
        # 本の在庫数取得
        b = Book.objects.get(isbn=self.book)
        b_q = b.book_q
        # 現在時刻取得

        if self.reserve_flag:
            self.end_datetime = now_time
            Rental.objects.create(book=b, user=self.user, start_datetime=now_time)
        else:
            if b_q > 0:
                raise ValueError("在庫あるよー")
            self.start_datetime = now_time
        super(Reserve, self).save(*args, **kwargs)

    def __str__(self):
        return self.user


# お問合せ
class Inquiry(models.Model):
    # userモデルから情報を取得
    name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    # name = models.CharField(
    #     max_length=50,
    #     verbose_name="名前"
    # )
    matter = models.TextField(
        max_length=500,
        verbose_name='問い合わせ内容',
    )
    date = models.DateTimeField(
        verbose_name='問い合わせ時間',
        default=now_time,
        null=True, blank=True,
    )

    def save(self, *args, **kwargs):
        self.date = now_time
        super(Inquiry, self).save(*args, **kwargs)
