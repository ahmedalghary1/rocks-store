from whitenoise.storage import CompressedManifestStaticFilesStorage


class ResilientCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Keep dynamic pages available while a static deployment is catching up."""

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            # A stale or incomplete manifest should degrade to an unhashed URL
            # instead of raising during template/context rendering.
            return self.clean_name(name)
