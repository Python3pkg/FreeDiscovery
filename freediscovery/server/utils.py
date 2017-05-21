# -*- coding: utf-8 -*-






def _is_inside_docker():
    """ An imperfect way of checking that the server is
    running inside a Docker container"""

    return os.path.exists('/freediscovery_shared/')

