import pytest

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.utils.encoding import smart_text

from saleor.site import utils
from saleor.site.models import AuthorizationKey
from saleor.dashboard.sites.forms import SiteSettingForm


def test_get_site_settings_uncached(site_settings):
    result = utils.get_site_settings_uncached(site_settings.id)
    assert result == site_settings


def test_index_view(admin_client, site_settings):
    response = admin_client.get(reverse('dashboard:site-index'), follow=True)
    assert response.status_code == 200

    context = response.context
    assert context['site'] == site_settings


@pytest.mark.django_db
def test_form():
    data = {'name': 'mirumee', 'domain': 'mirumee.com'}
    form = SiteSettingForm(data)
    assert form.is_valid()

    site = form.save()
    assert smart_text(site) == 'mirumee'

    form = SiteSettingForm({})
    assert not form.is_valid()


def test_site_update_view(admin_client, site_settings):
    url = reverse('dashboard:site-update',
                  kwargs={'site_id': site_settings.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    data = {'name': 'Mirumee Labs', 'header_text': 'We have all the things!',
            'domain': 'mirumee.com', 'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0}
    response = admin_client.post(url, data)
    assert response.status_code == 302

    site_settings.refresh_from_db()
    assert site_settings.name == 'Mirumee Labs'


@pytest.mark.django_db
def test_get_authorization_key_for_backend(site_settings, authorization_key):
    key_for_backend = utils.get_authorization_key_for_backend('Backend')
    assert key_for_backend == authorization_key


@pytest.mark.django_db
def test_get_authorization_key_for_backend(site_settings):
    assert utils.get_authorization_key_for_backend('Backend') is None


@pytest.mark.django_db
def test_get_authorization_key_no_settings_site(settings, authorization_key):
    settings.SITE_SETTINGS_ID = None
    assert utils.get_authorization_key_for_backend('Backend') is None


@pytest.mark.django_db
def test_one_authorization_key_for_backend_and_settings(
        site_settings, authorization_key):
    with pytest.raises(IntegrityError):
        AuthorizationKey.objects.create(
            site_settings=site_settings, name='Backend')


@pytest.mark.django_db
def test_authorization_key_key_and_secret(authorization_key):
    assert authorization_key.key_and_secret() == ('Key', 'Password')


@pytest.mark.django_db
def test_settings_available_backends_empty(site_settings):
    assert site_settings.available_backends().count() == 0


@pytest.mark.django_db
def test_settings_available_backends(site_settings, authorization_key):
    backend_name = authorization_key.name
    available_backends = site_settings.available_backends()
    assert backend_name in available_backends
