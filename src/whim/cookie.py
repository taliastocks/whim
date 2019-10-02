import uuid

import cachetools

from whim import settings


class Cookie(object):
    def __init__(self, settings: settings.SectionSettings):
        self._cookie_filename = settings.get_string('cookie_file')
        self._value = self._get_value_from_disk()

    _is_expired_cache = cachetools.TTLCache(maxsize=100, ttl=1)
    @cachetools.cached(_is_expired_cache)
    def is_expired(self) -> bool:
        return self._value != self._get_value_from_disk()

    def get_value(self) -> bool:
        return self._value

    def reset(self) -> str:
        new_id = str(uuid.uuid4())
        with open(self._cookie_filename, 'w') as f:
            f.write(new_id)

        self._value = new_id
        self._is_expired_cache.clear()
        return new_id

    def _get_value_from_disk(self) -> str:
        try:
            with open(self._cookie_filename) as f:
                return f.read().strip()
        except IOError:
            return self.reset()
