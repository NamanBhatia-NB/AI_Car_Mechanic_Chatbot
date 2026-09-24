from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Instant Mechanic API'

    def ready(self):
        # Python 3.14 compatibility patch for django.template.context.BaseContext.__copy__
        try:
            from django.template import context
            def _fixed_copy(self):
                duplicate = self.__class__.__new__(self.__class__)
                duplicate.__dict__.update(self.__dict__)
                duplicate.dicts = self.dicts[:]
                return duplicate
            context.BaseContext.__copy__ = _fixed_copy
        except Exception:
            pass
