from . import gunicorn.app.base


class GunicornApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(GunicornApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in list(self.options.items())
                       if key in self.cfg.settings and value is not None])
        for key, value in list(config.items()):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
