from pyramid.config import Configurator
from pyramid_mailer import mailer_factory_from_settings
from pyramid_mailer.message import Message
from tet.services import RequestScopedBaseService


class MailerService(RequestScopedBaseService):
    def __init__(self, **kw):
        super().__init__(**kw)
        mailer = self.request.registry['tet.mailer.factory']
        self._mailer = mailer.bind(self.request.tm)

    def send(self, message: Message):
        return self._mailer.send(message)

    def send_immediately(self, message: Message):
        return self._mailer.send_immediately(message)


def includeme(config: Configurator) -> None:
    settings = config.registry.settings
    prefix = settings.get('tet.mailer.prefix', 'tet.mailer.')
    mailer = mailer_factory_from_settings(settings, prefix=prefix)
    config.registry['tet.mailer.factory'] = mailer
