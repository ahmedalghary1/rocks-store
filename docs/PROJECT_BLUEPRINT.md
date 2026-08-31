# ROCKS ELECTRIC — مخطط المشروع

## المعمارية

- `core`: الصفحة الرئيسية، الصفحات التعريفية، التواصل، إعدادات الموقع والمفضلة.
- `catalog`: التصنيفات والمنتجات والصور والمواصفات والمتغيرات والبحث.
- `cart`: سلة Session وخدمة التسعير المركزية.
- `orders`: الدفع، الطلبات، لقطات عناصر الطلب والكوبونات.
- `accounts`: لوحة العميل والعناوين، مع نظام مصادقة Django.
- `marketing`: البنرات والمحتوى التسويقي القابل للإدارة.

## قاعدة البيانات

`Category → Product → ProductImage / ProductSpecification / ProductVariant`، و`Order → OrderItem` مع الاحتفاظ باسم المنتج والكود والسعر لحظة الشراء. ترتبط الطلبات بالمستخدم اختياريًا حتى يدعم المتجر شراء الضيف.

## خريطة الموقع

- `/` الرئيسية
- `/products/` المنتجات والبحث والفلاتر
- `/products/<slug>/` تفاصيل المنتج
- `/wishlist/` المفضلة
- `/cart/` السلة
- `/checkout/` إتمام الطلب
- `/account/` لوحة العميل
- `/about/` من نحن
- `/contact/` التواصل
- `/admin/` الإدارة

## مكوّنات الواجهة

Header زجاجي، Mega Menu، Search Overlay، Hero، Category Card، Product Card، Quick View، Toast، Product Gallery، Tabs، Filter Drawer، Cart Line، Order Summary، Checkout Form، Empty State، Newsletter، Footer، Mobile Bottom Navigation.

## Wireframe الرئيسية

Header → Hero (نص يمين/منتج يسار) → Quick Categories → Featured Products → LED Promo → Best Sellers → Why ROCKS → New Arrivals → Brand Story → Trust Strip → Newsletter → Footer.

## نظام التصميم

الأخضر الداكن هو السطح الأساسي، الأبيض للمحتوى، والذهبي/الأخضر الكهربائي accents. العناوين Alexandria والنصوص Cairo، مع قياسات fluid، ومسافات 4–120px، وأنصاف أقطار 8–32px. الحركة تستخدم `cubic-bezier(.22,1,.36,1)` وتقتصر أساسًا على opacity وtransform.
