# ROCKS ELECTRIC

متجر عربي RTL مبني بـ Django وHTML/CSS وJavaScript بدون أطر واجهات.

## التشغيل المحلي

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_store
python manage.py createsuperuser
python manage.py runserver
```

ثم افتح `http://127.0.0.1:8000/`. لوحة الإدارة في `/admin/`.

## الاختبار

```powershell
python manage.py test
python manage.py check --deploy
```

للنشر، انسخ `.env.example` إلى `.env` واضبط مفتاحًا سريًا حقيقيًا، `DEBUG=False`، النطاقات المسموح بها وقاعدة PostgreSQL. شغّل `collectstatic` وقدّم التطبيق عبر Gunicorn خلف Nginx أو منصة Django مُدارة.
