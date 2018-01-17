import django.conf


def pytest_configure():
	django.conf.settings.configure()
