import logging
import os
from abc import ABCMeta, abstractmethod

from pyramid.config import Configurator
from pyramid_mailer import mailer_factory_from_settings
from pyramid_mailer.mailer import DebugMailer
from pyramid_mailer.message import Message
from tet.services import RequestScopedBaseService

_log = logging.getLogger(__name__)


class IMailerService(metaclass=ABCMeta):
    @abstractmethod
    def send_immediately(self, message):
        pass

    @abstractmethod
    def send(self, message):
        pass


class DebugCoalescingMailer(object):
    def __init__(self, mailer, mailer_debug_path, **bind_kw):
        self._mailer_debug_path = os.path.abspath(mailer_debug_path)

        args_without_tm = dict(bind_kw)
        self._tm = args_without_tm.pop('transaction_manager', None)
        self._main_mailer = mailer.bind(**args_without_tm)
        self._debug_mailer = DebugMailer(mailer_debug_path).bind(**bind_kw)

    def bind(self, **kw):
        return self.__class__(
            mailer=self._main_mailer,
            mailer_debug_path=self._mailer_debug_path,
            **kw
        )

    def send_immediately(self, message: Message) -> None:
        try:
            self._main_mailer.send_immediately(message)
        except Exception as e:
            _log.exception(e)

        self._debug_mailer.send_immediately(message)

    def send(self, message: Message) -> None:
        try:
            self._main_mailer.send_immediately(message)
        except Exception as e:
            _log.exception(e)

        self._debug_mailer.send(message)


class MailerService(RequestScopedBaseService, IMailerService):
    def __init__(self, **kw):
        super().__init__(**kw)
        mailer = self.request.registry['tet.mailer.factory']
        self._mailer = mailer.bind(transaction_manager=self.request.tm)

    def send(self, message: Message):
        return self._mailer.send(message)

    def send_immediately(self, message: Message):
        return self._mailer.send_immediately(message)


def includeme(config: Configurator) -> None:
    config.include('tet.services')
    settings = config.registry.settings
    prefix = settings.get('tet.mailer.prefix', 'tet.mailer.')
    mailer = mailer_factory_from_settings(settings, prefix=prefix)

    debug_path = settings.get(prefix + 'debug_directory')
    if debug_path:
        mailer = DebugCoalescingMailer(mailer, debug_path)

    config.registry['tet.mailer.factory'] = mailer
    config.register_tet_service(MailerService,
                                scope='request',
                                interface=IMailerService)
