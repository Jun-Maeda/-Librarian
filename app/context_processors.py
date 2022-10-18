from app.models import Rental
import datetime

def common(request):
    # ログインユーザーのPKを取得
    l_u = request.user.pk
    # 今日の時間から7日前を取得
    re_time = datetime.date.today() - datetime.timedelta(days=7)

    # ログインユーザーが8日以上に借りていて返していないものを取得
    u_rental = Rental.objects.filter(user=l_u, return_flag=False, start_datetime__lte=re_time)
    context = {
        'rental_over': u_rental,
    }
    return context
