from django.conf.urls import url

from keybase_proofs.views import KeybaseProofListView
from keybase_proofs.views import KeybaseProofProfileView
from keybase_proofs.views import KeybaseProofView

app_name = 'keybase_proofs'
urlpatterns = [
    url(r'^api/(?P<username>.+)?', KeybaseProofListView.as_view(), name='list-proofs-api'),
    url(r'^profile/(?P<username>.+)?', KeybaseProofProfileView.as_view(), name='profile'),
    url(r'^new-proof?', KeybaseProofView.as_view(), name='new-proof'),
]
