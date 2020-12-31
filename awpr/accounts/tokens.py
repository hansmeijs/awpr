from django.contrib.auth.tokens import PasswordResetTokenGenerator
# PR2020-12-10 removed: from django.utils import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        """
        PR2020-12-10 debug: in Django 3 'six' is removed from django.utils
        can use function str() instead of six.text_type()
        from https://github.com/jazzband/django-pipeline/issues/707
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.activated)
        )
        """
        return (
            str(user.pk) + str(timestamp) + str(user.activated)
        )


account_activation_token = AccountActivationTokenGenerator()