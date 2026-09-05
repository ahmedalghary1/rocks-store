# ROCKS ELECTRIC

## PythonAnywhere uploaded images

Uploaded product, category and banner images are stored in `MEDIA_ROOT`. New uploads keep their original pixel dimensions, are stripped of metadata, compressed as WebP, and saved without retaining the original file. Replaced and deleted database images are also removed from storage.

For the `rocksev` PythonAnywhere account, set this in `.env`:

```dotenv
MEDIA_ROOT=/home/rocksev/rocks-store/media
IMAGE_WEBP_QUALITY=82
```

Then create the directory and convert any existing JPG/PNG uploads:

```bash
cd /home/rocksev/rocks-store
source /home/rocksev/venv/bin/activate
mkdir -p /home/rocksev/rocks-store/media
pip install -r requirements.txt
python manage.py optimize_media_images
```

In the PythonAnywhere **Web** tab, add this exact Static files mapping and reload the web app:

| URL | Directory |
| --- | --- |
| `/media/` | `/home/rocksev/rocks-store/media` |

Do not point `/media/` at `staticfiles`; user uploads and collected static assets are separate directories.

متجر عربي RTL مبني بـDjango ويستخدم SQLite مع حماية ذرّية للمخزون والكوبونات ومنع تكرار الطلب.

## التشغيل المحلي

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

غيّر `.env` إلى `DEBUG=True` وعيّن مفتاحًا محليًا، ثم:

```powershell
python manage.py migrate
python manage.py seed_store
python manage.py createsuperuser
python manage.py runserver
```

## قائمة نشر الإنتاج

1. أنشئ `.env` خارج Git بقيم حقيقية لـ`SECRET_KEY` و`ALLOWED_HOSTS` و`CSRF_TRUSTED_ORIGINS` والبريد ومجلدي cache والنسخ الاحتياطي.
2. ضع `SQLITE_PATH` على قرص دائم، ولا تضع قاعدة البيانات داخل مجلد مؤقت.
3. استخدم عملية تطبيق واحدة عند تشغيل Gunicorn مع SQLite:

   ```bash
   gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 60
   ```

4. نفّذ قبل تحويل الزيارات إلى الإصدار الجديد، وبالترتيب التالي:

   ```bash
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput --clear
   python manage.py check --deploy
   python manage.py test
   python manage.py check_production_readiness
   ```

5. في PythonAnywhere اربط `/media/` بمجلد `MEDIA_ROOT` الدائم. اترك `/static/` يمر عبر WhiteNoise للاستفادة من الضغط والتخزين المؤقت، أو اضبط Cache-Control لمدة طويلة إذا استخدمت static mapping مباشرًا.
6. اضبط بريد الطلبات في `ORDER_NOTIFICATION_EMAIL` وبيانات SMTP. بدونها تُحفظ الطلبات لكن لن تصل إشعارات بريدية.
7. أدخل الهاتف وواتساب والبريد والعنوان وروابط السوشيال من لوحة الإدارة، واضبط تكلفة الشحن وحد الشحن المجاني لكل محافظة من `Shipping zones`. الدفع عند الاستلام هو الطريقة الوحيدة المدعومة.
8. راجع نصوص الخصوصية والشروط والشحن والاسترجاع مع مستشار قانوني حسب السوق الفعلي.
9. اختبر نسخ قاعدة البيانات واستعادتها دوريًا، وانسخ مجلد media بصورة مستقلة. أمر النسخ يتحقق من سلامة ملف SQLite الناتج تلقائيًا.

### إعداد PythonAnywhere

ملف WSGI يقرأ إعدادات الإنتاج من `/home/rocksev/rocks-store/.env`. متغيرات
`export` التي تُكتب داخل Bash console لا تنتقل تلقائيًا إلى Web worker. أنشئ
مفتاحًا آمنًا مرة واحدة:

```bash
cd /home/rocksev/rocks-store
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

ثم أنشئ ملف `.env` بصلاحيات خاصة وضع فيه الناتج بدل القيمة التوضيحية:

```dotenv
SECRET_KEY=ضع-هنا-المفتاح-الذي-تم-توليده
DEBUG=False
ALLOWED_HOSTS=rocksev.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://rocksev.pythonanywhere.com
SQLITE_PATH=/home/rocksev/rocks-store/db.sqlite3
CACHE_LOCATION=/home/rocksev/rocks-store/.cache
BACKUP_DIRECTORY=/home/rocksev/backups
LEGAL_CONTENT_APPROVED=False
```

نفّذ `chmod 600 .env`، ثم من تبويب Web أعد تحميل التطبيق. لا تضف `.env` إلى Git
ولا تغيّر المفتاح بعد بدء استخدام الموقع، لأن تغييره يبطل الجلسات الحالية.

إذا ظهر خطأ `Missing staticfiles manifest entry` بعد رفع نسخة جديدة، فتأكد أن
الملف موجود في المصدر ثم أعد بناء الـmanifest بعد `git pull` وليس قبله:

```bash
cd /home/rocksev/rocks-store
source /home/rocksev/venv/bin/activate
python manage.py findstatic images/rocks-logo-official.png
python manage.py collectstatic --noinput --clear
```

يجب أن يعرض `findstatic` مسار الملف داخل مجلد `static`. بعد نجاح الأمرين أعد
تحميل التطبيق من تبويب Web.

## نسخ SQLite احتياطيًا

الأمر يستخدم SQLite Online Backup API ويصلح أثناء عمل الموقع:

```bash
python manage.py backup_database --directory /absolute/persistent/backups
```

جدوله يوميًا، واحتفظ بنسخة خارج الخادم. اختبر الاستعادة على بيئة منفصلة كل شهر.

## إشعارات الطلبات

كل طلب يحتفظ بحالة إرسال البريد وعدد المحاولات داخل SQLite. شغّل الأمر التالي كل خمس دقائق من scheduled task لإعادة المحاولة عند تعطل SMTP:

```bash
python manage.py retry_order_notifications --max-attempts 10
```

راجع حالات الإرسال والأخطاء من `Order notifications` داخل لوحة الإدارة.

## التحقق والمراقبة

- فحص الخدمة: `/health/`
- لوحة الإدارة: `/admin/`
- sitemap: `/sitemap.xml`
- robots: `/robots.txt`

GitHub Actions يشغّل migrations والفحوصات الأمنية للـ dependencies و`check --deploy` والاختبارات و`collectstatic` آليًا. السجلات تخرج إلى stdout لتلتقطها منصة الاستضافة.

## ملاحظات SQLite

SQLite مناسب لحجم صغير إلى متوسط مع كتابة محدودة. تحديثات المخزون والكوبون في هذا المشروع ذرّية، ومدة انتظار القفل 30 ثانية. أبقِ المعاملات قصيرة وعملية التطبيق واحدة، وراقب أخطاء `database is locked`. إذا زاد ضغط الكتابة بوضوح ستكون ترقية قاعدة البيانات قرارًا تشغيليًا لاحقًا، وليست مطلوبة لتشغيل النسخة الحالية.
