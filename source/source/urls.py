from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static  
from django.conf import settings
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView

urlpatterns = [
    path("", include("main.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path('manifest.json', TemplateView.as_view(template_name="manifest.json")),
    path('offline.html', TemplateView.as_view(template_name="offline.html", content_type='text/html')),
    path('serviceworker.js', TemplateView.as_view(template_name="serviceworker.js", content_type='text/javascript')),
]

handler404 = 'main.views.handle_404' 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += i18n_patterns(path("admin/", admin.site.urls))
